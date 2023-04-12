import dataiku
from pandas import DataFrame, concat, pivot_table
from json import loads
from os import getenv
import requests
from flask import request
import logging


# Editlog utils

# Used by EES for initialization of editlog
# TODO: move to EES
def get_editlog_ds_schema():
    return [
        # not using date type, in case the editlog is CSV
        {"name": "date", "type": "string", "meaning": "DateSource"},
        {"name": "user", "type": "string", "meaning": "Text"},
        # action can be "update", "create", or "delete"; currently it's ignored by the pivot method
        {"name": "action", "type": "string", "meaning": "Text"},
        {"name": "key", "type": "string", "meaning": "Text"},
        {"name": "column_name", "type": "string", "meaning": "Text"},
        {"name": "value", "type": "string", "meaning": "Text"}
    ]

# Used by write_empty_editlog method below
def __get_editlog_columns__():
    return ["date", "user", "action", "key", "column_name", "value"]

# Used by Empty Editlog step and by EES for initialization of editlog
def write_empty_editlog(editlog_ds):
    editlog_ds.write_dataframe(DataFrame(columns=__get_editlog_columns__()), infer_schema=False)


# Utils for EES and plugin components (recipes and scenario steps)

# Used by pivot_editlog method below
def __unpack_keys__(df, new_key_names, old_key_name="key"):
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

# Used by pivot_editlog method below, and by EES when checking for status of editlog 
def get_editlog_df(editlog_ds):
    # the schema was specified upon creation of the dataset, so let's use it
    return editlog_ds.get_dataframe(infer_with_pandas=False, bool_as_str=True)

