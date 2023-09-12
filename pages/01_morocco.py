import os
import leafmap
import solara
import ipyleaflet
import ipywidgets as widgets
import pandas as pd

url = 'https://open.gishub.org/maxar-open-data'
repo = 'https://github.com/opengeos/maxar-open-data/blob/master/datasets'


def get_datasets():
    datasets = f'{url}/datasets.csv'
    df = pd.read_csv(datasets)
    return df


def get_catalogs(name):
    dataset = f'{url}/datasets/{name}.tsv'

    dataset_df = pd.read_csv(dataset, sep='\t')
    catalog_ids = dataset_df['catalog_id'].unique().tolist()
    catalog_ids.sort()
    return catalog_ids


def add_widgets(m):
    datasets = get_datasets()['dataset'].tolist()

    style = {"description_width": "initial"}
    padding = "0px 0px 0px 5px"
    dataset = widgets.Dropdown(
        options=datasets,
        description='Event:',
        value="Morocco-Earthquake-Sept-2023",
        style=style,
        layout=widgets.Layout(width="270px", padding=padding),
    )

    image = widgets.Dropdown(
        value=None,
        options=get_catalogs(dataset.value),
        description='Image:',
        style=style,
        layout=widgets.Layout(width="270px", padding=padding),
    )

    checkbox = widgets.Checkbox(
        value=True,
        description='Show footprints',
        style=style,
        layout=widgets.Layout(width="130px", padding=padding),
    )

    split = widgets.Checkbox(
        value=False,
        description='Split map',
        style=style,
        layout=widgets.Layout(width="130px", padding=padding),
    )

    def change_dataset(change):
        default_geojson = f'{url}/datasets/{change.new}.geojson'
        m.layers = m.layers[:2]
        m.controls = m.controls[:-1]
        m.add_geojson(default_geojson, layer_name='Footprint', zoom_to_layer=True)
        image.options = get_catalogs(change.new)

    dataset.observe(change_dataset, names='value')

    def change_image(change):
        if change.new:
            mosaic = f'{url}/datasets/{dataset.value}/{image.value}.json'
            m.add_stac_layer(mosaic, name=image.value)

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
                m.split_map(
                    left_layer=left_layer,
                    right_layer=right_layer,
                    add_close_button=True,
                )
                split.value = False
            else:
                left_layer = None

    split.observe(change_split, names='value')

    event_control = ipyleaflet.WidgetControl(widget=dataset, position='topright')
    image_control = ipyleaflet.WidgetControl(widget=image, position='topright')
    checkboxes = widgets.HBox([checkbox, split])
    checkbox_control = ipyleaflet.WidgetControl(widget=checkboxes, position='topright')

    m.add(event_control)
    m.add(image_control)
    m.add(checkbox_control)


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
        default_geojson = f'{url}/datasets/Morocco-Earthquake-Sept-2023.geojson'
        self.add_geojson(default_geojson, layer_name='Footprint', zoom_to_layer=True)


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
