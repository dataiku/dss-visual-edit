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


def __get_column_tabulator_type__(de, col_name):
    # Determine column type as string, boolean, boolean_tick, or number
    # - based on the type given in editschema_manual, if any
    # - the dataset's schema, otherwise
    ###

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
    # IDEA: improve this code with a dict to do matching (instead of if/else)?
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


### Linked records


def get_formatted_items_from_linked_df(
    linked_df: DataFrame,
    key_col: str,
    label_col: str,
    lookup_cols: Union[list, None] = None,
) -> list:
    """
    Get values of specified columns in the dataframe of a linked dataset, to be read by the `itemFormatter` provided to Tabulator when defining a linked record:

    - If no label column and no lookup columns are specified, the return value is a sorted list of key column values
    - Otherwise, the return value is a list of dicts sorted by label

    The `itemFormatter` function is defined in `custom_tabulator.js`. It is called by Tabulator for each table column which is defined as a linked record, for each row. It formats values of such columns into HTML elements, whose contents come from the dict whose `value` key matches the value of the linked record column.

    Example params:
    - linked_df: the indexed dataframe of a linked dataset
    - key_col: "id"
    - label_col: "name"
    - lookup_cols: ["col1", "col2"]

    Example return value:
    ```
    [
        {
            "value": "0f45e",
            "label": "Label One",
            "col1": "value1",
            "col2": "value2"
        },
        {
            "value": "c3d2a",
            "label": "Label Two",
            "col1": "value3",
            "col2": "value4"
        }
    ]
    ```

    If no lookup columns are specified, then the return value is:
    ```
    [
        {
            "value": "0f45e",
            "label": "Label One"
        },
        {
            "value": "c3d2a",
            "label": "Label Two"
        }
    ]
    ```

    If no lookup and label columns are specified, then the return value is:
    ```
    ["0f45e", "c3d2a"]
    ```
    """
    selected_columns = [key_col]
    if label_col != key_col:
        selected_columns += [label_col]
    if lookup_cols is not None:
        selected_columns += lookup_cols

    selected_df = (
        linked_df.reset_index()[selected_columns]
        .fillna("")  # the data table component does not handle NaN values
        .astype(str)  # it also expects all values to be strings
        .sort_values(label_col)
    )

    if len(selected_columns) == 1:
        return selected_df[selected_columns[0]].to_list()

    return selected_df.rename(columns={key_col: "value", label_col: "label"}).to_dict(
        "records"
    )


def __get_column_tabulator_linked_record__(de, linked_record_name):
    """Define Tabulator formatter and editor settings for a column whose type is linked record"""

    linked_records_df = de.linked_records_df
    linked_ds_name = linked_records_df.loc[linked_record_name, "ds_name"]
    linked_ds_key_column = linked_records_df.loc[linked_record_name, "ds_key"]
    linked_ds_label_column = linked_records_df.loc[linked_record_name, "ds_label"]
    linked_ds_lookup_columns = linked_records_df.loc[
        linked_record_name, "ds_lookup_columns"
    ]

    t_col = {}
    t_col["sorter"] = "string"

    # Formatter: if a label column was specified, get labels from the `label` endpoint and show them as user-friendly alternatives to the actual values (corresponding to primary keys of the linked dataset)
    if linked_ds_label_column != "" and linked_ds_label_column != linked_ds_key_column:
        t_col["formatter"] = assign(
            f"""
            function(cell){{
                url_base = "label/{linked_ds_name}"
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
                url_base = "lookup/{linked_ds_name}"
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
        t_col["editorParams"]["itemFormatter"] = __ns__("itemFormatter")

    return t_col


def get_columns_tabulator(de, show_header_filter=True, freeze_editable_columns=False):
    """Prepare column settings to pass to Tabulator"""

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
        # Properties to be shared by all columns
        t_col = {
            "field": col_name,
            "title": col_name,
            "headerFilter": show_header_filter,
            "resizable": True,
            "headerContextMenu": __ns__("headerMenu"),
        }

        # Define formatter and header filters based on type
        t_type = __get_column_tabulator_type__(de, col_name)
        if col_name not in linked_record_names:
            t_col.update(__get_column_tabulator_formatter__(t_type))
        if col_name in de.primary_keys:
            t_col["frozen"] = True

        # Define editor, if it's an editable column
        if col_name in de.editable_column_names:
            if freeze_editable_columns:
                t_col["frozen"] = True  # freeze to the right
            if col_name in linked_record_names:
                t_type = "linked_record"
                t_col.update(__get_column_tabulator_linked_record__(de, col_name))
            else:
                t_col.update(__get_column_tabulator_editor__(t_type))
        pretty_types = {
            "number": "Number",
            "string": "Text",
            "textarea": "Text",
            "boolean": "Checkbox",
            "boolean_tick": "Checkbox",
            "date": "Date",
            "linked_record": "Linked Record",
        }
        t_col["titleFormatter"] = assign(
            f"""
            function(cell){{
                return cell.getValue() + "<br><span class='column-type'>{pretty_types[t_type]}</span>"
            }}
            """
        )

        t_cols.append(t_col)

    return t_cols
