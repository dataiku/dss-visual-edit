from typing import List, Union

from pandas import DataFrame

from DataEditor import DataEditor
from webapp.config.models import EditSchema


def _get_user_column_def_override(col_name: str, edit_schema: List[EditSchema]) -> dict:
    for col_def in edit_schema:
        if col_def.name == col_name:
            return col_def.aggrid_col_def
    return {}


def _to_aggrid_data_type(dku_col_type: str, dku_col_meaning: str) -> dict:
    if dku_col_type in ["int", "bigint", "double", "float"]:
        return {"cellDataType": "number"}
    elif dku_col_type == "boolean":
        return {"cellDataType": "boolean"}
    elif dku_col_type == "date":
        return {"cellDataType": "dateTimeString"}
    elif dku_col_type == "datetime":
        return {"cellDataType": "dateTimeString"}
    else:
        if dku_col_meaning == "URL":
            return {"cellRenderer": "DkuUrlLinkCellRenderer", "headerTooltip": "URL Link"}

        return {"cellDataType": "text"}


def _to_aggrid_cell_editor(dku_col_type: str, dku_col_meaning: str) -> dict:
    if dku_col_type in ["int", "bigint", "double", "float"]:
        return {"cellEditor": "agNumericCellEditor"}
    elif dku_col_type == "boolean":
        return {"cellEditor": "agCheckboxCellEditor"}
    elif dku_col_type == "date" or dku_col_type == "datetime":
        return {"cellEditor": "agDateCellEditor"}
    else:
        return {"cellEditor": "agLargeTextCellEditor", "cellEditorPopup": True}


def _get_pk_column_def_aggrid(
    col_name: str, dku_col_type: str, dku_col_meaning: str, show_header_filter: bool, edit_schema: List[EditSchema]
) -> dict:
    ag_data_type = _to_aggrid_data_type(dku_col_type, dku_col_meaning)
    col_def = {
        "field": col_name,
        "headerName": col_name,
        "editable": False,
        "resizable": True,
        "filter": show_header_filter,
        "filterParams": {"buttons": ["reset", "apply"], "closeOnApply": True},
    }
    return col_def | ag_data_type | _get_user_column_def_override(col_name, edit_schema)


def _get_display_column_def_aggrid(
    col_name: str, dku_col_type: str, dku_col_meaning: str, show_header_filter: bool, edit_schema: List[EditSchema]
) -> dict:
    ag_data_type = _to_aggrid_data_type(dku_col_type, dku_col_meaning)
    col_def = {
        "field": col_name,
        "headerName": col_name,
        "editable": False,
        "resizable": True,
        "filter": show_header_filter,
        "filterParams": {"buttons": ["reset", "apply"], "closeOnApply": True},
    }
    return col_def | ag_data_type | _get_user_column_def_override(col_name, edit_schema)


def _get_editable_column_def_aggrid(
    col_name: str,
    dku_col_type: str,
    dku_col_meaning: str,
    show_header_filter: bool,
    freeze_editable_columns: bool,
    edit_schema: List[EditSchema],
) -> dict:
    ag_data_type = _to_aggrid_data_type(dku_col_type, dku_col_meaning)
    ag_cell_editor = _to_aggrid_cell_editor(dku_col_type, dku_col_meaning)
    # Alternate red shades for editable columns (even: deep red, odd: light red)
    col_def = {
        "field": col_name,
        "headerName": col_name,
        "editable": True,
        "resizable": not freeze_editable_columns,
        "filter": show_header_filter,
        "filterParams": {"buttons": ["reset", "apply"], "closeOnApply": True},
    }
    return col_def | ag_data_type | ag_cell_editor | _get_user_column_def_override(col_name, edit_schema)


def _get_linked_record_column_def_aggrid(
    col_name: str, dku_col_type: str, dku_col_meaning: str, linked_ds_name: str, show_header_filter: bool
) -> dict:
    ag_data_type = _to_aggrid_data_type(dku_col_type, dku_col_meaning)
    return {
        "field": col_name,
        "headerName": col_name,
        "editable": True,
        "cellEditor": "agRichSelectCellEditor",
        "cellEditorParams": {
            "function": "dkuLinkedRecordsCellEditor(params)",
        },
        "linkedDatasetName": linked_ds_name,
        "filter": show_header_filter,
        "resizable": True,
    } | ag_data_type


