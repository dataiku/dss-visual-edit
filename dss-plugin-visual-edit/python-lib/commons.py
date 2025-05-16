from __future__ import annotations
import dataiku
from pandas import DataFrame, concat, pivot_table, options, Int64Dtype
from pandas.api.types import is_integer_dtype, is_float_dtype
from flask import request
import logging


# Editlog utils - used by Empty Editlog step and by DataEditor for initialization of editlog


def write_empty_editlog(editlog_ds):
    cols = [col["name"] for col in editlog_ds.get_config().get("schema").get("columns")]
    editlog_ds.write_dataframe(
        DataFrame(columns=cols),
        infer_schema=False,
    )


# Utils for DataEditor and plugin components (recipes and scenario steps)


# Used by replay_edits method below
def __unpack_keys__(df, new_key_names, old_key_name="key"):
    if len(new_key_names) == 1:
        df.rename(columns={old_key_name: new_key_names[0]}, inplace=True)
    else:
        # 1. Convert key values from strings to tuples
        keys_series = df.apply(lambda row: eval(row[old_key_name]), axis=1)

        # 2. Expand tuples found in keys_series into a dataframe with new_key_names as columns
        #    If no key value was found in the tuple, the dataframe will have a missing value
        #    (Previously we were using result_type="expand", but this fails when
        #     the results of the unpack function are arrays of different lengths)
        keys_df = DataFrame(columns=new_key_names)
        i1 = 0
        for t in keys_series:
            # create a dict `d` that holds, for each of the new keys, the value found in tuple `t` (and nothing if no value is found)
            d = {}
            i2 = 0
            for k in new_key_names:
                if i2 < len(t):
                    # this assumes that keys are in the same order in the tuples coming from the editlog and in new_key_names
                    d[k] = t[i2]
                i2 += 1
            keys_df = concat([keys_df, DataFrame(data=d, index=[i1])])
            i1 += 1

        # 3. Add a column to edits for each key listed in primary_keys
        df[new_key_names] = keys_df

        # 4. Remove the old key column
        df.drop(columns=[old_key_name], inplace=True)

    return df


def get_dataframe(mydataset):
    # Get the dataframe from the dataset, using data types as given by its schema, Int64 for integer columns, and str for boolean columns
    #
    # Note: an alternative would be to use mydataset.get_dataframe(infer_with_pandas=False, bool_as_str=True), but this fails when there are missing values in integer columns.

    # Get the right column types: this would be given by the dataset's schema, except when dealing with integers where we want to enforce the use of Pandas' Int64 type (see https://pandas.pydata.org/pandas-docs/stable/user_guide/integer_na.html).
    myschema = mydataset.read_schema()
    # Get the names, dtypes and parse_date_columns from the schema, with bool_as_str=True to deal with potentially missing boolean values.
    [names, dtypes, parse_date_columns] = dataiku.Dataset.get_dataframe_schema_st(
        myschema, bool_as_str=True
    )
    for col in myschema:
        n = col["name"]
        t = col["type"]
        if n == "validated":
            dtypes[n] = "bool" # we know that there won't be any missing values in the validated column, so we can use the standard bool type
        if t in ["tinyint", "smallint", "int", "bigint"]:
            dtypes[n] = "Int64"

    # Get the dataframe, using iter_dataframes_forced_types to which we can pass our column types. This code was inspired from the example at https://developer.dataiku.com/latest/api-reference/python/datasets.html#dataiku.Dataset.iter_dataframes_forced_types
    mydataset_df = DataFrame({})
    chunksize = 1000
    for df in mydataset.iter_dataframes_forced_types(
        names, dtypes, parse_date_columns, chunksize=chunksize
    ):
        mydataset_df = concat([mydataset_df, df])
    return mydataset_df


