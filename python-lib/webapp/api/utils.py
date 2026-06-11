from functools import wraps

from DataEditor import DataEditor


def use_data_editor(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        from webapp.config.loader import webapp_config

        project_key = webapp_config.project_key

        editable_column_names = webapp_config.editable_column_names
        authorized_users = webapp_config.authorized_users
        freeze_edits = webapp_config.freeze_edits
        original_ds_name = webapp_config.original_ds_name
        kwargs["data_editor"] = DataEditor(
            original_ds_name=original_ds_name,
            project_key=project_key,
            primary_keys=webapp_config.primary_keys,
            editable_column_names=editable_column_names,
            linked_records=webapp_config.linked_records,
            editschema_manual=webapp_config.editschema_manual,
            authorized_users=authorized_users,
            freeze_edits=freeze_edits,
        )

        return f(*args, **kwargs)

    return wrapper