# Used by Pivot recipe and by EES for getting edited cells
def pivot_editlog(editlog_ds, primary_keys, editable_column_names):

    # Create empty dataframe with the proper editlog pivoted schema: all primary keys, all editable columns, and "date" column
    # This helps ensure that the dataframe we return always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = primary_keys + editable_column_names + ["last_edit_date", "last_action", "first_action"]
    all_columns_df = DataFrame(columns=cols)

    editlog_df = get_editlog_df(editlog_ds)
    if (not editlog_df.size): # i.e. if empty editlog
        editlog_pivoted_df = all_columns_df
    else:
        editlog_df.rename(
            columns={"date": "edit_date"},
            inplace=True)
        editlog_df = __unpack_keys__(editlog_df, primary_keys)

        # for each key, compute last edit date, last action and first action
        editlog_grouped_last = editlog_df[primary_keys + ["edit_date", "action"]
                       ].groupby(primary_keys).last().add_prefix("last_")
        editlog_grouped_first = editlog_df[primary_keys + ["action"]
                       ].groupby(primary_keys).first().add_prefix("first_")
        editlog_grouped_df = editlog_grouped_last.join(editlog_grouped_first, on=primary_keys)

        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("edit_date"),  # ordering by edit date
            index=primary_keys,
            columns="column_name",
            values="value",
            # for each named column, we only keep the last value
            aggfunc=lambda values: values.iloc[-1] if not values.empty else None
        ).join(
            editlog_grouped_df,
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

# Used by get_original_df below and by EES for init
def get_display_column_names(schema, primary_keys, editable_column_names):
    return [col.get("name") for col in schema if col.get("name") not in primary_keys + editable_column_names]

# Used by merge_edits_from_log_pivoted_df method below
def __get_original_df__(original_ds):

    try:
        original_df = original_ds.get_dataframe(infer_with_pandas=False, bool_as_str=True) # the dataset schema is likely to have been reviewed by the end-user, so let's use it!
    except:
        logging.warning("""Couldn't use the original dataset's schema when loading its contents as a dataframe. Letting Pandas infer the schema.
        
        This is likely due to a column with missing values and 'int' storage type; this can be fixed by changing its storage type to 'string'.""")
        original_df = original_ds.get_dataframe()

    original_ds_config = original_ds.get_config()
    primary_keys = original_ds_config["customFields"]["primary_keys"]
    editable_column_names = [col for col in original_ds_config["customFields"]["editable_column_names"] if col in original_df.columns]
    schema = original_ds_config.get("schema").get("columns")
    display_column_names = get_display_column_names(schema, primary_keys, editable_column_names)
    
    # make sure that primary keys will be in the same order for original_df and editlog_pivoted_df, and that we'll return a dataframe where editable columns are last
    return original_df[primary_keys + display_column_names + editable_column_names], primary_keys, display_column_names, editable_column_names


# Used by Merge recipe and by EES for getting edited data
def merge_edits_from_log_pivoted_df(original_ds, editlog_pivoted_df):
    original_df, primary_keys, display_columns, editable_columns = __get_original_df__(original_ds)
    editable_columns_new = [] # this will contain the list of new columns coming from editlog pivoted but not found in the original dataset's schema

    if (not editlog_pivoted_df.size):  # i.e. if empty editlog
        edited_df = original_df
    else:

        created = editlog_pivoted_df["first_action"]=="create"
        created_df = editlog_pivoted_df[created]


        # Prepare editlog_pivoted_df
        ###

        not_deleted = editlog_pivoted_df["last_action"]!="delete"
        editlog_pivoted_df = editlog_pivoted_df[not_deleted & ~created]

        # Drop columns which are not primary keys nor editable columns
        if ("last_edit_date" in editlog_pivoted_df.columns):
            editlog_pivoted_df.drop(columns=["last_edit_date"], inplace=True)
        if ("last_action" in editlog_pivoted_df.columns):
            editlog_pivoted_df.drop(columns=["last_action"], inplace=True)
        if ("first_action" in editlog_pivoted_df.columns):
            editlog_pivoted_df.drop(columns=["first_action"], inplace=True)

        # Change types to match those of original_df
        for col in editlog_pivoted_df.columns:
            if col in primary_keys + display_columns + editable_columns:
                editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(
                     original_df[col].dtypes.name)
            else:
                editable_columns_new.append(col)

        original_df.set_index(primary_keys, inplace=True)
        if (not editlog_pivoted_df.index.name): # if index has no name, i.e. it's a range index
            editlog_pivoted_df.set_index(primary_keys, inplace=True)


        # "Replay" edits: Join and Merge
        ###

        # Join -> this adds _value_last columns
        edited_df = original_df.join(
            editlog_pivoted_df, rsuffix="_value_last")

        # "Merge" -> this creates _original columns
        # all last_ and first_ columns have already been dropped
        for col in editable_columns:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(
                edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"])

        edited_df.reset_index(inplace=True)


        # Stack created rows
        ###

        if (created_df.size):
            edited_df = concat([created_df, edited_df])

        # Drop the _original and _value_last columns
        edited_df = edited_df[primary_keys + display_columns + editable_columns + editable_columns_new]

    return edited_df



# Utils for webapp backend

# Used by backend for the edit callback
def get_user_details():
    client = dataiku.api_client()
    # from https://doc.dataiku.com/dss/latest/webapps/security.html#identifying-users-from-within-a-webapp
    # don't use client.get_own_user().get_settings().get_raw() as this would give the user who started the webapp
    request_headers = dict(request.headers)
    auth_info_browser = client.get_auth_info_from_browser_headers(
        request_headers)
    return auth_info_browser["authIdentifier"]

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
    return project.get_dataset(ds_name).get_last_metric_values().get_metric_by_id("reporting:BUILD_START_DATE").get("lastValues")[0].get("computed")

# Used by backend's lookup endpoint and by EES (when linked dataframe can be loaded in memory and provided in the Tabulator column settings)
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

# Utils for EES

def get_editable_column_names(schema):
    editable_column_names = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
    return editable_column_names

def get_primary_keys(schema):
    keys = []
    for col in schema:
        if col.get("editable_type") == "key":
            keys.append(col["name"])
    return keys

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
