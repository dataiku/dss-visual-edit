# Development

Most changes to the code can be tested by running the webapp locally. You can then further test the integration with Dataiku by installing the plugin with your customizations. For this, you would change the repo URL used by the plugin installer to fetch from Git. Alternatively, you can create a ZIP file from the `dss-plugin-visual-edit` directory and upload it to the plugin installer.

## Running the webapp locally

In the rest of this section, we explain how to run the webapp locally. As a pre-requisite, you should configure your machine to [connect to your Dataiku instance](https://doc.dataiku.com/dss/latest/python-api/outside-usage.html#setting-up-the-connection-with-dss) (on a Mac, this is in `~/.dataiku/config.json`).

### Create a Python environment

* Pre-requisite: install pyenv-virtualenv. On a Mac:

```bash
brew install pyenv pyenv-virtualenv
```

* Create and activate a Python 3.9 virtual environment (to match the Python version used by the plugin, specified in `code-env/python/desc.json`):

```bash
pyenv virtualenv 3.9.19 visual-edit
pyenv activate visual-edit
```

* Install plugin requirements and dev requirements:

```bash
pip install --upgrade pip
pip install -r code-env/python/spec/requirements.txt
pip install -r code-env/python/spec/requirements.dev.39.txt
```

* Add Dataiku internal client to the environment. This can be done by linking to the `dataiku` and `dataikuapi` packages that already exist in your Dataiku installation:

```bash
ln -s PATH_TO_PACKAGES/dataiku ~/.pyenv/versions/3.9.19/envs/visual-edit/lib/python3.9/site-packages/dataiku
ln -s PATH_TO_PACKAGES/dataikuapi ~/.pyenv/versions/3.9.19/envs/visual-edit/lib/python3.9/site-packages/dataikuapi
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
