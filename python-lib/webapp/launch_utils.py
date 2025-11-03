from flask import Flask
from flask_cors import CORS


# This create app is used for both production & local dev environments.
def run_create_app(app: Flask) -> Flask:
    import logging

    from webapp.logging.setup import setup as setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)

    # Importing this module will actually load the configuration once and for all.
    from DataEditor import DataEditor
    from webapp.config.loader import webapp_config  # noqa: F401

    project_key = webapp_config.project_key

    editable_column_names = webapp_config.editable_column_names
    authorized_users = webapp_config.authorized_users
    freeze_edits = webapp_config.freeze_edits
    original_ds_name = webapp_config.original_ds_name
    DataEditor(
        original_ds_name=original_ds_name,
        project_key=project_key,
        primary_keys=webapp_config.primary_keys,
        editable_column_names=editable_column_names,
        linked_records=webapp_config.linked_records,
        editschema_manual=webapp_config.editschema_manual,
        authorized_users=authorized_users,
        freeze_edits=freeze_edits,
    )

    from .api import api

    CORS(app)

    app.register_blueprint(api)

    from webapp.api.middleware import handle_unexpected_error

    app.register_error_handler(Exception, handle_unexpected_error)

    @app.before_request
    def authorize_request():
        from flask import jsonify

        from commons import try_get_user_identifier
        from webapp.config.loader import webapp_config

        authorized_users = webapp_config.authorized_users
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

    return app
