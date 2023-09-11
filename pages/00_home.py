import solara


@solara.component
def Page():
    with solara.Column(align="center"):
        markdown = """
        ## A Solara Web App for Visualizing [Maxar Open Data](https://www.maxar.com/open-data)
        
        ### Introduction

        **A collection of [Solara](https://github.com/widgetti/solara) web apps for geospatial applications.**

        - Web App: <https://giswqs-solara-maxar.hf.space>
        - GitHub: <https://github.com/opengeos/solara-maxar>
        - Hugging Face: <https://huggingface.co/spaces/giswqs/solara-maxar>

        """

        solara.Markdown(markdown)
