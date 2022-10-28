import dataiku
from pandas import DataFrame, concat, pivot_table
from json5 import loads
from os import getenv
import requests
from flask import request
import logging


# Editlog utils

def get_editlog_ds_schema():
    return [
        # not using date type, in case the editlog is CSV
        {"name": "date", "type": "string", "meaning": "DateSource"},
        {"name": "user", "type": "string", "meaning": "Text"},
        {"name": "key", "type": "string", "meaning": "Text"},
        {"name": "column_name", "type": "string", "meaning": "Text"},
        {"name": "value", "type": "string", "meaning": "Text"}
    ]


def get_editlog_columns():
    return ["date", "user", "key", "column_name", "value"]


def get_editlog_df(editlog_ds):
    # Try to get dataframe from editlog dataset, if it's not empty. Otherwise, create empty dataframe.
    try:
        editlog_df = editlog_ds.get_dataframe(infer_with_pandas=False, bool_as_str=True) # the schema was specified upon creation of the dataset, so let's use it
    except:
        print("Editlog is empty. Writing schema and empty dataframe...")
        editlog_df = DataFrame(columns=get_editlog_columns())
        editlog_ds.write_schema(get_editlog_ds_schema())
        editlog_ds.write_dataframe(editlog_df, infer_schema=False)
        print("Done.")
    return editlog_df


def get_editlog_pivoted_ds_schema(original_schema, primary_keys, editable_column_names):
    editlog_pivoted_ds_schema = []
    edited_ds_schema = []
    for col in original_schema:
        new_col = {}
        new_col["name"] = col.get("name")
        type = col.get("type")
        if (type):
            new_col["type"] = type
        meaning = col.get("meaning")
        if (meaning):
            new_col["meaning"] = meaning
        edited_ds_schema.append(new_col)
        if (col.get("name") in primary_keys + editable_column_names):
            editlog_pivoted_ds_schema.append(new_col)
    editlog_pivoted_ds_schema.append(
        {"name": "last_edit_date", "type": "string", "meaning": "DateSource"})
    return editlog_pivoted_ds_schema, edited_ds_schema


# Recipe utils


def get_primary_keys(schema):
    keys = []
    for col in schema:
        if col.get("editable_type") == "key":
            keys.append(col["name"])
    return keys


def get_display_column_names(schema, primary_keys, editable_column_names):
    return [col.get("name") for col in schema if col.get("name") not in primary_keys + editable_column_names]


def get_editable_column_names(schema):
    editable_column_names = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
    return editable_column_names


def unpack_keys(df, new_key_names, old_key_name="key"):
    if (len(new_key_names) == 1):
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


def pivot_editlog(editlog_ds, primary_keys, editable_column_names):

    # Create empty dataframe with the proper editlog pivoted schema: all primary keys, all editable columns, and "date" column
    # This helps ensure that the dataframe we return always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = primary_keys + editable_column_names + ["last_edit_date"]
    all_columns_df = DataFrame(columns=cols)

    editlog_df = get_editlog_df(editlog_ds)
    if (not editlog_df.size):  # i.e. if empty editlog
        editlog_pivoted_df = all_columns_df
    else:
        editlog_df.rename(columns={"date": "last_edit_date"}, inplace=True)
        editlog_df = unpack_keys(editlog_df, primary_keys)
        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("last_edit_date"),  # ordering by edit date
            index=primary_keys,
            columns="column_name",
            values="value",
            # for each named column, we only keep the last value
            aggfunc=lambda values: values.iloc[-1] if not values.empty else None
        ).join(
            # join the last edit date for each key
            editlog_df[primary_keys + ["last_edit_date"]
                       ].groupby(primary_keys).last(),
            on=primary_keys
        )
        # Drop any columns from the pivot that may not be one of the editable_column_names
        for col in editlog_pivoted_df.columns:
            if not col in cols:
                editlog_pivoted_df.drop(columns=[col], inplace=True)

        editlog_pivoted_df.reset_index(inplace=True)
        # this makes sure that all (editable) columns are here and in the right order
        editlog_pivoted_df = concat([all_columns_df, editlog_pivoted_df])

    return editlog_pivoted_df

def get_original_df(original_ds):

    try:
        original_df = original_ds.get_dataframe(infer_with_pandas=False, bool_as_str=True) # the dataset schema is likely to have been reviewed by the end-user, so let's use it!
    except:
        logging.warning("""Couldn't use the original dataset's schema when loading its contents as a dataframe. Letting Pandas infer the schema.
        
        This is likely due to a column with missing values and 'int' storage type; this can be fixed by changing its storage type to 'string'.""")
        original_df = original_ds.get_dataframe()

    original_ds_config = original_ds.get_config()
    primary_keys = original_ds_config["customFields"]["primary_keys"]
    editable_column_names = original_ds_config["customFields"]["editable_column_names"]
    schema = original_ds_config.get("schema").get("columns")
    display_column_names = get_display_column_names(schema, primary_keys, editable_column_names)
    
    # make sure that primary keys will be in the same order for original_df and editlog_pivoted_df, and that we'll return a dataframe where editable columns are last
    return original_df[primary_keys + display_column_names + editable_column_names], primary_keys

