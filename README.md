# README

## Plugin documentation

The documentation website for Visual Edit is at [https://dataiku.github.io/dss-visual-edit/](https://dataiku.github.io/dss-visual-edit/).

Quick Links:
* For Data Experts:
  * [Installation](https://dataiku.github.io/dss-visual-edit/install-plugin)
  * User guides:
    * [Use Case #1: Correcting Source Data](https://dataiku.github.io/dss-visual-edit/get-started)
    * [Use Case #2: Reviewing Machine-Generated Data](https://dataiku.github.io/dss-visual-edit/reviewing)
    * [Deploying in Production](https://dataiku.github.io/dss-visual-edit/deploy)
  * Advanced features:
    * [Linked Records](https://dataiku.github.io/dss-visual-edit/linked-records)
    * [Editschema](https://dataiku.github.io/dss-visual-edit/editschema)
    * [Python API](https://dataiku.github.io/dss-visual-edit/get-started-crud-python-api)
  * [FAQ](faq)
* For Business Users:
  * [How to use the data table](https://dataiku.github.io/dss-visual-edit/data-table-features)

## Contents of this repository

* `dash_tabulator`: source code for the Dash component powering the plugin's "data table", based on the [Tabulator](http://tabulator.info) Javascript library.
* `plugin-dss-visual-edit`: actual plugin code; when installing the plugin in Dataiku, we would provide this directory only.
* `docs/`: source code in Markdown for the documentation website
  * `backend/`: technical documentation generated from docstrings by Mkdocs (following [this tutorial](https://realpython.com/python-project-documentation-with-mkdocs/)). Updates are manual. They require running `mkdocs build` from `plugin-dss-visual-edit/python-lib/` and moving the output (in `site/`) to the repo's `docs/backend/`.

In addition to the documentation website, check out these directories' README files for additional explanations of how the plugin works.
