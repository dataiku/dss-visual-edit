import dataiku
from pandas import DataFrame, concat, pivot_table
from json import loads
from os import getenv
import requests


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

def get_editable_column_names(schema):
    editable_column_names = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
    return editable_column_names

def pivot_editlog(editlog_ds, primary_keys, editable_column_names):
    # Create empty dataframe with the proper editlog pivoted schema: all primary keys, all editable columns, and "date" column
    # This helps ensure that the dataframe we return always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = primary_keys + editable_column_names + ["date"]
    all_columns_df = DataFrame(columns=cols)

    editlog_df = get_editlog_df(editlog_ds)
    if (not editlog_df.size): # i.e. if empty editlog
        editlog_pivoted_df = all_columns_df
    else:
        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("date"), # ordering by edit date
            index="key",
            columns="column_name",
            values="value",
            aggfunc="last" # for each named column, we only keep the last value
        ).join(
            editlog_df[["key", "date"]].groupby("key").last(), # join the last edit date for each key
            on="key"
        )

        # Unpack keys
        # primary_keys = ["key1", "key2"]
        # editlog_pivoted_df = DataFrame(data={"key": ["('one', 'two')", "('three', 'four')"], "col1": [1, 2], "col2": [3, 4]})
        def unpack(row):
            return eval(row["key"]) # convert string to tuple
        editlog_pivoted_df.reset_index(inplace=True)
        keys = editlog_pivoted_df.apply(unpack, axis=1, result_type="expand")
        editlog_pivoted_df.drop(columns=["key"], inplace=True)

        # add keys to editlog_pivoted
        # - old version: editlog_pivoted_df[primary_keys] = keys
        # - new version with insert():
        i = 0
        for primary_key in primary_keys:
            editlog_pivoted_df.insert(i, primary_key, keys.loc[:, i].to_list())
            i += 1

        editlog_pivoted_df = concat([all_columns_df, editlog_pivoted_df])

    return editlog_pivoted_df

def merge_edits(original_df, editlog_pivoted_df, primary_keys):
    if (not editlog_pivoted_df.size): # i.e. if empty editlog
        edited_df = original_df
    else:
        # We don't need the date column in the rest
        editlog_pivoted_df.drop(columns=["date"], inplace=True)

        # Change types of primary keys to match original_df
        for col in primary_keys: # or editlog_pivoted_df.columns.tolist() ?
            editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(original_df[col].dtypes.name)

        # Join -> this adds _value_last columns
        original_df.set_index(primary_keys, inplace=True)
        editlog_pivoted_df.set_index(primary_keys, inplace=True)
        edited_df = original_df.join(editlog_pivoted_df, on=primary_keys, rsuffix="_value_last")
        
        # "Merge" -> this creates _original columns
        editable_column_names = editlog_pivoted_df.columns.tolist() # "date" column has already been dropped
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
    current_user_settings = client.get_own_user().get_settings().get_raw()
    return f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""

def tabulator_row_key_values(row, primary_keys):
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