# Used by Replay recipe and by DataEditor for getting edited cells
def replay_edits(
    editlog_ds,
    primary_keys,
    editable_column_names,
    validation_column_required = False,
    notes_column_required = False,
):
    """
    Get the edited cells from an editlog dataset.

    :param editlog_ds: the editlog dataset
    :param primary_keys: the primary keys of the dataset
    :param editable_column_names: the editable columns of the dataset
    :param validation_column_required: whether the validation column is required
    :param notes_column_required: whether the notes column is required
    :return: a DataFrame containing only the edited rows and editable columns.
    - The DataFrame will contain the following columns: primary keys, editable columns, feedback columns ("validated" and "notes", if required), metadata columns ("last_edit_date", "last_action", "first_action").
    - When the same cell was edited multiple times, the last edit is kept.
    """

    feedback_columns = []
    validation_column_name = "validated"
    notes_column_name = "notes"
    if validation_column_required:
        feedback_columns.append(validation_column_name)
    if notes_column_required:
        feedback_columns.append(notes_column_name)

    metadata_columns = ["last_edit_date", "last_edited_by", "last_action", "first_action"]

    # Fix expected columns. This helps ensure that the dataframe we return always has the right schema, even if some columns of the input dataset were never edited.
    cols = (
        editable_column_names
        + feedback_columns
        + metadata_columns
    )

    editlog_df = get_dataframe(editlog_ds)
    
    if not editlog_df.size:  # i.e. if empty editlog
        edits_df = DataFrame(columns=(primary_keys + cols))

    else:
        editlog_df.rename(columns={"date": "edit_date", "user": "edited_by"}, inplace=True)
        editlog_df = __unpack_keys__(editlog_df, primary_keys).sort_values("edit_date")

        # Make sure "action" column is present
        if "action" not in editlog_df.columns:
            editlog_df["action"] = "update"

        # Apply edits, i.e. pivot and keep the last value for each column
        edits_df = pivot_table(
            editlog_df,
            index=primary_keys,
            columns="column_name",
            values="value",
            # for each named column, we only keep the last value
            aggfunc=lambda values: values.iloc[-1] if not values.empty else None,
        )

        # Drop any columns from the pivot that may not be one of the expected columns
        for col in edits_df.columns:
            if col not in editable_column_names + feedback_columns:
                logging.warning(
                    f"Column {col} not found in editable columns or feedback columns. Dropping it from the editlog."
                )
                edits_df.drop(columns=[col], inplace=True)

        if notes_column_required:
            # Make sure that there is a notes column
            if notes_column_name not in edits_df.columns:
                edits_df[notes_column_name] = ""
            # Fill its missing values with the default value: empty string
            edits_df[notes_column_name] = edits_df[notes_column_name].fillna("")
            # Make sure that the notes column is string
            edits_df[notes_column_name] = edits_df[notes_column_name].astype(str)

        if validation_column_required:
            # Make sure that there is a validation column
            if validation_column_name not in edits_df.columns:
                edits_df[validation_column_name] = False
            # Fill its missing values with the default value: False
            edits_df[validation_column_name] = edits_df[
                validation_column_name
            ].fillna(False)
            # Make sure that the validation column is boolean
            edits_df[validation_column_name] = edits_df[validation_column_name].astype(bool)

        # create metadata columns
        editlog_grouped_last = (
            editlog_df[primary_keys + ["edit_date", "edited_by", "action"]]
            .groupby(primary_keys)
            .last()
            .add_prefix("last_")
        )
        editlog_grouped_first = (
            editlog_df[primary_keys + ["action"]]
            .groupby(primary_keys)
            .first()
            .add_prefix("first_")
        )
        editlog_grouped_df = editlog_grouped_last.join(
            editlog_grouped_first, on=primary_keys
        )
        edits_df = edits_df.join(editlog_grouped_df, on=primary_keys)

        edits_df = edits_df[cols]

        edits_df.reset_index(inplace=True)

    return edits_df


# Used by DataEditor for init and by get_original_df below
def get_display_column_names(schema, primary_keys, editable_column_names):
    return [
        col.get("name")
        for col in schema
        if col.get("name") not in primary_keys + editable_column_names
    ]


# Used by DataEditor and by apply_edits_from_df method below
def get_original_df(original_ds):
    """
    Get the original dataset as a dataframe
    
    Columns ordered as follows: primary keys, display columns, editable columns, plus validation and notes columns if required (with default values set to empty string and False respectively).

    The dataset's configuration specifies the primary keys, editable columns, and whether validation and notes columns are required. The display columns are all other columns in the dataset.

    :param original_ds: the original dataset
    :return: a tuple containing the original dataframe, the primary keys, display columns and editable columns.
    """

    # Get the original dataset as a dataframe 
    original_df = get_dataframe(original_ds)

    # Read the dataset configuration
    original_ds_config = original_ds.get_config()
    primary_keys = original_ds_config["customFields"]["primary_keys"]
    editable_column_names = [ # filter out column names that are not in the original dataset
        col
        for col in original_ds_config["customFields"]["editable_column_names"]
        if col in original_df.columns
    ]
    validation_column_required = original_ds_config["customFields"]["validation_column_required"]
    notes_column_required = original_ds_config["customFields"]["notes_column_required"]

    # Add the validation and notes columns if required
    feedback_columns = []
    if validation_column_required:
        original_df["validated"] = False
        feedback_columns.append("validated")
    if notes_column_required:
        original_df["notes"] = ""
        feedback_columns.append("notes")

    # Get the display column names
    schema = original_ds_config.get("schema").get("columns")
    display_column_names = get_display_column_names(
        schema, primary_keys, editable_column_names
    )

    # make sure that primary keys will be in the same order for original_df and edits_df, and that we'll return a dataframe where editable columns are last
    return (
        original_df[primary_keys + display_column_names + editable_column_names + feedback_columns],
        primary_keys,
        display_column_names,
        editable_column_names,
    )


