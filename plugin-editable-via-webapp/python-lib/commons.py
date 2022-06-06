import dataiku
from pandas import DataFrame, concat, pivot_table
from json import loads
from os import getenv
import requests


### Editlog utils

def get_editlog_schema():
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
        editlog_ds.write_schema(get_editlog_schema())
        editlog_ds.write_dataframe(editlog_df)
        print("Done.")
    return editlog_df

### Recipe utils

def get_primary_key(schema):
    for col in schema:
        if col.get("editable_type")=="key":
            return col.get("name"), col.get("type")

def merge_edits(original_df, editlog_pivoted_df, primary_key):
    original_df.set_index(primary_key, inplace=True)
    if (not editlog_pivoted_df.size): # i.e. if empty editlog
        edited_df = original_df
    else:
        editlog_pivoted_df.set_index("key", inplace=True)

        # We don't need the date column in the rest
        editlog_pivoted_df = editlog_pivoted_df.drop(columns=["date"])

        # Change types of columns to match original_df?
        # for col in editlog_pivoted_df.columns.tolist():
        #     editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(input_df[col].dtype)

        # Join -> this adds _value_last columns
        editlog_pivoted_df.index.names = [primary_key]
        edited_df = original_df.join(editlog_pivoted_df, rsuffix="_value_last")

        # "Merge" -> this creates _original columns
        editable_column_names = editlog_pivoted_df.columns.tolist() # "date" column has already been dropped
        for col in editable_column_names:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"])

        # Drop the _original and _value_last columns -> this gets us back to the original schema
        edited_df = edited_df[edited_df.columns[:-2*len(editable_column_names)]]

    return edited_df.reset_index()

def pivot_editlog(editlog_ds, editable_column_names):
    # Create empty dataframe that has all editable columns
    # This will help make sure that the pivoted editlog always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = ["key"] + editable_column_names + ["date"]
    all_editable_columns_df = DataFrame(columns=cols)
    all_editable_columns_df.set_index("key", inplace=True)

    editlog_df = get_editlog_df(editlog_ds)
    if (not editlog_df.size): # i.e. if empty editlog
        editlog_pivoted_df = all_editable_columns_df
    else:
        editlog_df.set_index("key", inplace=True)
        # For each named column, we only keep the last value
        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("date"), # ordering by edit date
            index="key",
            columns="column_name",
            values="value",
            aggfunc="last"
        ).join(
            editlog_df[["date"]].groupby("key").last() # join the last edit date for each key
        )
        editlog_pivoted_df = concat([all_editable_columns_df, editlog_pivoted_df])

    return editlog_pivoted_df.reset_index()

### Other utils

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
