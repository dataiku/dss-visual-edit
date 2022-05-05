# -*- coding: utf-8 -*-

import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html, Dash
from dash.dependencies import Input, Output, State
from flask import Flask
from pandas import DataFrame, pivot_table
import datetime
import os
import json


# Dash webapp to edit dataset records
# This code is structured as follows:
# 1. Access parameters that end-users filled in using webapp config
# 2. Initialize Dataiku client and project
# 3. Create change log dataset and editable dataset, if they don't already exist
# 4. Initialize the SQL executor and name of table to edit
# 5. Define the layout of the webapp and the DataTable component
# 6. Define the callback function that updates the editable and change log when cell values get edited


# 1. Access parameters that end-users filled in using webapp config

# Define project key
project_key = os.getenv("DKU_CURRENT_PROJECT_KEY")
if (not project_key or project_key==""):
    project_key = "CATEGORIZE_TRANSACTIONS"
os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key

# Define dataset names
if (os.getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    settings = get_webapp_config()["settings"] # TODO: create "settings" text parameter in webapp.json
else:
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)
    application = app.server
    settings = json.load(open("settings-v1.json"))

input_dataset_name = settings["input_dataset"]
# Parse schema
# - 1st pass
def parse_schema(schema):
    editable_column_names = []
    linked_records = []
    for col in schema["columns"]:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
            if col.get("editable_type")=="linked_record":
                linked_records.append(
                    {
                        "name": col.get("name"),
                        "linked_table_name": dataiku.Dataset(col.get("linked_ds"), project_key).get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", dataiku.get_custom_variables().get("NODE")),
                        "linked_key": col.get("linked_ds_key_col"),
                        "lookup_columns": []
                    }
                )
        else:
            if col.get("editable_type")=="key":
                primary_key = col.get("name")
                primary_key_type = col.get("type")
    # - 2nd pass
    for col in schema["columns"]:
        if col.get("editable_type")=="lookup_column":
            for linked_record in linked_records:
                if linked_record["name"]==col.get("linked_record_col"):
                    linked_record["lookup_columns"].append({"name": col.get("name"),
                    "linked_ds_name": col.get("linked_ds_name")})
    return editable_column_names, linked_records, primary_key, primary_key_type
editable_column_names, linked_records, primary_key, primary_key_type = parse_schema(settings["schema"])

# 2. Initialize Dataiku client and project

client = dataiku.api_client()
project = client.get_project(project_key)


original_ds = dataiku.Dataset(input_dataset_name, project_key)
original_df = original_ds.get_dataframe(limit=100) # TODO: limit only for webapp
connection_name = original_ds.get_config()['params']['connection'] # name of the connection to the original dataset, to use for the editlog too
executor = SQLExecutor2(connection=connection_name)


# 3.1. Create editlog, if it doesn't already exist

editlog_ds_name = input_dataset_name + "_editlog_new"
editlog_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, editlog_ds_name)
if (editlog_ds_creator.already_exists()):
    editlog_ds = dataiku.Dataset(editlog_ds_name, project_key)

    # TODO: V2: lookup columns to retrieve
    # for this we create a new table with our original_df sample and execute a join query between it and each linked dataset
else:
    editlog_schema = [
        {"name": primary_key, "type": primary_key_type},
        {"name": "column_name", "type": "string"},
        {"name": "value", "type": "string"},
        {"name": "date", "type": "date"},
        {"name": "user", "type": "string"}
    ]
    editlog_ds_creator.with_store_into(connection=connection_name)
    editlog_ds_creator.create()
    editlog_ds = dataiku.Dataset(editlog_ds_name)
    editlog_ds.write_schema(editlog_schema)
editlog_ds.spec_item["appendMode"] = True # make sure that we append to that dataset (and don't write over it)
editlog_df = editlog_ds.get_dataframe()
from commons import replay_edits
editable_df = replay_edits(original_df, editlog_df, primary_key, editable_column_names)

# TODO: V2: Implement linked records
# ext_ds = dataiku.Dataset(ext_dataset, project_key)
# ext_tablename = ext_ds.get_config()['params']['table'].replace("${projectKey}", project_key)



# 3.2. Define columns to use in the DataTable component later on

# IDEA: loop over columns identified as linked records, and lookup columns for each
pd_cols = editable_df.columns.tolist()
# pd_cols.insert(0, primary_key)
# for col in ext_lookup_columns: pd_cols.append("ext_" + col) # TODO: V2: how is ext_lookup_columns defined?
dash_cols = ([{"name": i, "id": i} for i in pd_cols]) # columns for dash


# 5. Define the layout of the webapp

app.layout = html.Div([
    html.H3("Edit"),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=dash_table.DataTable(
                id='editable-table',
                columns=dash_cols,
                style_cell_conditional=[
                    {
                        'if': {'column_id': c},
                        'backgroundColor': '#d8e3ed'
                    } for c in editable_column_names
                ],
                style_as_list_view=True,
                data=editable_df[pd_cols].to_dict('records'),
                editable=True
            ),
        ),
        html.Pre(id='output')
    ])
])


# 6. Define the callback function that updates the editlog when cell values get edited

@app.callback([Output('output', 'children'),
               Output('editable-table', 'data')],
              [State('editable-table', 'active_cell'),
               Input('editable-table', 'data')], prevent_initial_call=True)
def update(cell_coordinates, table_data):
    # Determine the row and column of the cell that was edited
    row_id = cell_coordinates["row"]-1
    column_name = cell_coordinates["column_id"]
    primary_key_value = table_data[row_id][primary_key]
    value = table_data[row_id][column_name]
    
    # Set the date of the change and the user behind it
    d = datetime.date.today()
    current_user_settings = client.get_own_user().get_settings().get_raw()
    u = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""

    # Update table data
    message = f"""Updated column {column_name} where {primary_key} is {primary_key_value}.
                  New value: {value}."""
    # TODO: V2: implement lookup columns

    # Add to editlog
    edit_df = DataFrame(data={primary_key: [primary_key_value], "column_name": [column_name], "value": [value], "date": [d], "user": [u]})
    editlog_ds.write_dataframe(edit_df)

    # Loop over editable linked records
    for linked_record in linked_records:
        if (column_name==linked_record["name"]):
            # Retrieve values of the lookup columns from the external dataset, corresponding to the edited value
            # IDEA: add linked_record["linked_key"] as an INDEX to speed up the query
            lookup_columns_linked_ds_names = []
            for lookup_column in linked_record["lookup_columns"]:
                lookup_columns_linked_ds_names.append(lookup_column["linked_ds_name"])
            select_query = f"""SELECT {", ".join(lookup_columns_linked_ds_names)}
                               FROM "{linked_record["linked_table_name"]}"
                               WHERE "{linked_record["linked_key"]}"={value}"""
            select_df = executor.query_to_df(select_query)
            # Update table_data with these values — note that column names are different in table_data and in the linked record's table
            for lookup_column in linked_record["lookup_columns"]:
                table_data[row_id][lookup_column["name"]] = select_df[lookup_column["linked_ds_name"]].iloc[0]

    return message, table_data


# Run Dash app in debug mode when outside of Dataiku
if __name__ == "__main__":
    if app: app.run_server(debug=True)
