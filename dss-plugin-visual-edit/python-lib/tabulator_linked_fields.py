### Linked Fields

from typing import Union
from pandas import DataFrame
from dash_extensions.javascript import Namespace
from dash_extensions.javascript import assign

# used to reference javascript functions in custom_tabulator.js
__ns__ = Namespace("myNamespace", "tabulator")


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


def __get_column_linked_record__(de, linked_record_name):
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
