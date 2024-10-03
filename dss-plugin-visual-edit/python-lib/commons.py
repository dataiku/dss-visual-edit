from __future__ import annotations
import dataiku
from pandas import DataFrame, concat, pivot_table, options, Int64Dtype
from pandas.api.types import is_integer_dtype, is_float_dtype
from flask import request
import logging

feedback_columns = ["validated", "comments"]

metadata_columns = [
    "last_edit_date",
    "last_edited_by",
    "last_action",
    "first_action",
]

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
    [names, dtypes, parse_date_columns] = dataiku.Dataset.get_dataframe_schema_st(
        myschema, bool_as_str=True
    )
    for col in myschema:
        n = col["name"]
        t = col["type"]
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


def replay_edits(editlog_ds, primary_keys, editable_column_names):
    replay_edits_from_df(get_dataframe(editlog_ds), primary_keys, editable_column_names)


def replay_edits_from_df(editlog_df, primary_keys, editable_column_names):

    # Create empty dataframe with the proper edits dataset schema: all primary keys, all editable columns, and "date" column
    # This helps ensure that the dataframe we return always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = primary_keys + editable_column_names + feedback_columns + metadata_columns
    all_columns_df = DataFrame(columns=cols)

    if not editlog_df.size:  # i.e. if empty editlog
        edits_df = all_columns_df
    else:
        editlog_df.rename(columns={"date": "edit_date"}, inplace=True)
        editlog_df = __unpack_keys__(editlog_df, primary_keys).sort_values("edit_date")

        # If "action" is not in the editlog's columns, we add it and set all values to "update"
        if "action" not in editlog_df.columns:
            editlog_df["action"] = "update"

        # Compute comments column for each key
        ###

        editlog_comments = editlog_df[editlog_df["action"] == "comment"]
        editlog_last_comments = (
            editlog_comments[primary_keys + ["value"]]
            .groupby(primary_keys)
            .last()
            .rename(columns={"value": "comments"})
        )

        # remove rows where the "action" column is "comment"
        editlog_df = editlog_df[editlog_df["action"] != "comment"]

        # Compute metadata columns for each key
        ###

        # Last edit date, user, and action
        editlog_grouped_last = (
            editlog_df[primary_keys + ["edit_date", "user", "action"]]
            .groupby(primary_keys)
            .last()
            .add_prefix("last_")
        )
        editlog_grouped_last.rename(
            columns={"last_user": "last_edited_by"}, inplace=True
        )
        # First action
        editlog_grouped_first = (
            editlog_df[primary_keys + ["action"]]
            .groupby(primary_keys)
            .first()
            .add_prefix("first_")
        )
        # Join the two grouped dataframes
        editlog_grouped_df = editlog_grouped_last.join(
            editlog_grouped_first, on=primary_keys
        )

        # Compute the pivot table
        ###

        # On validated rows, copy context to "value" column so that it will be included in the pivot table
        def copy_context(log_entry):
            # based on the values of primary_keys for that log_entry, get the last action
            last_action = editlog_grouped_df.loc[
                get_key_values_as_tuple(log_entry.to_dict(), primary_keys),
                "last_action",
            ]
            if last_action == "validate":
                log_entry["column_name"] = "context"
                log_entry["value"] = log_entry["context"]
            return log_entry

        editlog_df = editlog_df.apply(copy_context, axis=1)

        edits_df = pivot_table(
            editlog_df,
            index=primary_keys,
            columns="column_name",
            values="value",
            # for each named column, we only keep the last value
            aggfunc=lambda values: values.iloc[-1] if not values.empty else None,
        )

        # Unpack context column
        def unpack_context(row):
            if row["context"] == row["context"]:  # checking that it's not NaN
                context = eval(row["context"])
                for k, v in context.items():
                    row[k] = v
            return row

        edits_df = edits_df.apply(unpack_context, axis=1)

        # Drop any columns from the pivot that may not be one of the editable_column_names or the context column
        for col in edits_df.columns:
            if col not in primary_keys + editable_column_names:
                edits_df.drop(columns=[col], inplace=True)

        # Add metadata and comments columns to the pivot table
        ###

        edits_df = edits_df.join(editlog_grouped_df, on=primary_keys).join(
            editlog_last_comments, on=primary_keys
        )

        # Compute the "validated" column (boolean with no missing values)
        edits_df["validated"] = edits_df["last_action"] == "validate"

        edits_df.reset_index(inplace=True)

        # Make sure that all (editable) columns are here and in the right order
        edits_df = concat([all_columns_df, edits_df])

    return edits_df


