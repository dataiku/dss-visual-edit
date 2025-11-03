import logging

from flask import Blueprint, Response, jsonify

from webapp.config.loader import webapp_config

logger = logging.getLogger(__name__)

config_blueprint = Blueprint("config_blueprint", __name__, url_prefix="/config")


@config_blueprint.route("", methods=["GET"])
def get_config() -> Response:
    return jsonify(
        {
            "originalDsName": webapp_config.original_ds_name,
            "primaryKeyColumnNames": webapp_config.primary_keys,
            "editableColumnNames": webapp_config.editable_column_names,
            "showHeaderFilter": webapp_config.show_header_filter,
            "freezeEditableColumns": webapp_config.freeze_editable_columns,
            "freezeEdits": webapp_config.freeze_edits,
            "groupColumnNames": webapp_config.group_column_names,
            "linkedRecords": [
                {
                    "name": lr.info.name,
                    "dsName": lr.info.ds_name,
                    "dsKey": lr.info.ds_key,
                    "dsLabel": lr.info.ds_label,
                    "dsLookupColumns": lr.info.ds_lookup_columns,
                }
                for lr in webapp_config.linked_records
            ],
            "editSchema": webapp_config.editschema_manual,
        }
    )
