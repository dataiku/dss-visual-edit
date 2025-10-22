"""
AG Grid utility functions to generate column configuration for Dash AG Grid.
"""

from typing import Union
from pandas import DataFrame
import logging

from DataEditor import DataEditor

def _get_column_aggrid_data_type(dku_col_type: str, dku_col_meaning: str) -> dict:
    if dku_col_type in ["int", "bigint", "double", "float"]:
        return { "cellDataType": "number" }
    elif dku_col_type == "boolean":
        return { "cellDataType": "boolean" }
    elif dku_col_type == "date":
        return { "cellDataType": "dateTimeString" }
    elif dku_col_type == "datetime":
        return { "cellDataType": "dateTimeString" }
    else:
        if dku_col_meaning == "URL":
            return { 
                "cellRenderer": "VisualEditLinkComponent",
                "headerTooltip": "URL Link"
            }
                
        return { "cellDataType": "text" }
    
def _get_column_aggrid_cell_editor(dku_col_type: str, dku_col_meaning: str) -> dict:
    if dku_col_type in ["int", "bigint", "double", "float"]:
        return { "cellEditor": "agNumericCellEditor" }
    elif dku_col_type == "boolean":
        return { "cellEditor": "agCheckboxCellEditor" }
    elif dku_col_type == "date" or dku_col_type == "datetime":
        return { "cellEditor": "agDateCellEditor" }
    else:
        return {"cellEditor": "agLargeTextCellEditor", "cellEditorPopup": True}

def _get_pk_column_def_aggrid(col_name: str, dku_col_type: str, dku_col_meaning: str, show_header_filter: bool) -> dict:
    ag_data_type = _get_column_aggrid_data_type(dku_col_type, dku_col_meaning)
    col_def = {
        "field": col_name,
        "headerName": col_name,
        "editable": False,
        "resizable": True,
        "filter": show_header_filter,
        "filterParams": {
            "buttons": ["reset", "apply"],
            "closeOnApply": True
        },
    }
    return col_def | ag_data_type

def _get_display_column_def_aggrid(col_name: str, dku_col_type: str, dku_col_meaning: str, show_header_filter: bool) -> dict:
    ag_data_type = _get_column_aggrid_data_type(dku_col_type, dku_col_meaning)
    col_def = {
        "field": col_name,
        "headerName": col_name,
        "editable": False,
        "resizable": True,
        "filter": show_header_filter,
        "filterParams": {
            "buttons": ["reset", "apply"],
            "closeOnApply": True
        },
    }
    return col_def | ag_data_type

def _get_editable_column_def_aggrid(col_name: str, dku_col_type: str, dku_col_meaning: str, show_header_filter: bool, freeze_editable_columns: bool) -> dict:
    ag_data_type = _get_column_aggrid_data_type(dku_col_type, dku_col_meaning)
    ag_cell_editor = _get_column_aggrid_cell_editor(dku_col_type, dku_col_meaning)
    # Alternate red shades for editable columns (even: deep red, odd: light red)
    col_def = {
        "field": col_name,
        "headerName": col_name,
        "editable": True,
        "resizable": not freeze_editable_columns,
        "filter": show_header_filter,
        "filterParams": {
            "buttons": ["reset", "apply"],
            "closeOnApply": True
        }
    }
    return col_def | ag_data_type | ag_cell_editor

def _get_linked_record_column_def_aggrid(col_name: str, dku_col_type: str, dku_col_meaning: str, linked_ds_name: str, show_header_filter: bool) -> dict:
    ag_data_type = _get_column_aggrid_data_type(dku_col_type, dku_col_meaning)
    return {
        "field": col_name,
        "headerName": col_name,
        "editable": True,
        "cellEditor": "agRichSelectCellEditor",
        "cellEditorParams": {
            # "values": [0, 1, 2, 3, 4, 5],  # Placeholder values; in practice, this should be dynamically fetched
            # "values": { "function": "visualEditGetLinkedRecords(params)" },
            "function": "visualEditGetLinkedRecords(params)",
            # "allowTyping": True,
            # "filterList": True,
            # "highlightMatch": True
        },
        "linkedDatasetName": linked_ds_name,
        "filter": show_header_filter,
        "resizable": True,
    } | ag_data_type


def get_columns_aggrid(de: DataEditor, show_header_filter=True, freeze_editable_columns=False):
    # Similar logic to Tabulator, but adapted for AG Grid
    linked_record_names = []
    if de.linked_records:
        try:
            linked_records_df = de.linked_records_df
            linked_record_names = linked_records_df.index.values.tolist()
        except Exception:
            logging.exception("Failed to get linked record names.")

    ag_cols = []

    ag_pk_cols = []
    for pk_col in de.primary_keys:
        col_type: str = de.schema_columns_df.loc[pk_col, "type"] # type: ignore
        col_meaning: str = de.schema_columns_df.loc[pk_col, "meaning_id"] if "meaning_id" in de.schema_columns_df.columns else "" # type: ignore
        col_def = _get_pk_column_def_aggrid(pk_col, col_type, col_meaning, show_header_filter)
        ag_pk_cols.append(col_def)

    ag_cols.append({"headerName": "Row identification", "children": ag_pk_cols, "marryChildren": True})

    ag_display_cols = []
    for display_col in de.display_column_names:
        col_type: str = de.schema_columns_df.loc[display_col, "type"] # type: ignore
        col_meaning: str = de.schema_columns_df.loc[display_col, "meaning"] if "meaning" in de.schema_columns_df.columns else "" # type: ignore
        col_def = _get_display_column_def_aggrid(display_col, col_type, col_meaning, show_header_filter)
        ag_display_cols.append(col_def)

    ag_cols.append({"headerName": "Contextual information", "children": ag_display_cols, "marryChildren": True})

    schema_df = de.schema_columns_df
    for col_name in de.editable_column_names:
        col_type = schema_df.loc[col_name, "type"] # type: ignore
        col_meaning: str = de.schema_columns_df.loc[col_name, "meaning"] if "meaning" in de.schema_columns_df.columns else "" # type: ignore
        if col_name in linked_record_names:
            # Linked record column
            linked_ds_name = linked_records_df.loc[col_name, "ds_name"] # type: ignore
            col_def = _get_linked_record_column_def_aggrid(col_name, col_type, col_meaning, linked_ds_name, show_header_filter)
            ag_cols.append(col_def)
            continue
        col_def = _get_editable_column_def_aggrid(col_name, col_type, col_meaning, show_header_filter, freeze_editable_columns)
        ag_cols.append(col_def)
    return ag_cols


def get_formatted_items_from_linked_df(
    linked_df: DataFrame,
    key_col: str,
    label_col: str,
    lookup_cols: Union[list, None] = None,
) -> list:
    # Reuse logic from tabulator_utils if needed
    selected_columns = [key_col]
    if label_col != key_col:
        selected_columns += [label_col]
    if lookup_cols is not None:
        selected_columns += lookup_cols
    selected_df = linked_df.reset_index()[selected_columns].fillna("").astype(str).sort_values(label_col)
    if len(selected_columns) == 1:
        return selected_df[selected_columns[0]].to_list()
    return selected_df.rename(columns={key_col: "value", label_col: "label"}).to_dict("records")
