from dataiku.customwebapp import get_webapp_config
from json import loads, load
from os import getenv
from webapp_config_utils import get_linked_records


class WebAppConfig:
    def __init__(self) -> None:
        self.running_in_dss = getenv("DKU_CUSTOM_WEBAPP_CONFIG") is not None
        if self.running_in_dss:
            config = get_webapp_config()
            self.original_ds_name = config.get("original_dataset")
            self.debug_mode = bool(config.get("debug_mode"))

            editschema_manual_raw = config.get("editschema")
            self.editschema_manual = (
                loads(editschema_manual_raw)
                if editschema_manual_raw and editschema_manual_raw != ""
                else {}
            )
        else:
            self.original_ds_name = getenv("ORIGINAL_DATASET")
            self.debug_mode = bool(getenv("DEBUG_MODE"))

            config = load(
                open("../../webapp-settings/" + self.original_ds_name + ".json")
            )

            self.editschema_manual = config.get("editschema")
            if not self.editschema_manual:
                self.editschema_manual = {}

        self.primary_keys = config.get("primary_keys")
        self.editable_column_names = config.get("editable_column_names")
        self.freeze_editable_columns = config.get("freeze_editable_columns")
        self.group_column_names = config.get("group_column_names")
        self.linked_records_count = config.get("linked_records_count")
        self.linked_records = get_linked_records(config, self.linked_records_count)
        self.authorized_users = config.get("authorized_users")

        self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        if not self.project_key:
            raise Exception(
                "No project key configured. DKU_CURRENT_PROJECT_KEY environment variable is expected to be set."
            )
