import os
import locale
from pathlib import Path
import re
from behave import use_fixture
from behave.configuration import Configuration
from behave.model import Scenario, Status
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

    use_fixture(create_dss_client, context)


def before_scenario(context: AugmentedBehaveContext, scenario: Scenario):
    for tag in scenario.tags:
        if tag == "cleanup_projects":
            use_fixture(cleanup_projects, context)
        if tag == "cleanup_managed_folders":
            use_fixture(cleanup_managed_folders, context)
        if tag == "delete_datasets":
            use_fixture(delete_datasets, context)

    project_key_suffix = re.sub(
        r"[^A-Za-z0-9]", "", Path(scenario.filename).stem
    ).upper()
    project_key = f"VISUALEDIT{project_key_suffix}"

    context.execute_steps(
        f"""
            Given I login to DSS
            And a project created from export file "./assets/VISUALEDITINTEGRATIONTESTS.zip" with key "{project_key}"
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
    webapp = context.current_webapp
    if scenario.status is Status.failed and webapp:
        if hasattr(context, "evidence_path"):
            logs = webapp.get_state().state["currentLogTail"]
            with open(
                os.path.join(context.evidence_path, f"webapp_{webapp.webapp_id}.log"),
                "w",
                encoding=locale.getpreferredencoding(False),
            ) as f:
                for line in logs["lines"]:
                    f.write(f"{line}\n")