def _get_pk_column_defs(de: DataEditor, edit_schema: List[EditSchema], show_header_filter: bool) -> List[dict]:
    ag_pk_cols = []
    for col_name in de.primary_keys:
        col_type: str = de.schema_columns_df.loc[col_name, "type"]  # type: ignore
        col_meaning: str = (
            de.schema_columns_df.loc[col_name, "meaning_id"] if "meaning_id" in de.schema_columns_df.columns else ""
        )  # type: ignore
        col_def = _get_pk_column_def_aggrid(col_name, col_type, col_meaning, show_header_filter, edit_schema)
        ag_pk_cols.append(col_def)
    return ag_pk_cols


def _get_display_column_defs(de: DataEditor, edit_schema: List[EditSchema], show_header_filter: bool) -> List[dict]:
    ag_display_cols = []
    for col_name in de.display_column_names:
        col_type: str = de.schema_columns_df.loc[col_name, "type"]  # type: ignore
        col_meaning: str = (
            de.schema_columns_df.loc[col_name, "meaning"] if "meaning" in de.schema_columns_df.columns else ""
        )  # type: ignore
        col_def = _get_display_column_def_aggrid(col_name, col_type, col_meaning, show_header_filter, edit_schema)
        ag_display_cols.append(col_def)
    return ag_display_cols


def _get_editable_column_defs(
    de: DataEditor, edit_schema: List[EditSchema], show_header_filter: bool, freeze_editable_columns: bool
) -> List[dict]:
    ag_editable_cols = []
    linked_record_names = de.linked_records_df.index.values.tolist()
    editable_column_names = set(de.editable_column_names) - set(linked_record_names)
    for col_name in editable_column_names:
        col_type: str = de.schema_columns_df.loc[col_name, "type"]  # type: ignore
        col_meaning: str = (
            de.schema_columns_df.loc[col_name, "meaning"] if "meaning" in de.schema_columns_df.columns else ""
        )  # type: ignore
        col_def = _get_editable_column_def_aggrid(
            col_name,
            col_type,
            col_meaning,
            show_header_filter,
            freeze_editable_columns,
            edit_schema,
        )
        ag_editable_cols.append(col_def)
    return ag_editable_cols


def _get_linked_record_column_defs(
    de: DataEditor, edit_schema: List[EditSchema], show_header_filter: bool
) -> List[dict]:
    ag_linked_record_cols = []
    if de.linked_records:
        linked_records_df = de.linked_records_df
        linked_record_names = linked_records_df.index.values.tolist()
        for col_name in linked_record_names:
            col_type: str = de.schema_columns_df.loc[col_name, "type"]  # type: ignore
            col_meaning: str = (
                de.schema_columns_df.loc[col_name, "meaning"] if "meaning" in de.schema_columns_df.columns else ""
            )  # type: ignore
            linked_ds_name: str = linked_records_df.loc[col_name, "ds_name"]  # type: ignore
            col_def = _get_linked_record_column_def_aggrid(
                col_name, col_type, col_meaning, linked_ds_name, show_header_filter
            )
            ag_linked_record_cols.append(col_def)
    return ag_linked_record_cols


def _get_extra_column_defs(de: DataEditor, edit_schema: List[EditSchema]) -> List[dict]:
    ag_extra_cols = []
    all_col_names = de.primary_keys + de.display_column_names + de.editable_column_names
    extra_col_defs = set([col.name for col in edit_schema]) - set(all_col_names)
    for extra_col_name in extra_col_defs:
        col_def = next((col.aggrid_col_def for col in edit_schema if col.name == extra_col_name), None)
        if col_def:
            ag_extra_cols.append(col_def)
    return ag_extra_cols


def get_columns_aggrid(
    de: DataEditor, edit_schema: List[EditSchema], show_header_filter=True, freeze_editable_columns=False
) -> List[dict]:
    ag_cols = []

    pk_col_defs = _get_pk_column_defs(de, edit_schema, show_header_filter)
    ag_cols.append({"headerName": "Row identification", "children": pk_col_defs, "marryChildren": True})

    display_col_defs = _get_display_column_defs(de, edit_schema, show_header_filter)
    ag_cols.append({"headerName": "Contextual information", "children": display_col_defs, "marryChildren": True})

    editable_col_defs = _get_editable_column_defs(de, edit_schema, show_header_filter, freeze_editable_columns)
    ag_cols.extend(editable_col_defs)

    linked_record_col_defs = _get_linked_record_column_defs(de, edit_schema, show_header_filter)
    ag_cols.extend(linked_record_col_defs)

    extra_col_defs = _get_extra_column_defs(de, edit_schema)
    ag_cols.extend(extra_col_defs)

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
