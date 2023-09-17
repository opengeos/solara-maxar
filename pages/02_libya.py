import os
import leafmap
import solara
import ipywidgets as widgets
import pandas as pd
import geopandas as gpd
import tempfile
from shapely.geometry import Point

event = 'Libya-Floods-Sept-2023'
url = 'https://raw.githubusercontent.com/opengeos/maxar-open-data/master'
repo = 'https://github.com/opengeos/maxar-open-data/blob/master/datasets'


def get_datasets():
    datasets = f'{url}/datasets.csv'
    df = pd.read_csv(datasets)
    return df


def get_catalogs(name):
    dataset = f'{url}/datasets/{name}.tsv'
    basename = os.path.basename(dataset)
    tempdir = tempfile.gettempdir()
    tmp_dataset = os.path.join(tempdir, basename)
    if os.path.exists(tmp_dataset):
        dataset_df = pd.read_csv(tmp_dataset, sep='\t')
    else:
        dataset_df = pd.read_csv(dataset, sep='\t')
        dataset_df.to_csv(tmp_dataset, sep='\t', index=False)
    catalog_ids = dataset_df['catalog_id'].unique().tolist()
    catalog_ids.sort()
    return catalog_ids


def add_widgets(m):
    datasets = get_datasets()['dataset'].tolist()
    setattr(m, 'zoom_to_layer', True)
    style = {"description_width": "initial"}
    padding = "0px 0px 0px 5px"
    dataset = widgets.Dropdown(
        options=datasets,
        description='Event:',
        value=event,
        style=style,
        layout=widgets.Layout(width="270px", padding=padding),
    )

    catalog_ids = get_catalogs(dataset.value)
    setattr(m, 'catalog_ids', catalog_ids)

    image = widgets.Dropdown(
        value=None,
        options=m.catalog_ids,
        description='Image:',
        style=style,
        layout=widgets.Layout(width="270px", padding=padding),
    )

    checkbox = widgets.Checkbox(
        value=True,
        description='Footprints',
        style=style,
        layout=widgets.Layout(width="90px", padding="0px"),
    )

    split = widgets.Checkbox(
        value=False,
        description='Split map',
        style=style,
        layout=widgets.Layout(width="92px", padding=padding),
    )

    reset = widgets.Checkbox(
        value=False,
        description='Reset',
        style=style,
        layout=widgets.Layout(width="75px", padding='0px'),
    )

    def reset_map(change):
        if change.new:
            image.value = None
            image.options = m.catalog_ids
            m.layers = m.layers[:3]
            m.zoom_to_layer = True
            reset.value = False

    reset.observe(reset_map, names='value')

    def change_dataset(change):
        default_geojson = f'{url}/datasets/{change.new}_union.geojson'
        m.layers = m.layers[:2]
        m.controls = m.controls[:-1]
        basename = os.path.basename(default_geojson)
        tempdir = tempfile.gettempdir()
        tmp_geojson = os.path.join(tempdir, basename)
        if os.path.exists(tmp_geojson):
            default_geojson = tmp_geojson
        else:
            leafmap.download_file(default_geojson, tmp_geojson, quiet=True)
        m.add_geojson(default_geojson, layer_name='Footprint', zoom_to_layer=True)
        setattr(m, 'gdf', gpd.read_file(default_geojson))

        image.options = get_catalogs(change.new)

    dataset.observe(change_dataset, names='value')

    def change_image(change):
        if change.new:
            mosaic = f'{url}/datasets/{dataset.value}/{image.value}.json'
            m.add_stac_layer(mosaic, name=image.value, fit_bounds=m.zoom_to_layer)

    image.observe(change_image, names='value')

    def change_footprint(change):
        geojson_layer = m.find_layer('Footprint')
        if change.new:
            geojson_layer.visible = True
        else:
            geojson_layer.visible = False

    checkbox.observe(change_footprint, names='value')

    def change_split(change):
        if change.new:
            if image.value is not None:
                left_layer = m.find_layer(image.value)
                right_layer = m.find_layer('Google Satellite')
                right_layer.visible = True
                footprint_layer = m.find_layer('Footprint')
                footprint_layer.visible = False
                checkbox.value = False
                m.split_map(
                    left_layer=left_layer,
                    right_layer=right_layer,
                    add_close_button=True,
                    left_label=image.value,
                    right_label='Google Satellite',
                )
                split.value = False
            else:
                left_layer = None

    split.observe(change_split, names='value')

    def handle_click(**kwargs):
        if kwargs.get('type') == 'click':
            latlon = kwargs.get('coordinates')
            geometry = Point(latlon[::-1])
            selected = m.gdf[m.gdf.intersects(geometry)]
            setattr(m, 'zoom_to_layer', False)
            if len(selected) > 0:
                catalog_ids = selected['catalog_id'].values.tolist()

                if len(catalog_ids) > 1:
                    image.options = catalog_ids
                image.value = catalog_ids[0]
            else:
                image.value = None

    m.on_interaction(handle_click)

    box = widgets.VBox([dataset, image, widgets.HBox([checkbox, split, reset])])
    m.add_widget(box, position='topright', add_header=False)


zoom = solara.reactive(2)
center = solara.reactive((20, 0))


class Map(leafmap.Map):
    def __init__(self, **kwargs):
        kwargs['toolbar_control'] = False
        super().__init__(**kwargs)
        basemap = {
            "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            "attribution": "Google",
            "name": "Google Satellite",
        }
        self.add_tile_layer(**basemap, shown=False)
        self.add_layer_manager(opened=False)
        add_widgets(self)
        default_geojson = f'{url}/datasets/{event}_union.geojson'
        basename = os.path.basename(default_geojson)
        tempdir = tempfile.gettempdir()
        tmp_geojson = os.path.join(tempdir, basename)
        if os.path.exists(tmp_geojson):
            default_geojson = tmp_geojson
        else:
            leafmap.download_file(default_geojson, tmp_geojson, quiet=True)
        self.add_geojson(default_geojson, layer_name='Footprint', zoom_to_layer=True)
        setattr(self, 'gdf', gpd.read_file(default_geojson))


@solara.component
def Page():
    with solara.Column(style={"min-width": "500px"}):
        # solara components support reactive variables
        # solara.SliderInt(label="Zoom level", value=zoom, min=1, max=20)
        # using 3rd party widget library require wiring up the events manually
        # using zoom.value and zoom.set
        Map.element(  # type: ignore
            zoom=zoom.value,
            on_zoom=zoom.set,
            center=center.value,
            on_center=center.set,
            scroll_wheel_zoom=True,
            toolbar_ctrl=False,
            data_ctrl=False,
            height="780px",
        )
        solara.Text(f"Center: {center.value}")
        solara.Text(f"Zoom: {zoom.value}")
