# DSS Plugin: Visual Edit

Visual Edit provides components to create data editing interfaces, packaged in a Dataiku plugin.

This document serves as developer documentation. As a preliminary step, we recommend reading the [user documentation](https://dataiku.github.io/dss-visual-edit/).

## Contents

The code was developed in Python (environment specs are in `code-env/`). Its functioning is based on the Event Sourcing pattern, where we don't store the edited data directly, but the events to recreate it. The contents of the plugin are organized as follows:

* **Data persistence layer**: provides a Python library with a CRUD API and methods to log and replay edits; these can be run in real-time mode within a webapp, or in batch mode within a data pipeline.
* **Integration of edits within a Dataiku Flow**: this is where Dataiku-specific components are specified and implemented, based on the above.
* **Dash Webapp**: provides an interface for end-users to edit data, powered by the [`dash_tabulator`](../dash_tabulator/README.md) component. The webapp is also packaged as a Dataiku Visual Webapp.

### Data persistence layer

* The CRUD Python API is implemented in `python-lib/DataEditor.py`. Its [documentation](https://dataiku.github.io/dss-visual-edit/backend/) was generated from docstrings by Mkdocs (following [this tutorial](https://realpython.com/python-project-documentation-with-mkdocs/)). Updates to the documentation website are manual, they require running `mkdocs build` from `python-lib/` and moving the output (in `site/`) to `../docs/backend/`.
* The core replay logic is in `python-lib/commons.py`.

### Integration of edits within a Dataiku Flow

We recommend reading the components' descriptions, available on your Dataiku instance once you've installed the plugin.

* **`custom-recipes/` (Dataiku plugin components: Recipes)** leverage the data persistence layer and Custom Fields (see below) to replay edits found in an editlog dataset, and integrate them into a Dataiku Flow.
* **`custom-fields/edit-schema/` (Dataiku plugin component: Custom Fields)** provides a place to store dataset settings such as primary keys and editable columns, which are used by webapps and recipes. Currently, these are duplicated across the original dataset and the editlog:
  * original dataset:
    * `primary_keys` is used by the Apply Edits function/recipe, which joins the original dataset with the one of edited rows
    * `editable_columns` is used to present columns in a certain order
    * Note: both properties are returned by the `get_original_df()` method in `commons.py`.
  * editlog dataset: 
    * `primary_keys` is used to unpack key values into 1 column per primary key and to figure out key names.
* **`python-steps/empty-editlog/` (Dataiku plugin component: Scenario step)** empties the editlog by deleting all rows (this is only used for testing purposes on a design instance).

### Dash Webapp

Structure of `webapps/visual-edit/backend.py`:

* Dataiku-specific logic
* Instantiate `DataEditor`
* Add a `dash_tabulator` component to the layout, for the data table, with data coming from `DataEditor`
* Add a callback triggered upon edits, using `DataEditor` to log edits.

Overview of components and callbacks: ![callback graph](callback_graph.png).

## Modifying the plugin

Most changes to the code can be tested by running the webapp locally. You can then further test the integration with Dataiku by installing the plugin with your customizations. For this, you would change the repo URL used by the plugin installer to fetch from Git (see [installation instructions](https://dataiku.github.io/dss-visual-edit/install-plugin); DO NOT tick "development mode"). Alternatively, you can create a ZIP file from the `dss-plugin-visual-edit` directory and upload it to the plugin installer.

As a pre-requisite to running the webapp locally, you should configure your machine to [connect to your Dataiku instance](https://doc.dataiku.com/dss/latest/python-api/outside-usage.html#setting-up-the-connection-with-dss) (on a Mac, this is in `~/.dataiku/config.json`).

### Create a Python environment

* Create a Python 3.9 environment (to match `code-env/python/desc.json`) and activate it. On a Mac:

```bash
brew install python@3.9
/usr/local/bin/python3.9 -m venv venv
source venv/bin/activate
```

* Install Pandas 1.5 (to match `code-env/python/desc.json`) and the other requirements:

```bash
pip install --upgrade pip
pip install pandas==1.5.3
pip install -r code-env/python/spec/requirements.txt
```

* Install Dataiku internal client:

```bash
instance_name=$(jq -r '.default_instance' ~/.dataiku/config.json)
DKU_DSS_URL=$(jq -r --arg instance $instance_name '.dss_instances[$instance].url' ~/.dataiku/config.json)
pip install $DKU_DSS_URL/public/packages/dataiku-internal-client.tar.gz
```

* Install dev requirements:

```bash
pip install dataiku-api-client
pip install ipykernel
```

### Store webapp settings in a JSON file

When the webapp runs locally, we don't have a settings interface where we can specify the original dataset, primary keys, editable columns, linked records, etc. The workaround is to:

* Store the name of the dataset in an environment variable named `ORIGINAL_DATASET`;
* Have the webapp look for these settings in a JSON file with the same name, in `webapp-settings/` (you can find examples in that directory).

### Solution 1: run the webapp using VS Code Flask launch config (recommended)

* Copy `.vscode/launch.json.example` to `.vscode/launch.json`. Adapt these two definitions:
  * Project key (`DKU_CURRENT_PROJECT_KEY`)
  * Dataset name (`ORIGINAL_DATASET`)
* Go to "Run and Debug" in VS Code
* You can set breakpoints in the backend code, and you have access to Dash dev tools in the browser (callback graph, etc.)
* If you start an interactive Python session in VS Code, you'll be able to use "Jupyter: Variables" next to "Debug Console", and in particular the dataframe inspector.

### Solution 2: run the webapp using `python backend.py`

With `app.run_server(debug=True)` in `backend.py`.

You would also need to define some environment variables first:

```bash
export DKU_CURRENT_PROJECT_KEY=JOIN_COMPANIES_SIMPLE
export ORIGINAL_DATASET=matches_uncertain
export PYTHONPATH=../../python-lib
python backend.py
```
