from behave import use_fixture
from behave.configuration import Configuration
from behave.runner import Context
from dssgherkin.fixtures.cleanup_managed_folders import cleanup_managed_folders
from dssgherkin.fixtures.cleanup_projects_fixture import cleanup_projects
from dssgherkin.fixtures.delete_datasets import delete_datasets
from dssgherkin.fixtures.dss_client_fixture import create_dss_client


def before_all(context: Context):
    config: Configuration = context.config
    config.setup_logging()


def before_scenario(context, scenario):
    use_fixture(create_dss_client, context)
    for tag in scenario.tags:
        if tag == "cleanup_projects":
            use_fixture(cleanup_projects, context)
        if tag == "cleanup_managed_folders":
            use_fixture(cleanup_managed_folders, context)
        if tag == "delete_datasets":
            use_fixture(delete_datasets, context)
