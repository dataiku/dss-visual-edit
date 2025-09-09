# DSS Plugin: Visual Edit

Visual Edit provides components to create data validation and editing interfaces, packaged in a Dataiku plugin.

This document serves as developer documentation. As a preliminary step, we recommend reading all pages of the [user documentation](https://dataiku.github.io/dss-visual-edit/) for data experts and for developers (including the FAQ and Troubleshooting pages which provide insights into the functioning of the plugin).

## Contents

The code was developed in Python (environment specs are in `code-env/`) and is organized as follows:

* **Data persistence layer** based on the [Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing): we don't store the edited data directly, but instead, we use an append-only store to record the full series of actions on that data (the "editlog"); we then use it to recreate the edited state.
* **Integration of edits within a Dataiku Flow**: this is where Recipes and other Dataiku-specific components are specified and implemented, based on the above.
* **Dash Webapp**: provides an interface for end-users to edit data; the front-end is powered by the [`dash_tabulator`](../dash_tabulator/README.md) component and the backend is powered by the data persistence layer. The webapp is also packaged as a Dataiku Visual Webapp.

### Data persistence layer

* **`python-lib/DataEditor.py`**
  * Provides a CRUD Python API with methods to edit and validate data from a Dataiku dataset.
  * Maintains a timestamped log of edits and of the usernames behind them, so that the history of edits can be viewed.
* The [API reference documentation](https://dataiku.github.io/dss-visual-edit/backend/) was generated from docstrings by Mkdocs (following [this tutorial](https://realpython.com/python-project-documentation-with-mkdocs/)). Updates to the documentation website are manual, they require running `mkdocs build` from `python-lib/` and moving the output (in `site/`) to `../docs/backend/`.
* **`python-lib/commons.py`** provides the core logic to replay and apply edits, based on a pivot of the editlog and a join with the original data. This can be run in real-time mode within a webapp, or in batch mode within a data pipeline.

### Integration of edits within a Dataiku Flow

We recommend reading the components' descriptions, available on your Dataiku instance once you've installed the plugin.

* **`custom-recipes/` (Dataiku plugin components: Recipes)** leverage the data persistence layer and Custom Fields (see below) to replay edits found in an editlog dataset, and integrate them into a Dataiku Flow.
* **`custom-fields/visual-edit-schema/` (Dataiku plugin component: Custom Fields)** provides a place to store dataset settings such as primary keys and editable columns, which are used by the Recipes. Currently, these settings are duplicated across the original dataset and the editlog:
  * original dataset:
    * `primary_keys` is used by the Apply Edits function/recipe, which joins the original and edits datasets
    * `editable_columns` is used to present columns in a certain order
    * Note: both properties are returned by the `get_original_df()` method in `commons.py`.
  * editlog dataset:
    * `primary_keys` is used by the Replay Edits function/recipe to unpack key values into 1 column per primary key and to figure out key names.
* **`python-steps/visual-edit-empty-editlog/` (Dataiku plugin component: Scenario step)** empties the editlog by deleting all rows (this is only used for testing purposes on a design instance).

### Dash Webapp

Structure of `webapps/visual-edit/backend.py`:

* Dataiku-specific logic
* Instantiate `DataEditor`
* Add a `dash_tabulator` component to the layout, for the data table, with data coming from `DataEditor`
* Add a callback triggered upon edits, using `DataEditor` to log edits.

See below for how to run the webapp locally and have access to Dash dev tools in the browser, including the callback graph: it provides a visual overview of the components and callbacks, which helps understand the logic behind the automatic detection of changes in the original dataset.

### Data table

## Modifying the plugin

See [DEVELOPMENT.md](DEVELOPMENT.md).
