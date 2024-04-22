from dataiku.customwebapp import get_webapp_config
from json import loads, load
from os import getenv


class WebAppConfig:
    def __init__(self) -> None:
        self.running_in_dss = getenv("DKU_CUSTOM_WEBAPP_CONFIG") is not None
        if self.running_in_dss:
            config = get_webapp_config()
            self.original_ds_name = config.get("original_dataset")

            editschema_manual_raw = config.get("editschema")
            self.editschema_manual = (
                loads(editschema_manual_raw)
                if editschema_manual_raw and editschema_manual_raw != ""
                else {}
            )
        else:
            self.original_ds_name = getenv("ORIGINAL_DATASET")

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
        self.linked_records = self.__get_linked_records__(
            config, self.linked_records_count
        )
        self.authorized_users = config.get("authorized_users")

        self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        if not self.project_key:
            raise Exception(
                "No project key configured. DKU_CURRENT_PROJECT_KEY environment variable is expected to be set."
            )

    def __get_linked_records__(self, params, linked_records_count):
        """
        Get linked records from webapp parameters, as a list of dictionaries
        """
        linked_records = []
        # if linked_records_count is not None and is positive
        if linked_records_count and linked_records_count > 0:
            for c in range(1, linked_records_count + 1):
                name = params.get(f"linked_record_name_{c}")
                ds_name = params.get(f"linked_record_ds_name_{c}")
                ds_key = params.get(f"linked_record_key_{c}")
                ds_label = params.get(f"linked_record_label_column_{c}")
                ds_lookup_columns = params.get(f"linked_record_lookup_columns_{c}")
                if not ds_label:
                    ds_label = ds_key
                if not ds_lookup_columns:
                    ds_lookup_columns = []
                linked_records.append(
                    {
                        "name": name,
                        "ds_name": ds_name,
                        "ds_key": ds_key,
                        "ds_label": ds_label,
                        "ds_lookup_columns": ds_lookup_columns,
                    }
                )
        return linked_records
