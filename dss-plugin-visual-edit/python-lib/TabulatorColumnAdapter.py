"""
Tabulator adapter for generating columns configuration for Tabulator data table component.
All Tabulator-specific logic is encapsulated here.
"""

import logging
from pandas import DataFrame
from dash_extensions.javascript import Namespace
from dash_extensions.javascript import assign
from tabulator_linked_fields import __get_column_linked_record__

# used to reference javascript functions in custom_tabulator.js
__ns__ = Namespace("myNamespace", "tabulator")


from BaseColumnAdapter import BaseColumnAdapter


class TabulatorColumnAdapter(BaseColumnAdapter):
    @staticmethod
    def get_column_type(de, col_name):
        # Delegate to shared logic in BaseColumnAdapter
        return BaseColumnAdapter.get_column_type(de, col_name)

    @staticmethod
    def get_column_formatter(t_type):
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
            t_col["formatterParams"] = {
                "inputFormat": "iso",
                "outputFormat": "yyyy-MM-dd",
            }
            t_col["headerFilterParams"] = {"format": "yyyy-MM-dd"}
        return t_col

    @staticmethod
    def get_column_editor(t_type):
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


def get_columns_tabulator(de, show_header_filter=True, freeze_editable_columns=False):
    """
    Prepare column settings to pass to Tabulator
    """

    linked_record_names = []
    if de.linked_records:
        try:
            linked_records_df = de.linked_records_df
            linked_record_names = linked_records_df.index.values.tolist()
        except Exception:
            logging.exception("Failed to get linked record names.")

    t_cols = []
    for col_name in (
        de.primary_keys + de.display_column_names + de.editable_column_names
    ):
        # Properties to be shared by all columns: enable header filters, column resizing, and a special menu on right-click of column header
        t_col = {
            "field": col_name,
            "title": col_name,
            "headerFilter": show_header_filter,
            "resizable": True,
            "headerContextMenu": __ns__("headerMenu"),
        }

        # Define formatter and header filters based on type
        t_type = TabulatorColumnAdapter.get_column_type(de, col_name)
        if col_name not in linked_record_names:
            t_col.update(TabulatorColumnAdapter.get_column_formatter(t_type))
        if col_name in de.primary_keys or (
            col_name in de.editable_column_names and freeze_editable_columns
        ):
            t_col["frozen"] = True

        # Define the column's "title formatter" to show the column type below its name
        t_col["titleFormatter"] = assign(
            f"""
            function(cell){{
                return cell.getValue() + "<br><span class='column-type'>{TabulatorColumnAdapter.get_pretty_type(t_type)}</span>"
            }}
            """
        )

        # Define the column's formatter, header filters, and editor (if editable)
        t_col.update(TabulatorColumnAdapter.get_column_formatter(t_type))
        if col_name in de.editable_column_names:
            if t_type == "linked_record":
                t_col.update(__get_column_linked_record__(de, col_name))
            else:
                t_col.update(TabulatorColumnAdapter.get_column_editor(t_type))

        t_cols.append(t_col)

    return t_cols
