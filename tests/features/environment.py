import locale
import logging
import os
import uuid
from urllib.parse import urljoin

from behave import use_fixture
from behave.configuration import Configuration
from behave.model import Scenario
from dssgherkin.fixtures.cleanup_managed_folders import cleanup_managed_folders
from dssgherkin.fixtures.cleanup_projects_fixture import cleanup_projects
from dssgherkin.fixtures.delete_datasets import delete_datasets
from dssgherkin.fixtures.dss_client_fixture import create_dss_client
from dssgherkin.typings.generic_context_type import AugmentedBehaveContext, Credentials
from requests import get

from features.docker.container_resources import NoopResourcesController, get_container_resources_controller
from features.steps.url_builder import (
    get_cookie_as_dict,
)

logger = logging.getLogger(__name__)

limited_container_name = os.getenv("LIMITED_CONTAINER_NAME", None)

dss_container_resources_controller = (
    get_container_resources_controller(limited_container_name) if limited_container_name else NoopResourcesController()
)


def login(context: AugmentedBehaveContext):
    context.execute_steps("Given I login to DSS")


def logout(context: AugmentedBehaveContext):
    try:
        url = urljoin(context.dss_client.host, "logged-out/")
        response = get(url, cookies=get_cookie_as_dict(context))
        response.raise_for_status()

        logger.info(f"Logged out of DSS with status code {response.status_code}.")
    except Exception as e:
        logger.error(f"Error logging out of DSS: {e}")


def before_all(context: AugmentedBehaveContext):
    config: Configuration = context.config
    config.setup_logging()

    username = os.getenv("DSS_USERNAME")
    password = os.getenv("DSS_PASSWORD")

    assert username
    assert password

    context.dss_credentials = Credentials(username, password)

    use_fixture(create_dss_client, context)


def before_scenario(context: AugmentedBehaveContext, scenario: Scenario):
    dss_container_resources_controller.restart_if_needed(scenario)

    for tag in scenario.tags:
        if tag == "cleanup_projects":
            use_fixture(cleanup_projects, context)
        if tag == "cleanup_managed_folders":
            use_fixture(cleanup_managed_folders, context)
        if tag == "delete_datasets":
            use_fixture(delete_datasets, context)

    login(context)
    project_key = uuid.uuid4().hex[:8]
    context.execute_steps(
        f"""
            Given a project created from export file "./assets/VISUALEDITINTEGRATIONTESTS.zip" with key "{project_key}"
        """
    )

    project = context.current_project
    assert project

    project_permissions = project.get_permissions()
    project_permissions["permissions"].append(
        {
            "group": "readers",
            "admin": False,
            "executeApp": True,
            "exportDatasetsData": True,
            "manageAdditionalDashboardUsers": True,
            "manageDashboardAuthorizations": True,
            "manageExposedElements": True,
            "moderateDashboards": True,
            "readDashboards": True,
            "readProjectContent": True,
            "runScenarios": True,
            "shareToWorkspaces": True,
            "writeDashboards": True,
            "writeProjectContent": True,
        }
    )
    project.set_permissions(project_permissions)


def after_scenario(context: AugmentedBehaveContext, scenario: Scenario):
    logout(context)

    webapp = context.current_webapp
    if webapp:
        if hasattr(context, "evidence_path"):
            logs = webapp.get_state().state["currentLogTail"]
            with open(
                os.path.join(context.evidence_path, f"webapp_{webapp.webapp_id}.log"),
                "w",
                encoding=locale.getpreferredencoding(False),
            ) as f:
                for line in logs["lines"]:
                    f.write(f"{line}\n")
