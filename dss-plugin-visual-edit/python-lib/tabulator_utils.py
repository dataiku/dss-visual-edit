"""
This file contains functions used to generate the Tabulator columns configuration for a given dataset.
"""

from typing import Union
from pandas import DataFrame
from dash_extensions.javascript import Namespace
import logging
from dash_extensions.javascript import assign

# used to reference javascript functions in custom_tabulator.js
__ns__ = Namespace("myNamespace", "tabulator")


def __get_column_type__(de, col_name):
    """
    Determine column type as linked_record, string, boolean, boolean_tick, number, or date.

    The type is used to define the column's formatter and editor settings in Tabulator.
    It is based on...
    - linked record definitions, if any
    - the type given in editschema_manual, if any
    - the dataset's schema, otherwise:
        - the column meaning, if any
        - the column storage type, otherwise
    """

    linked_record_names = []
    if de.linked_records:
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
            not de.editschema_manual_df.empty
            and "type" in de.editschema_manual_df.columns
            and col_name in de.editschema_manual_df.index
        ):
            editschema_manual_type = de.editschema_manual_df.loc[col_name, "type"]
        else:
            editschema_manual_type = None

        # this tests that 1) editschema_manual_type isn't None, and 2) it isn't a nan
        if editschema_manual_type and editschema_manual_type == editschema_manual_type:
            t_type = editschema_manual_type
        else:
            schema_df = DataFrame(data=de.schema_columns).set_index("name")
            if "meaning" in schema_df.columns.to_list():
                schema_meaning = schema_df.loc[col_name, "meaning"]
            else:
                schema_meaning = None
            # If a meaning has been defined, we use it to infer t_type
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
                # type coming from schema
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


def __get_column_tabulator_formatter__(t_type):
    """Define Tabulator formatter settings for a column based on its type

    Returns:
        dict: Tabulator column settings
    """
    t_col = {}
    if t_type == "boolean":
        t_col["sorter"] = "boolean"
        t_col["formatter"] = "tickCross"
        t_col["formatterParams"] = {"allowEmpty": True}
        t_col["hozAlign"] = "center"
        t_col["headerFilterParams"] = {"tristate": True}
    elif t_type == "boolean_tick":
        t_col["sorter"] = "exists"
        t_col["formatter"] = "tickCross"
        t_col["formatterParams"] = {"allowEmpty": True, "crossElement": " "}
        t_col["hozAlign"] = "center"
    elif t_type == "number":
        t_col["sorter"] = "number"
        t_col["headerFilter"] = __ns__("minMaxFilterEditor")
        t_col["headerFilterFunc"] = __ns__("minMaxFilterFunction")
        t_col["headerFilterLiveFilter"] = False
    elif t_type == "date":
        t_col["sorter"] = "datetime"
        t_col["formatter"] = "datetime"
        t_col["formatterParams"] = {"inputFormat": "iso", "outputFormat": "yyyy-MM-dd"}
        t_col["headerFilterParams"] = {"format": "yyyy-MM-dd"}
    return t_col


def __get_column_tabulator_editor__(t_type):
    """Define Tabulator editor settings for a column based on its type

    Returns:
        dict: Tabulator column settings
    """
    t_col = {}
    if t_type == "boolean":
        t_col["editor"] = "list"
        t_col["editorParams"] = {
            "values": {"true": "True", "false": "False", "": "(empty)"}
        }
        t_col["headerFilter"] = "input"
        t_col["headerFilterParams"] = {}
    elif t_type == "boolean_tick":
        t_col["editor"] = "tickCross"
    elif t_type == "number":
        t_col["editor"] = "number"
    elif t_type == "date":
        t_col["editor"] = "date"
        t_col["editorParams"] = {"format": "yyyy-MM-dd"}
    elif t_type == "textarea":
        t_col["formatter"] = "textarea"
        t_col["editor"] = "textarea"
    else:
        t_col["editor"] = "input"
    return t_col