def update_df_with_edits(df, edits_df, primary_keys, join="left"):
    """
    Update values of `df` with those found in `edits_df`.

    Exception: If a value was edited to NA but wasn't NA in the input dataset, the original value will be kept. This is similar to the behaviour of pandas' DataFrame.update(). 

    Parameters:

    - df (DataFrame) : Input dataset.
    - edits_df (DataFrame) : Contains edited values. Columns must be a subset of `df`'s columns.
    - primary_keys (list) : Names of columns that act as (multi-)index in `df` _and_ in `edits_df`.
    - join ({"left", "outer"}, default "left"): How to combine the two DataFrames...

       - left: use `df`'s index (this makes sense when `edits_df` is a subset of `df`)
       - outer: union of `df`'s index and `edits_df`'s index

    Returns:
    DataFrame: Edited dataset
    """

    if (not edits_df.size):
        edited_df = df

    else:

        # Align types of editable columns in editlog_pivoted_df on those of original_df
        if ("last_edit_date" in edits_df.columns):
            edits_df.drop(columns=["last_edit_date"], inplace=True)
        editable_column_names = edits_df.columns.tolist()
        for col in editable_column_names:
            edits_df[col] = edits_df[col].astype(
                     df[col].dtypes.name)

        # Join
        # Note: this adds "_value_last" columns
        df.set_index(primary_keys, inplace=True)
        edits_df.set_index(primary_keys, inplace=True)
        edited_df = df.join(
            edits_df, rsuffix="_value_last", how=join)

        # Update values in editable columns
        # - Copy original values to "_original" columns
        # - Replace values with those coming from "_value_last" columns (when they exist)
        for col in editable_column_names:
            edited_df[col + "_original"] = edited_df[col]
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(
                edited_df[col + "_value_last"].notnull(), # where this is True, keep the original value; where False, replace with corresponding value from "other" (defined below)
                other=edited_df[col + "_original"])

        # Drop the "_original" and "_value_last" columns -> this gets us back to the original schema
        edited_df = edited_df[edited_df.columns[:-2 *
                                                len(editable_column_names)]].reset_index()

    return edited_df


def update_ds_with_edits(ds, edits_df):
    original_df, primary_keys = get_original_df(ds)
    return update_df_with_edits(original_df, edits_df, primary_keys)


# Other utils

def get_user_details():
    client = dataiku.api_client()
    # from https://doc.dataiku.com/dss/latest/webapps/security.html#identifying-users-from-within-a-webapp
    # don't use client.get_own_user().get_settings().get_raw() as this would give the user who started the webapp
    request_headers = dict(request.headers)
    auth_info_browser = client.get_auth_info_from_browser_headers(
        request_headers)
    return auth_info_browser["authIdentifier"]


def tabulator_row_key_values(row, primary_keys):
    """Get values for a given row coming from Tabulator and a list of columns that are primary keys"""
    return DataFrame(data=row, index=[0]).set_index(primary_keys).index[0]


def get_last_build_date(ds_name, project):
    return project.get_dataset(ds_name).get_last_metric_values().get_metric_by_id("reporting:BUILD_START_DATE").get("lastValues")[0].get("computed")


def get_values_from_linked_df(linked_df, linked_ds_key, linked_ds_label, linked_ds_lookup_columns):
    linked_columns = [linked_ds_key]
    if (linked_ds_label != linked_ds_key):
        linked_columns += [linked_ds_label]
    if linked_ds_lookup_columns != []:
        linked_columns += linked_ds_lookup_columns
    values_df = linked_df[linked_columns].sort_values(linked_ds_label)
    if len(linked_columns) == 1:
        return values_df[linked_columns[0]].to_list()
    else:
        return values_df[linked_columns].rename(
            columns={linked_ds_key: "value", linked_ds_label: "label"}).to_dict("records")

# Other utils (unused)


def get_table_name(dataset, project_key):
    return dataset.get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", dataiku.get_custom_variables().get("NODE"))


def call_rest_api(path):
    PORT = dataiku.base.remoterun.get_env_var("DKU_BASE_PORT")
    if (PORT == None):
        PORT = "11200"
    BASE_API_URL = "http://127.0.0.1:" + PORT + \
        "/public/api/projects/" + getenv("DKU_CURRENT_PROJECT_KEY")
    return loads(
        requests.get(
            url=BASE_API_URL + path,
            headers=dataiku.core.intercom.get_auth_headers(),
            verify=False
        ).text)


def get_webapp_json(webapp_ID):
    return call_rest_api("/webapps/" + webapp_ID)


def find_webapp_id(original_ds_name):
    from pandas import DataFrame
    webapps_df = DataFrame(call_rest_api("/webapps/"))
    webapps_edit_df = webapps_df[webapps_df["type"] ==
                                 "webapp_editable-via-webapp_edit-dataset-records"]
    webapps_edit_df["original_ds_name"] = webapps_edit_df.apply(
        lambda row: get_webapp_json(row["id"]).get(
            "config").get("original_dataset"),
        axis=1)
    return webapps_edit_df[webapps_edit_df["original_ds_name"] == original_ds_name].iloc[0]["id"]
