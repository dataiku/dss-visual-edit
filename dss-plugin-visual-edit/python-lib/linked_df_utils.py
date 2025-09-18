from typing import Union
from pandas import DataFrame, concat
from dataiku_utils import get_dataframe_filtered


def get_linked_dataframe_filtered(linked_record, project_key, filter_term, n_results):
    """Return a DataFrame of rows from the linked dataset filtered by a term.

    This helper handles two cases:
    - The linked dataset is a Dataiku-managed dataset (accessed via ``linked_record.ds``):
      in that case the call delegates to ``dataiku_utils.get_dataframe_filtered`` so
      server-side filtering / paging can be used for SQL-backed datasets.
    - The linked dataset is already loaded in memory on the backend (``linked_record.df``):
      the function applies a pandas prefix filter on the configured label column.

    Parameters
    - linked_record: LinkedRecord-like object containing ``ds``, ``ds_name``,
      ``ds_label`` and (when in-memory) ``df`` attributes.
    - project_key: str, Dataiku project key used when requesting a managed dataset.
    - filter_term: str, prefix term used to filter the label column (case-insensitive).
    - n_results: int, maximum number of rows to return.

    Returns
    - pandas.DataFrame of matching rows _not indexed_ by the linked dataset's key, or a (message, status) tuple on error.
    """

    linked_ds_label = linked_record.ds_label
    if linked_record.ds:
        # The linked dataset is SQL-based; we use the Dataiku API to filter it (but we could also use a SQL query)
        linked_ds_name = linked_record.ds_name
        linked_df_filtered = get_dataframe_filtered(
            ds_name=linked_ds_name,
            project_key=project_key,
            filter_column=linked_ds_label,
            filter_term=filter_term,
            n_results=n_results,
        )
    else:
        # The linked dataframe is already available in memory (and capped to 1000 rows); it can be filtered by Pandas
        # This dataframe is indexed by the linked dataset's key column: we reset the index to stay consistent with the rest of this method
        if linked_record.df is None:
            return "Something went wrong. Try restarting the backend.", 500
        linked_df = linked_record.df.reset_index()
        if filter_term == "":
            linked_df_filtered = linked_df.head(n_results)
        else:
            # Filter linked_df for rows whose label starts with the search term
            linked_df_filtered = linked_df[
                linked_df[linked_ds_label].str.lower().str.startswith(filter_term)
            ].head(n_results)
    return linked_df_filtered


def get_linked_label(linked_record, key):
    """Return the display label for a linked-record key.

    If a `ds_label` is configured and differs from the key column, this function
    attempts to retrieve the corresponding label value from the linked dataset.
    It supports both managed datasets (`linked_record.ds`) and in-memory dataframes
    (`linked_record.df`). If no label column is defined, the `key` is returned as-is.

    Parameters
    - linked_record: LinkedRecord-like object with `ds`, `ds_key`,
      `ds_label` and optionally `df` attributes.
    - key: scalar key value (string). If an empty string is provided, the function
      returns the empty string.

    Returns
    - label string on success, or a (message, status) tuple on error.
    """
    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label
    # Return label only if a label column is defined (and different from the key column)
    if key != "" and linked_ds_label and linked_ds_label != linked_ds_key:
        if linked_record.ds:
            try:
                label = linked_record.ds.get_cell_value_sql_query(
                    linked_ds_key, key, linked_ds_label
                )
            except Exception:
                return "Something went wrong fetching label of linked value.", 500
        else:
            linked_df = linked_record.df
            if linked_df is None:
                return "Something went wrong. Try restarting the backend.", 500
            try:
                label = linked_df.loc[key, linked_ds_label]
            except Exception:
                return label
    else:
        label = key
    return label


def get_linked_options(linked_record, term, key):
    """Return a list of formatted dropdown options for a linked record.

    The returned structure is intended for the frontend: either a list of key
    strings (when no label/lookup columns are configured) or a list of dictionaries
    with `value`, `label` and optional lookup fields. The function applies
    server- or client-side filtering using `get_linked_dataframe_filtered` and
    guarantees that the currently-selected `key` is present in the results when
    possible.

    Parameters
    - linked_record: LinkedRecord-like object with `ds`, `ds_key`,
      `ds_label`, `ds_lookup_columns` and `df` (when in-memory) attributes.
    - term: str, the search term entered by the user (prefix match).
    - key: str, the current value of the edited cell; used to ensure the current
      value is present in the options list.

    Returns
    - A list suitable for the frontend picker (list[str] or list[dict]).
    """
    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label
    linked_ds_lookup_columns = linked_record.ds_lookup_columns

    if term != "":
        # when a search term is provided, show a limited number of options matching this term
        n_options = 10
    else:
        # otherwise, show many options to choose from
        n_options = 1000

    # Get a dataframe of the linked dataset filtered by the search term or the key
    linked_df_filtered = get_linked_dataframe_filtered(
        linked_record=linked_record,
        project_key=project_key,
        filter_term=term,
        n_results=n_options,
    )

    # when a key is provided, make sure to include an option corresponding to this key
    # if not already the case, get the label for this key and use it as search term to filter the linked dataframe
    # this ensures that when editing a linked record, the current value is always present in the dropdown list of options
    # note that this could result in more than 1 option being returned (if several rows of the linked dataset share the same label), but we cap to n_options
    if key != "" and key != "null":
        linked_label_rows = linked_df_filtered[linked_df_filtered[linked_ds_key] == key]
        if linked_label_rows.empty:
            label = get_linked_label(linked_record, key).lower()
            linked_label_rows = get_linked_dataframe_filtered(
                linked_record=linked_record,
                project_key=project_key,
                filter_term=label,
                n_results=n_options,
            )
            linked_df_filtered = concat([linked_label_rows, linked_df_filtered])

    editor_values_param = get_formatted_items_from_linked_df(
        linked_df=linked_df_filtered,
        key_col=linked_ds_key,
        label_col=linked_ds_label,
        lookup_cols=linked_ds_lookup_columns,
    )

    return editor_values_param


def get_formatted_items_from_linked_df(
    linked_df: DataFrame,
    key_col: str,
    label_col: str,
    lookup_cols: Union[list, None] = None,
) -> list:
    """
    Get values of specified columns in the dataframe of a linked dataset, to be read by Dash Tabulator's `listItemFormatter`.

    - If no label column and no lookup columns are specified, the return value is a sorted list of key column values.
    - Otherwise, the return value is a list of dicts sorted by label.

    Example params:
    - linked_df: the indexed dataframe of a linked dataset
    - key_col: "id"
    - label_col: "name"
    - lookup_cols: ["col1", "col2"]

    Example return value:

    If no label and lookup columns are specified, then the return value is:
    ```
    ["0f45e", "c3d2a"]
    ```

    If a label column is specified but no lookup columns, then the return value is:
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

    If label and lookup columns are specified, then the return value is:
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
