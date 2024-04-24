from __future__ import annotations
from typing import Any, List
from dataiku.customwebapp import get_webapp_config
from json import load
from os import getenv
from webapp.config.models import Config, LinkedRecordInfo, LinkedRecord


class WebAppConfig:
    def __init__(self) -> None:
        self.running_in_dss = getenv("DKU_CUSTOM_WEBAPP_CONFIG") is not None
        if self.running_in_dss:
            dic_config = get_webapp_config()
            typed_config = Config(**dic_config)
            self.__validate_original_dataset_name__(typed_config.original_dataset)

        else:
            original_ds_name = self.__validate_original_dataset_name__(
                getenv("ORIGINAL_DATASET")
            )
            dic_config = load(open(f"../../webapp-settings/{original_ds_name}.json"))
            typed_config = Config(**dic_config)
            typed_config.original_dataset = original_ds_name

        self.original_ds_name = typed_config.original_dataset
        self.primary_keys = typed_config.primary_keys
        self.editable_column_names = typed_config.editable_column_names
        self.freeze_editable_columns = typed_config.freeze_editable_columns
        self.group_column_names = typed_config.group_column_names
        self.linked_records_count = typed_config.linked_records_count
        self.linked_records = self.__get_linked_records__(
            dic_config, self.linked_records_count
        )
        self.editschema_manual = typed_config.editschema

        self.authorized_users = typed_config.authorized_users

        self.project_key = self.__get_project_key__()

    def __validate_original_dataset_name__(self, name: Any) -> str:
        if name is None or not isinstance(name, str):
            raise Exception(f"original_dataset value '{name}' is invalid.")
        return name

    def __get_project_key__(self) -> str:
        key = getenv("DKU_CURRENT_PROJECT_KEY")
        if not key:
            raise Exception(
                "No project key configured. DKU_CURRENT_PROJECT_KEY environment variable is expected to be set."
            )
        return key

    def __get_linked_records__(
        self, params, linked_records_count: int
    ) -> List[LinkedRecord]:
        """
        Get linked records from webapp parameters, as a list of dictionaries
        """
        linked_records: List[LinkedRecord] = []
        # if linked_records_count is not None and is positive
        if linked_records_count > 0:
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
                    LinkedRecord(
                        LinkedRecordInfo(
                            name, ds_name, ds_key, ds_label, ds_lookup_columns
                        )
                    )
                )
        return linked_records
