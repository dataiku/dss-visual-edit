![Gherking tests](https://github.com/dataiku/dss-visual-edit/actions/workflows/gherkin-tests.yml/badge.svg)

## Contents of this repository

* `dash_tabulator/`: source code for the Dash component powering Visual Edit's "data table", based on the Tabulator Javascript library. Read more in the [dash_tabulator README](dash_tabulator/README.md).
* `dss-plugin-visual-edit/`: actual plugin code; when installing the plugin in Dataiku, we would provide this directory only. Read more in the [dss-plugin-visual-edit README](dss-plugin-visual-edit/README.md).
* `docs/`: source code in Markdown for the documentation website.

## Plugin documentation

The documentation website for Visual Edit is at [https://dataiku.github.io/dss-visual-edit/](https://dataiku.github.io/dss-visual-edit/).

Quick Links:

* For Data Experts:
  * [Compatibility](https://dataiku.github.io/dss-visual-edit/compatibility)
  * User guides:
    * [Getting started](https://www.dataiku.com/product/plugins/visual-edit/)
    * [Validating machine-generated data](https://dataiku.github.io/dss-visual-edit/validate)
    * [Building a complete application to test with end-users](https://dataiku.github.io/dss-visual-edit/build-complete-application)
    * [Deploying to production](https://dataiku.github.io/dss-visual-edit/deploy)
  * Case study: Entity Resolution (coming soon)
  * Advanced features:
    * [Linked Records](https://dataiku.github.io/dss-visual-edit/linked-records)
    * [Editschema](https://dataiku.github.io/dss-visual-edit/editschema)
  * [FAQ](https://dataiku.github.io/dss-visual-edit/faq)
  * [Troubleshooting](https://dataiku.github.io/dss-visual-edit/troubleshooting)
* For Developers:
  * [Introduction to Visual Edit's CRUD API](https://github.com/dataiku/dss-visual-edit/blob/master/docs/CRUD_example_usage.ipynb) (Python notebook)
  * [Low-code webapp customizations with Dash](https://dataiku.github.io/dss-visual-edit/dash-examples)
  * [Reference API documentation](https://dataiku.github.io/dss-visual-edit/backend/#DataEditor)
  * Full-code webapp customizations: see [dash_tabulator documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dash_tabulator/README.md) and [Plugin Developer Documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dss-plugin-visual-edit/README.md)
* For Business Users:
  * [How to use the data table](https://dataiku.github.io/dss-visual-edit/data-table-features)
