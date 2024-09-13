# Integration tests

These tests are written using the Gherkin specification language and a [Dataiku library containing generic Gherkin steps](https://github.com/dataiku/dss-gherkin-steps/blob/main/README.md). See the [parent folder's README](../README.md) for more context.

## Contents

We test the following:

- Editing of columns of type int, float, and string.
- Editing datasets with a single primary key and with several primary key columns.
- Editing of a 'Reviewed' column (which should have a [special behavior](https://dataiku.github.io/dss-visual-edit/validate#special-behavior-of-the-validation-column-reviewed))
- Impact of the `labels` and `lookup_columns` configuration variables of Linked Records
- Impact of the `authorized_users` configuration variable on the ability to make edits.

All tests are performed both on a FileSystem and on a PostgreSQL connection. We test that edits are stored in the editlog dataset as expected; we also build the edits and edited datasets and we test their contents as well.

## How to set up an environment to run tests locally

- Create a Pyhton environment with test requirements found in this directory.
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- VS Code:
  - Install the [Cucumber extension](https://marketplace.visualstudio.com/items?itemName=alexkrechik.cucumberautocomplete).
  - In `tests/.vscode/`, duplicate `settings.json.example` to `settings.json` and `launch.json.example` to `launch.json`.
  - Fill in the environment variables in `settings.json`.
- Configure `.dataiku/config.json` to select the instance where the tests will run.
- Open a `.feature` file and press F5 to run the tests.
