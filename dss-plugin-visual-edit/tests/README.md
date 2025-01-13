# Tests

## Which Connections are compatible with Visual Edit?

As explained in the [deployment guide](https://dataiku.github.io/dss-visual-edit/deploy), we strongly recommend using an SQL connection for the `editlog` and `edits` datasets; it is not necessary to change the connection of the Original Dataset nor of the `edited` dataset.

You may use other connections for demo/evaluation purposes (e.g. looking at the webapp UX and the integration with the Flow).

Here is an overview of what was explicitly tested and what is expected to work.

* **Persisting edits** (i.e. appending rows to the `editlog` dataset):
  * ✅ We run automated tests on **PostgreSQL** and **FileSystem**.
  * ✅ We successfully tested manually on **Snowflake**.
  * ⚠️ We successfully tested manually on **S3** but each edit resulted in a new file, which is not ideal.
  * ❓ Persisting edits may not work with other connections, including SQL ones. For instance, it fails on BigQuery.
  * This is because the implementation is based on the `write_dataframe` method of the Dataiku API, which may fail when the dataset is in "append only" mode (as is the case with the `editlog`).
* **Building `edits` and `edited` datasets** from an `editlog`, and showing edited data in the webapp, is expected to work on all connections as it is based on the `get_dataframe` and `write_dataframe` methods of the Dataiku API.
* **Initializing a secure `editlog`**: successful manual tests on PostgreSQL (see deployment guide).

## Automated Integration Tests

These tests are written using the Gherkin specification language and a [Dataiku library containing generic Gherkin steps](https://github.com/dataiku/dss-gherkin-steps/blob/main/README.md). See the [parent folder's README](../README.md) for more context.

### Contents

We test the following:

- Editing of columns of type int, float, and string.
- Editing datasets with a single primary key and with several primary key columns.
- Editing of a validation column (which should have a [special behavior](https://dataiku.github.io/dss-visual-edit/validate#special-behavior-of-the-validation-column))
- Impact of the `labels` and `lookup_columns` configuration variables of Linked Records
- Impact of the `authorized_users` configuration variable on the ability to make edits.

All tests are performed both on a FileSystem and on a PostgreSQL connection. We test that edits are stored in the editlog dataset as expected; we also build the edits and edited datasets and we test their contents as well.

### How to set up an environment to run tests locally

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
