import logging

from dataiku import api_client
from flask import Blueprint, Response, jsonify

from commons import get_last_build_date, try_get_user_identifier
from DataEditor import DataEditor
from webapp.api.utils import use_data_editor
from webapp.config.loader import webapp_config

logger = logging.getLogger(__name__)

layout_blueprint = Blueprint("layout_blueprint", __name__, url_prefix="/layout")


@layout_blueprint.route("", methods=["GET"])
@use_data_editor
def layout_endpoint(data_editor: DataEditor) -> Response:
    global last_build_date_initial, last_build_date_ok
    original_ds_name = webapp_config.original_ds_name
    authorized_users = webapp_config.authorized_users
    project = api_client().get_project(webapp_config.project_key)
    try:
        last_build_date_initial = get_last_build_date(original_ds_name, project)
        last_build_date_ok = True
    except Exception:
        logger.warning(
            "Failed to get last build date of %s. Serve layout without this information.",
            original_ds_name,
            exc_info=True,
        )
        last_build_date_initial = ""
        last_build_date_ok = False

    user_id = try_get_user_identifier()

    # If authorized users are configured:
    # 1. failing to resolve user info
    # 2. not being in the list of authorized users
    # leads to unauthorized access.
    if authorized_users:
        if user_id is None or user_id not in authorized_users:
            logger.warning("Unauthorized user %s tried to access the webapp.", user_id)
            response = jsonify({"error": "Unauthorized"})
            response.status_code = 403
            return response

    columns = []
    layout = {
        "datasetName": original_ds_name,
        "columns": columns,
        "data": data_editor.get_edited_df().to_dict("records"),
        "groupBy": webapp_config.group_column_names,
    }
    return jsonify(layout)
