from __future__ import annotations
import dataiku
from pandas import DataFrame, concat, pivot_table, options
from flask import request
import logging


# Editlog utils - used by Empty Editlog step and by EES for initialization of editlog


def write_empty_editlog(editlog_ds):
    cols = [col["name"] for col in editlog_ds.get_config().get("schema").get("columns")]
    editlog_ds.write_dataframe(
        DataFrame(columns=cols),
        infer_schema=False,
    )


# Utils for EES and plugin components (recipes and scenario steps)


# Used by pivot_editlog method below
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

        # 3. Add a column to editlog_pivoted for each key listed in primary_keys
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
        myschema, bool_as_str=True, int_as_float=False
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


# Used by Pivot recipe and by EES for getting edited cells


def pivot_editlog(editlog_ds, primary_keys, editable_column_names):
    # Create empty dataframe with the proper editlog pivoted schema: all primary keys, all editable columns, and "date" column
    # This helps ensure that the dataframe we return always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = (
        primary_keys
        + editable_column_names
        + ["last_edit_date", "last_action", "first_action"]
    )
    all_columns_df = DataFrame(columns=cols)

    editlog_df = get_dataframe(editlog_ds)
    if not editlog_df.size:  # i.e. if empty editlog
        editlog_pivoted_df = all_columns_df
    else:
        editlog_df.rename(columns={"date": "edit_date"}, inplace=True)
        editlog_df = __unpack_keys__(editlog_df, primary_keys).sort_values("edit_date")

        # if "action" is not in the editlog's columns, we add it and set all values to "update"
        if "action" not in editlog_df.columns:
            editlog_df["action"] = "update"

        # for each key, compute last edit date, last action and first action
        editlog_grouped_last = (
            editlog_df[primary_keys + ["edit_date", "action"]]
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

        editlog_pivoted_df = pivot_table(
            editlog_df,
            index=primary_keys,
            columns="column_name",
            values="value",
            # for each named column, we only keep the last value
            aggfunc=lambda values: values.iloc[-1] if not values.empty else None,
        ).join(editlog_grouped_df, on=primary_keys)

        # Drop any columns from the pivot that may not be one of the editable_column_names
        for col in editlog_pivoted_df.columns:
            if not col in cols:
                editlog_pivoted_df.drop(columns=[col], inplace=True)

        editlog_pivoted_df.reset_index(inplace=True)
        # this makes sure that all (editable) columns are here and in the right order
        editlog_pivoted_df = concat([all_columns_df, editlog_pivoted_df])

    return editlog_pivoted_df


# Used by get_original_df below and by EES for init
def get_display_column_names(schema, primary_keys, editable_column_names):
    return [
        col.get("name")
        for col in schema
        if col.get("name") not in primary_keys + editable_column_names
    ]


# Used by EES and by merge_edits_from_log_pivoted_df method below
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

    # make sure that primary keys will be in the same order for original_df and editlog_pivoted_df, and that we'll return a dataframe where editable columns are last
    return (
        original_df[primary_keys + display_column_names + editable_column_names],
        primary_keys,
        display_column_names,
        editable_column_names,
    )


# Used by Merge recipe and by EES for getting edited data
def merge_edits_from_log_pivoted_df(original_ds, editlog_pivoted_df):
    original_df, primary_keys, display_columns, editable_columns = get_original_df(
        original_ds
    )
    # this will contain the list of new columns coming from editlog pivoted but not found in the original dataset's schema
    editable_columns_new = []

    if not editlog_pivoted_df.size:  # i.e. if empty editlog
        edited_df = original_df
    else:
        created = editlog_pivoted_df["first_action"] == "create"
        not_deleted = editlog_pivoted_df["last_action"] != "delete"
        created_df = editlog_pivoted_df[not_deleted & created]

        # Prepare editlog_pivoted_df
        ###
        editlog_pivoted_df = editlog_pivoted_df[not_deleted & ~created]

        # Drop columns which are not primary keys nor editable columns
        options.mode.chained_assignment = None  # this helps prevent SettingWithCopyWarnings that are triggered by the drops below
        if "last_edit_date" in editlog_pivoted_df.columns:
            editlog_pivoted_df.drop(columns=["last_edit_date"], inplace=True)
        if "last_action" in editlog_pivoted_df.columns:
            editlog_pivoted_df.drop(columns=["last_action"], inplace=True)
        if "first_action" in editlog_pivoted_df.columns:
            editlog_pivoted_df.drop(columns=["first_action"], inplace=True)

        # Change types to match those of original_df
        for col in editlog_pivoted_df.columns:
            if col in primary_keys + display_columns + editable_columns:
                if original_df[col].dtypes.name == "Int64":
                    editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(float)
                editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(
                    original_df[col].dtypes.name
                )
            else:
                editable_columns_new.append(col)

        original_df.set_index(primary_keys, inplace=True)
        if (
            not editlog_pivoted_df.index.name
        ):  # if index has no name, i.e. it's a range index
            editlog_pivoted_df.set_index(primary_keys, inplace=True)

        # "Replay" edits: Join and Merge
        ###

        # Join -> this adds _value_last columns
        edited_df = original_df.join(editlog_pivoted_df, rsuffix="_value_last")

        # "Merge" -> this creates _original columns
        # all last_ and first_ columns have already been dropped
        for col in editable_columns:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(
                edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"]
            )

        edited_df.reset_index(inplace=True)

        # Stack created rows
        ###

        if created_df.size:
            edited_df = concat([created_df, edited_df])

        # Drop the _original and _value_last columns
        edited_df = edited_df[
            primary_keys + display_columns + editable_columns + editable_columns_new
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


# Used by backend for the edit callback
def get_user_identifier():
    user = try_get_user_identifier()
    return "unknown" if user is None else user


# Used by backend's for CRUD methods


def get_key_values_from_dict(row, primary_keys):
    """
    Get values for a given row provided as a dict and a list of primary key column names

    Example params:
    - row:
    ```
    {
        "key1": "cat",
        "key2": "2022-12-21"
    }
    ```
    - primary_keys: `["key1", "key2"]`
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
