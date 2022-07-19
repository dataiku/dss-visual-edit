import dataiku
from pandas import DataFrame, concat, pivot_table
from json5 import loads
from os import getenv
import requests
from flask import request


### Editlog utils

def get_editlog_ds_schema():
    return [
        {"name": "date", "type": "string", "meaning": "DateSource"}, # not using date type, in case the editlog is CSV
        {"name": "user", "type": "string", "meaning": "Text"},
        {"name": "key", "type": "string"},
        {"name": "column_name", "type": "string", "meaning": "Text"},
        {"name": "value", "type": "string"}
    ]

def get_editlog_columns():
    return ["date", "user", "key", "column_name", "value"]

def get_editlog_df(editlog_ds):
    # Try to get dataframe from editlog dataset, if it's not empty. Otherwise, create empty dataframe.
    try:
        editlog_df = editlog_ds.get_dataframe()
    except:
        print("Editlog is empty. Writing schema and empty dataframe...")
        editlog_df = DataFrame(columns=get_editlog_columns())
        editlog_ds.write_schema(get_editlog_ds_schema())
        editlog_ds.write_dataframe(editlog_df)
        print("Done.")
    return editlog_df

### Recipe utils

def get_primary_keys(schema):
    keys = []
    for col in schema:
        if col.get("editable_type")=="key":
            keys.append(col["name"])
    return keys

def get_display_column_names(editschema):
    display_column_names = []
    for col in editschema:
        if not col.get("editable") and col.get("editable_type")!="key":
            display_column_names.append(col.get("name"))
    return display_column_names

def get_editable_column_names(schema):
    editable_column_names = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
    return editable_column_names

def unpack_keys(df, new_key_names, old_key_name="key"):
    if (len(new_key_names)==1):
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
                    d[k] = t[i2] # this assumes that keys are in the same order in the tuples coming from the editlog and in new_key_names
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
    if (not editlog_df.size): # i.e. if empty editlog
        editlog_pivoted_df = all_columns_df
    else:
        editlog_df.rename(columns={"date": "last_edit_date"}, inplace=True)
        editlog_df = unpack_keys(editlog_df, primary_keys)
        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("last_edit_date"), # ordering by edit date
            index=primary_keys,
            columns="column_name",
            values="value",
            aggfunc="last" # for each named column, we only keep the last value
        ).join(
            editlog_df[primary_keys + ["last_edit_date"]].groupby(primary_keys).last(), # join the last edit date for each key
            on=primary_keys
        )
        # Drop any columns from the pivot that may not be one of the editable_column_names
        for col in editlog_pivoted_df.columns:
            if not col in cols:
                editlog_pivoted_df.drop(columns=[col], inplace=True)

        editlog_pivoted_df.reset_index(inplace=True)
        editlog_pivoted_df = concat([all_columns_df, editlog_pivoted_df]) # this makes sure that all (editable) columns are here and in the right order

    return editlog_pivoted_df

def merge_edits(original_df, editlog_pivoted_df, primary_keys):
    if (not editlog_pivoted_df.size): # i.e. if empty editlog
        edited_df = original_df
    else:
        # We don't need the date column in the rest
        editlog_pivoted_df.drop(columns=["last_edit_date"], inplace=True)

        # Change types of primary keys to match original_df
        for col in primary_keys: # or editlog_pivoted_df.columns.tolist() ?
            editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(original_df[col].dtypes.name)

        # Join -> this adds _value_last columns
        original_df.set_index(primary_keys, inplace=True)
        editlog_pivoted_df.set_index(primary_keys, inplace=True)
        edited_df = original_df.join(editlog_pivoted_df, on=primary_keys, rsuffix="_value_last")
        
        # "Merge" -> this creates _original columns
        editable_column_names = editlog_pivoted_df.columns.tolist() # "last_edit_date" column has already been dropped
        for col in editable_column_names:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"])

        # Drop the _original and _value_last columns -> this gets us back to the original schema
        edited_df = edited_df[edited_df.columns[:-2*len(editable_column_names)]].reset_index()

    return edited_df

### Other utils

def get_user_details():
    client = dataiku.api_client()
    # from https://doc.dataiku.com/dss/latest/webapps/security.html#identifying-users-from-within-a-webapp
    # don't use client.get_own_user().get_settings().get_raw() as this would give the user who started the webapp
    request_headers = dict(request.headers)
    auth_info_browser = client.get_auth_info_from_browser_headers(request_headers)
    return auth_info_browser["authIdentifier"]

def tabulator_row_key_values(row, primary_keys):
    """Get values for a given row coming from Tabulator and a list of columns that are primary keys"""
    return DataFrame(data=row, index=[0]).set_index(primary_keys).index[0]

### Other utils (unused)

def get_table_name(dataset, project_key):
    return dataset.get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", dataiku.get_custom_variables().get("NODE"))

def get_webapp_json(webapp_ID):
    project_key = getenv("DKU_CURRENT_PROJECT_KEY")
    return loads(
        requests.get(
            url="http://127.0.0.1:" + dataiku.base.remoterun.get_env_var("DKU_BASE_PORT") + "/public/api/projects/" + project_key + "/webapps/" + webapp_ID,
            headers=dataiku.core.intercom.get_auth_headers(),
            verify=False
        ).text)