# Used by Apply recipe and by DataEditor for getting edited data
def apply_edits_from_df(original_ds, edits_df):
    """
    Get an edited DataFrame from an original dataset and a DataFrame of edits to apply.

    :param original_ds: the original dataset.
    :param edits_df: a DataFrame containing the edits to apply, with columns for primary keys, editable columns, and feedback columns (if any).
    :return: an edited DataFrame containing the original dataset with the edits applied. It will contain the following columns: primary keys, display-only columns, editable columns, feedback columns ("validated" and "notes", if present in the edits DataFrame).
    """

    original_df, primary_keys, display_columns, editable_columns = get_original_df(original_ds)

    metadata_columns = ["last_edit_date", "last_edited_by", "last_action", "first_action"]
    feedback_columns = [] # placeholder for feedback columns found in the edits dataframe
    editable_columns_new = [] # placeholder for columns found in the edits dataframe but not in the original dataset

    if not edits_df.size:  # i.e. if empty editlog
        edited_df = original_df

    else:
        # Prepare edits_df
        ###

        # Change column types to match those of original_df
        for col in edits_df.columns:
            if col in primary_keys + display_columns + editable_columns:
                original_dtype = original_df[col].dtypes.name
                if is_integer_dtype(original_dtype):
                    # there may be missing values so choose a dtype supporting them.
                    # Cast as float first to work around issue with pandas 1.3 https://stackoverflow.com/a/60024263
                    edits_df[col] = edits_df[col].astype(float).astype(Int64Dtype())
                elif is_float_dtype(original_dtype):
                    edits_df[col] = edits_df[col].astype(float)
                else:
                    edits_df[col] = edits_df[col].astype(original_dtype)
            elif col == "validated":
                edits_df[col] = edits_df[col].astype(bool)
                feedback_columns.append(col)
            elif col == "notes":
                edits_df[col] = edits_df[col].astype(str)
                feedback_columns.append(col)
            elif col not in metadata_columns:
                editable_columns_new.append(col)

        # Now that the types are correct (including primary keys), we set the index
        original_df.set_index(primary_keys, inplace=True)
        if not edits_df.index.name:  # if index has no name, i.e. it's a range index
            edits_df.set_index(primary_keys, inplace=True)

        # Identify rows that were deleted or created
        deleted = edits_df["last_action"] == "delete"
        created = edits_df["first_action"] == "create"


        # Apply edits to previously existing rows, i.e. those that were not deleted or created.
        ###

        # For each editable column of the original dataset, a new column with "_value_last" suffix is added. For each row, it holds the last edited value (if any), or None if the column was never edited.
        edited_df = original_df.join(edits_df[~deleted & ~created], rsuffix="_value_last")

        # Merge values of editable columns: if a column was edited, the last value is kept, otherwise the original value is kept.
        for col in editable_columns + feedback_columns:
            # Copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # Replace the value in col: merge values from "_original" and "_value_last" columns
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(
                edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"]
            )
        
        # Fix column types (the join and the "merge" above may have changed the types of some columns)
        for col in editable_columns + feedback_columns:
            edited_df[col] = edited_df[col].astype(original_df[col].dtypes.name)

        # Stack created rows
        ###

        created_df = edits_df[~deleted & created]
        if created_df.size:
            edited_df = concat([created_df, edited_df])

        # Drop the _original and _value_last columns
        edited_df = edited_df[
            display_columns + editable_columns + editable_columns_new + feedback_columns + metadata_columns
        ]

        edited_df.reset_index(inplace=True)

    return edited_df


# Utils for webapp backend


def try_get_user_identifier() -> str | None:
    client = dataiku.api_client()
    # from https://doc.dataiku.com/dss/latest/webapps/security.html#identifying-users-from-within-a-webapp
    # don't use client.get_own_user().get_settings().get_raw() as this would give the user who started the webapp
    user = None
    if request:
        try:
            request_headers = dict(request.headers)
            auth_info_browser = client.get_auth_info_from_browser_headers(
                request_headers
            )
            user = auth_info_browser["authIdentifier"]
        except Exception:
            logging.exception("Failed to get user authentication info.")
    return user


# Used by backend's for CRUD methods


def get_key_values_from_dict(row, primary_keys):
    """
    Get the values of the primary keys from a row, as a tuple.

    Params:
    - row: a dictionary representing a row of a dataset
    - primary_keys: a list of strings representing the primary keys of the dataset

    Example params:
    - row:
    ```
    {
        "key1": "cat",
        "key2": "2022-12-21"
    }
    ```
    - primary_keys: `["key1", "key2"]`

    Example output: `("cat", "2022-12-21")`
    """
    # we create a dataframe containing this single row, set the columns to use as index (i.e. primary key(s)), then get the value of the index for the first (and only) row
    return DataFrame(data=row, index=[0]).set_index(primary_keys).index[0]


# Used by backend to figure out if data is up-to-date


def get_last_build_date(ds_name, project):
    return (
        project.get_dataset(ds_name)
        .get_last_metric_values()
        .get_metric_by_id("reporting:BUILD_START_DATE")
        .get("lastValues")[0]
        .get("computed")
    )
