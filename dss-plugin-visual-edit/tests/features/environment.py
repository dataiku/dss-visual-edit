import os
from behave import use_fixture
from behave.configuration import Configuration
from dssgherkin.fixtures.cleanup_managed_folders import cleanup_managed_folders
from dssgherkin.fixtures.cleanup_projects_fixture import cleanup_projects
from dssgherkin.fixtures.delete_datasets import delete_datasets
from dssgherkin.fixtures.dss_client_fixture import create_dss_client
from dssgherkin.typings.generic_context_type import AugmentedBehaveContext, Credentials


def before_all(context: AugmentedBehaveContext):
    config: Configuration = context.config
    config.setup_logging()

    username = os.getenv("DSS_USERNAME")
    password = os.getenv("DSS_PASSWORD")

    assert username
    assert password

    context.dss_credentials = Credentials(username, password)


def before_scenario(context, scenario):
    use_fixture(create_dss_client, context)
    for tag in scenario.tags:
        if tag == "cleanup_projects":
            use_fixture(cleanup_projects, context)
        if tag == "cleanup_managed_folders":
            use_fixture(cleanup_managed_folders, context)
        if tag == "delete_datasets":
            use_fixture(delete_datasets, context)
