![Gherking tests](https://github.com/dataiku/dss-visual-edit/actions/workflows/gherkin-tests.yml/badge.svg)

## Contents of this repository

* `dash_tabulator/`: source code for the Dash component powering Visual Edit's "data table", based on the Tabulator Javascript library. Read more in the [dash_tabulator README](dash_tabulator/README.md).
* `dss-plugin-visual-edit/`: actual plugin code; when installing the plugin in Dataiku, we would provide this directory only. Read more in the [dss-plugin-visual-edit README](dss-plugin-visual-edit/README.md).
* `docs/`: source code in Markdown for the documentation website.

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
  * For Developers:
    * [Introduction to Visual Edit's CRUD Python API](docs/CRUD_example_usage.ipynb)
    * [Low-code webapp customizations with Dash](https://dataiku.github.io/dss-visual-edit/dash-examples)
    * [Reference API documentation](https://dataiku.github.io/dss-visual-edit/backend/#DataEditor)
  * [FAQ](faq)
* For Business Users:
  * [How to use the data table](https://dataiku.github.io/dss-visual-edit/data-table-features)
