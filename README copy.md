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

## Modifying the plugin

Most changes to the code can be tested by running the webapp locally. You can then further test the integration with Dataiku by installing the plugin with your customizations. For this, you would change the repo URL used by the plugin installer to fetch from Git. Alternatively, you can create a ZIP file from the `dss-plugin-visual-edit` directory and upload it to the plugin installer.

In the rest of this section, we explain how to run the webapp locally. As a pre-requisite, you should configure your machine to [connect to your Dataiku instance](https://doc.dataiku.com/dss/latest/python-api/outside-usage.html#setting-up-the-connection-with-dss) (on a Mac, this is in `~/.dataiku/config.json`).

### Create a Python environment

The commands below can be run from the `dss-plugin-visual-edit` directory, from a VS Code terminal.

* Pre-requisite: install pyenv-virtualenv and Python 3.9.19 (to match the Python version used by the plugin, specified in `code-env/python/desc.json`). On a Mac:

```bash
brew install pyenv pyenv-virtualenv
pyenv install 3.9.19
```

* Create and activate a virtual environment:

```bash
pyenv virtualenv 3.9.19 visual-edit
pyenv activate visual-edit
```

* Install plugin requirements and dev requirements:

```bash
pip install --upgrade pip
pip install -r code-env/python/spec/requirements.dev.39.txt
```

* Add Dataiku API client to the virtual environment:

```bash
pip install dataiku-api-client
```

* Add Dataiku internal client to the virtual environment.
  * Copy the `dataiku` folder found in the `python` directory of your Dataiku installation to your local development machine. In the following, we assume that this folder is available in `PATH_TO_PACKAGE`.
  * Link `PATH_TO_PACKAGE/dataiku` to the virtual environment:

```bash
ln -s PATH_TO_PACKAGE/dataiku ~/.pyenv/versions/3.9.19/envs/visual-edit/lib/python3.9/site-packages/dataiku
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

## Integration tests

Visual Edit is validated against an integration test suite located in `dss-plugin-visual-edit/tests` and run on a ["test" Dataiku instance managed by the Business Solutions](https://tests-integration.solutions.dataiku-dss.io/home/).

* Tests are run automatically upon committing to the master branch or creating a Pull Request (the plugin is automatically updated on the "test" Dataiku instance beforehand).
* Tests can also be triggered from the "Actions" tab of this repository, by clicking "Run Gherkin tests" in the side bar, then clicking on "Run workflow" and choosing the branch that contains the test suite to run.
* Results can be found on the Action's run page, e.g., <https://github.com/dataiku/dss-visual-edit/actions/runs/RUN_ID/job/JOB_ID>
  * Click on the "Upload test results to workflow artifacts" step to open details
  * Look for "Artifact download URL", download and open ZIP.

Head over to `tests`' [README](tests/README.md) for more information on how tests are implemented, what is being tested, and how to run tests locally.
