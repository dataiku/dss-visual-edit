"""
TabulatorColumnAdapter: Generates column configuration for Tabulator data table component.
All Tabulator-specific logic is encapsulated here. Inherits shared logic from BaseColumnAdapter.
"""

import logging
from pandas import DataFrame
from dash_extensions.javascript import Namespace
from dash_extensions.javascript import assign

# used to reference javascript functions in custom_tabulator.js
__ns__ = Namespace("myNamespace", "tabulator")

from BaseColumnAdapter import BaseColumnAdapter


class TabulatorColumnAdapter(BaseColumnAdapter):
    """
    Adapter to generate Tabulator-specific column configuration from DataEditor schema info.
    """

    @staticmethod
    def get_column_type(de, col_name):
        # Delegate to shared logic in BaseColumnAdapter
        return BaseColumnAdapter.get_column_type(de, col_name)

    @staticmethod
    def get_column_configuration(t_type):
        """
        Returns Tabulator-specific formatting options for the given column type.
        Args:
            t_type (str): The inferred type of the column.
        Returns:
            dict: Tabulator formatting options for the column.
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
            t_col["formatterParams"] = {
                "inputFormat": "iso",
                "outputFormat": "yyyy-MM-dd",
            }
            t_col["headerFilterParams"] = {"format": "yyyy-MM-dd"}
        return t_col

    @staticmethod
    def get_column_editor_configuration(t_type):
        """
        Returns Tabulator-specific editor options for the given column type.
        Args:
            t_type (str): The inferred type of the column.
        Returns:
            dict: Tabulator editor options for the column.
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

    @staticmethod
    def get_title_formatter(t_type):
        """
        Returns a Tabulator JS function to format the column title, showing the pretty type below the name.
        Args:
            t_type (str): The inferred type of the column.
        Returns:
            assign: JS function for Tabulator's titleFormatter.
        """
        return assign(
            f"""
            function(cell){{
                return cell.getValue() + "<br><span class='column-type'>{TabulatorColumnAdapter.get_pretty_type(t_type)}</span>"
            }}
            """
        )

    @staticmethod
    def get_linked_record_configuration(de, col_name):
        """
        Returns Tabulator-specific formatter and editor settings for a column whose type is linked record.

        Args:
            de: DataEditor instance or similar object with schema info.
            col_name (str): Name of the linked record column.
        Returns:
            dict: Tabulator formatter and editor options for the linked record column.

        This method wires up Tabulator-specific JS hooks:
        - Uses Tabulator list editor and editorParams (valuesLookup, filterRemote, itemFormatter).
        - Embeds JS Ajax calls and references to Namespace-based JS helpers.
        """
        linked_records_df = de.linked_records_df
        linked_ds_name = linked_records_df.loc[col_name, "ds_name"]
        linked_ds_key_column = linked_records_df.loc[col_name, "ds_key"]
        linked_ds_label_column = linked_records_df.loc[col_name, "ds_label"]
        linked_ds_lookup_columns = linked_records_df.loc[col_name, "ds_lookup_columns"]

        t_col = {}
        t_col["sorter"] = "string"

        # Formatter: if a label column was specified, get labels from the `label` endpoint and show them as user-friendly alternatives to the actual values (corresponding to primary keys of the linked dataset)
        if (
            linked_ds_label_column != ""
            and linked_ds_label_column != linked_ds_key_column
        ):
            t_col["formatter"] = assign(
                f"""
                function(cell){{
                    url_base = "linked-label/{linked_ds_name}"
                    key = cell.getValue()
                    label = ""
                    // Send GET request to `url_base`, with parameter `key`
                    // Assign returned value to the `label` variable; in case connection fails, assign empty value to label
                    $.ajax({{
                        url: url_base + "?key=" + key,
                        async: false,
                        success: function(result){{
                            label = result
                        }},
                        error: function(result){{
                            label = ""
                            console.log("Could not retrieve label from server")
                        }}
                    }});
                    // if label is empty, return empty string
                    if (label == "") {{
                        return label
                    }} else {{
                        return "<span class='linked-record'>" + label + "</span>"
                    }}
                }}
                """
            )

        # Editor: use "list" for a dropdown
        t_col["editor"] = "list"
        t_col["editorParams"] = {
            "clearable": True,
            "elementAttributes": {"maxlength": "20"},
            "emptyValue": None,
            "placeholderLoading": "Loading List...",
            "placeholderEmpty": "No Results Found",
            "autocomplete": True,
            "filterRemote": True,
            "filterDelay": 300,
            "allowEmpty": False,
            "listOnEmpty": True,
            "freetext": False,
        }
        # Editor: get values from the `lookup` endpoint
        t_col["editorParams"]["valuesLookup"] = assign(
            f"""
                function(cell, filterTerm){{
                    url_base = "linked-options/{linked_ds_name}"
                    key = cell.getValue()
                    optionsList = []
                    // Send GET request to `url_base`, with parameter `key`
                    // Assign returned value to the `label` variable; in case connection fails, assign empty value to label
                    $.ajax({{
                        url: url_base + "?key=" + key + "&term=" + filterTerm,
                        async: false,
                        success: function(result){{
                            optionsList = result
                        }},
                        error: function(result){{
                            optionsList = []
                            console.log("Could not retrieve options from server")
                        }}
                    }});
                    return optionsList
                }}
                """
        )
        # Editor: format items in the list if lookup columns were provided (in which case items are structured)
        if linked_ds_lookup_columns != []:
            t_col["editorParams"]["itemFormatter"] = __ns__("listItemFormatter")

        return t_col


def get_columns_tabulator(de, show_header_filter=True, freeze_editable_columns=False):
    """
    Generate Tabulator column configuration using TabulatorColumnAdapter and add Tabulator-specific options.
    Args:
        de: DataEditor instance or similar object with schema info.
        show_header_filter (bool): Whether to show header filters.
        freeze_editable_columns (bool): Whether to freeze editable columns.
    Returns:
        list: List of Tabulator column configuration dictionaries.
    """
    cols = TabulatorColumnAdapter.get_columns(
        de, show_header_filter, freeze_editable_columns
    )
    # Because the definition of column header menu is common to all columns, we implement it here
    for col in cols:
        col["headerContextMenu"] = __ns__("columnHeaderMenu")
    return cols
