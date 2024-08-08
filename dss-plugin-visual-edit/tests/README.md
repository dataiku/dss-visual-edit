# Integration tests
These integrations tests are based on Gherkin language. It uses generic steps developed in a private repository. They are available as a python module.

A CI is setup to run these tests on demand.

## Setup local test run environment.
- Create pyhton env with its requirements.
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- Install [Cucumber vscode extension](https://marketplace.visualstudio.com/items?itemName=alexkrechik.cucumberautocomplete).


- Setup vscode.

In tests/.vscode, duplicate `settings.json.example` to `settings.json` and `launch.json.example` to `launch.json`.

- Configure `.dataiku/config.json` to select the instance where the tests will run.

- Fill in the environment variables in `settings.json`.

- Open a feature file, and press F5 to run the tests.
