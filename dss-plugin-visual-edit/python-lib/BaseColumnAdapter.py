"""
BaseColumnAdapter: Common logic for generating column definitions for data table components (Tabulator, AgGrid, etc).
"""

from typing import Any
from pandas import DataFrame
import logging


class BaseColumnAdapter:
    @staticmethod
    def get_column_type(de, col_name):
        """
        Determine column type as linked_record, string, boolean, boolean_tick, number, or date.
        Shared logic for all table components.
        """
        linked_record_names = []
        if hasattr(de, "linked_records") and de.linked_records:
            try:
                linked_records_df = de.linked_records_df
                linked_record_names = linked_records_df.index.values.tolist()
            except Exception:
                logging.exception("Failed to get linked record names.")
        if col_name in linked_record_names:
            t_type = "linked_record"
        else:
            t_type = "string"  # default type
            if (
                hasattr(de, "editschema_manual_df")
                and not de.editschema_manual_df.empty
                and "type" in de.editschema_manual_df.columns
                and col_name in de.editschema_manual_df.index
            ):
                editschema_manual_type = de.editschema_manual_df.loc[col_name, "type"]
            else:
                editschema_manual_type = None
            if (
                editschema_manual_type
                and editschema_manual_type == editschema_manual_type
            ):
                t_type = editschema_manual_type
            else:
                schema_df = DataFrame(data=de.schema_columns).set_index("name")
                if "meaning" in schema_df.columns.to_list():
                    schema_meaning = schema_df.loc[col_name, "meaning"]
                else:
                    schema_meaning = None
                if schema_meaning and schema_meaning == schema_meaning:
                    if schema_meaning == "Boolean":
                        t_type = "boolean"
                    if (
                        schema_meaning == "DoubleMeaning"
                        or schema_meaning == "LongMeaning"
                        or schema_meaning == "IntMeaning"
                    ):
                        t_type = "number"
                    if schema_meaning == "Date":
                        t_type = "date"
                else:
                    schema_type = schema_df.loc[col_name, "type"]
                    if schema_type == "boolean":
                        t_type = "boolean"
                    if schema_type in [
                        "tinyint",
                        "smallint",
                        "int",
                        "bigint",
                        "float",
                        "double",
                    ]:
                        t_type = "number"
                    if schema_type == "date":
                        t_type = "date"
        return t_type

    @staticmethod
    def get_pretty_type(t_type):
        pretty_types = {
            "number": "Number",
            "string": "Text",
            "textarea": "Text",
            "boolean": "Checkbox",
            "boolean_tick": "Checkbox",
            "date": "Date",
            "linked_record": "Linked Record",
        }
        return pretty_types.get(t_type, t_type)
