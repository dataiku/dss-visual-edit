![Gherking tests](https://github.com/dataiku/dss-visual-edit/actions/workflows/gherkin-tests.yml/badge.svg)

This repository contains the following directories linked to the [Visual Edit plugin](https://www.dataiku.com/product/plugins/visual-edit/):

* **`dss-plugin-visual-edit/`**:
  * Contains the actual plugin: when installing in a Dataiku instance, we would provide this directory only. It provides the following components:
     * Python API to persist edits.
     * Recipes to integrate edits into a Dataiku Flow.
     * Dash data table component based on the Tabulator JavaScript library.
     * Visual Webapp for no-code setup.
  * Documentation:
     * Users: see [https://dataiku.github.io/dss-visual-edit/](https://dataiku.github.io/dss-visual-edit/).
     * Developers: see [dss-plugin-visual-edit README](dss-plugin-visual-edit/README.md).
* **`docs/`**: source code in Markdown for the user documentation website.
* **`dash_tabulator/`**: source code for the Dash data table component. Read more in the [dash_tabulator README](dash_tabulator/README.md).