# Used by get_original_df below and by DataEditor for init
def get_display_column_names(schema, primary_keys, editable_column_names):
    return [
        col.get("name")
        for col in schema
        if col.get("name") not in primary_keys + editable_column_names
    ]


# Used by DataEditor and by apply_edits_from_df method below
def get_original_df(original_ds):
    original_df = get_dataframe(original_ds)

    original_ds_config = original_ds.get_config()
    primary_keys = original_ds_config["customFields"]["primary_keys"]
    editable_column_names = [
        col
        for col in original_ds_config["customFields"]["editable_column_names"]
        if col in original_df.columns
    ]
    schema = original_ds_config.get("schema").get("columns")
    display_column_names = get_display_column_names(
        schema, primary_keys, editable_column_names
    )

    # make sure that primary keys will be in the same order for original_df and edits_df, and that we'll return a dataframe where editable columns are last
    return (
        original_df[primary_keys + display_column_names + editable_column_names],
        primary_keys,
        display_column_names,
        editable_column_names,
    )


# Used by Apply recipe and by DataEditor for getting edited data
def apply_edits_from_df(original_ds, edits_df):
    original_df, primary_keys, display_columns, editable_columns = get_original_df(
        original_ds
    )
    # We create an editable_columns_new variable to store the list of new columns coming from edits dataset but not found in the original dataset's schema
    editable_columns_new = []
    # We create an editable_columns_original variable to store the list of columns that will be used to store the original values of the editable columns
    editable_columns_original = []

    if not edits_df.size:  # i.e. if empty editlog
        edited_df = original_df
    else:
        created = edits_df["first_action"] == "create"
        not_deleted = edits_df["last_action"] != "delete"
        created_df = edits_df[not_deleted & created]

        # Prepare edits_df
        ###
        edits_df = edits_df[not_deleted & ~created]

        # Change types to match those of original_df
        for col in edits_df.columns:
            original_dtype = original_df[col].dtypes.name
            if col in primary_keys + display_columns + editable_columns:
                if is_integer_dtype(original_dtype):
                    # there may be missing values so choose a dtype supporting them.
                    edits_df[col] = edits_df[col].astype(Int64Dtype())
                elif is_float_dtype(original_dtype):
                    edits_df[col] = edits_df[col].astype(float)
                else:
                    edits_df[col] = edits_df[col].astype(original_dtype)
            else:
                editable_columns_new.append(col)

        original_df.set_index(primary_keys, inplace=True)
        if not edits_df.index.name:  # if index has no name, i.e. it's a range index
            edits_df.set_index(primary_keys, inplace=True)

        # Join and "Merge"
        ###

        # Join -> this adds _value_last columns
        edited_df = original_df.join(edits_df, rsuffix="_value_last")

        # "Merge" -> this creates _original columns
        # all last_ and first_ columns have already been dropped
        for col in editable_columns:
            col_value_last = col + "_value_last"
            # col_value_last already has values, due to the join

            col_original = col + "_original"
            # when col_value_last is not null, we want col_original to have the value in col; otherwise we want an empty value
            edited_df[col_original] = edited_df[col].where(
                edited_df[col_value_last].notnull(), None
            )

            # when col_value_last is not null, we also want col to have the value in col_value_last
            edited_df[col] = edited_df[col_value_last].where(
                edited_df[col_value_last].notnull(), edited_df[col]
            )

            # add col_original to the list of columns used to store editable columns' original values
            editable_columns_original.append(col_original)

        edited_df.reset_index(inplace=True)

        # Stack created rows
        ###

        if created_df.size:
            edited_df = concat([created_df, edited_df])

        # Drop the _value_last columns
        edited_df = edited_df[
            primary_keys
            + display_columns
            + editable_columns
            + editable_columns_new
            + editable_columns_original
            + feedback_columns
            + metadata_columns
        ]

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


def get_key_values_as_tuple(row: dict, primary_keys):
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
