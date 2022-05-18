# -*- coding: utf-8 -*-

import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html, Dash
from dash.dependencies import Input, Output, State
from flask import Flask
from pandas import DataFrame
import datetime, pytz
import os
import json
import commons




# Dash webapp to edit dataset records
# TODO: update this description
# This code is structured as follows:
# 1. Access parameters that end-users filled in using webapp config
# 2. Initialize Dataiku client and project
# 3. Create change log dataset and editable dataset, if they don't already exist
# 5. Define the layout of the webapp and the DataTable component
# 6. Define the callback function that updates the editable and change log when cell values get edited


# 0. Init: get webapp settings, Dataiku client and project

if (os.getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    project_key = os.getenv("DKU_CURRENT_PROJECT_KEY")

    # get parameters from webapp config (specific to the current webapp)
    input_dataset_name = get_webapp_config()["input_dataset"]
    schema = json.loads(get_webapp_config()["schema"])
    
else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    settings = json.load(open(os.getenv("EDIT_DATASET_RECORDS_SETTINGS"))) # define this env variable in VS Code launch config and have it point to a settings file that contains the project key
    project_key = settings["project_key"]
    os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key # just in case

    # get parameters from settings file (specific to the current webapp)
    input_dataset_name = settings["input_dataset"]
    schema = settings["schema"]

    # instantiate Dash
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)
    application = app.server

client = dataiku.api_client()
project = client.get_project(project_key)



def parse_schema(schema):
    """Parse editable schema"""

    # First pass at the list of columns
    editable_column_names = []
    display_column_names = []
    linked_records = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
            if col.get("editable_type")=="linked_record":
                linked_records.append(
                    {
                        "name": col.get("name"),
                        "type": col.get("type"),
                        "ds_name": col.get("linked_ds_name"),
                        "ds_key": col.get("linked_ds_key"),
                        "lookup_columns": []
                    }
                )
        else:
            if col.get("editable_type")=="key":
                primary_key = col.get("name")
                primary_key_type = col.get("type")
            else:
                display_column_names.append(col.get("name"))

    # Second pass to create the lookup columns for each linked record
    for col in schema:
        if col.get("editable_type")=="lookup_column":
            for linked_record in linked_records:
                if linked_record["name"]==col.get("linked_record_col"):
                    linked_record["lookup_columns"].append({
                        "name": col.get("name"),
                        "linked_ds_column_name": col.get("linked_ds_column_name")
                    })

    return editable_column_names, display_column_names, linked_records, primary_key, primary_key_type

editable_column_names, display_column_names, linked_records, primary_key, primary_key_type = parse_schema(schema)
print("Schema parsed OK")
input_ds = dataiku.Dataset(input_dataset_name, project_key)
input_df = input_ds.get_dataframe(limit=100)
input_df = input_df[[primary_key] + display_column_names + editable_column_names]
connection_name = input_ds.get_config()['params']['connection'] # name of the connection to the original dataset, to use for the editlog too


# 3.1. Create editlog, if it doesn't already exist

editlog_ds_name = input_dataset_name + "_editlog"
editlog_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, editlog_ds_name)
if (editlog_ds_creator.already_exists()):
    editlog_ds = dataiku.Dataset(editlog_ds_name, project_key)
    editlog_df = editlog_ds.get_dataframe()
else:
    print("No editlog found, creating one")
    editlog_ds_creator.with_store_into(connection=connection_name)
    editlog_ds_creator.create()
    editlog_ds = dataiku.Dataset(editlog_ds_name)
    editlog_df = DataFrame(columns=commons.get_editlog_columns())
    editlog_ds.write_schema(commons.get_editlog_schema())
    editlog_ds.write_dataframe(editlog_df)
editlog_ds.spec_item["appendMode"] = True # make sure that we append to that dataset (and don't write over it)
print("Editlog OK")


# Replay edits

# when using interactive execution:
# sys.path.append('../../python-lib')
editable_df = commons.replay_edits(input_df, editlog_df, primary_key, editable_column_names)
print("Edits replayed OK")

# Get lookup columns

for linked_record in linked_records:
    lookup_column_names = []
    lookup_column_names_in_linked_ds = []
    for lookup_column in linked_record["lookup_columns"]:
        lookup_column_names.append(lookup_column["name"])
        lookup_column_names_in_linked_ds.append(lookup_column["linked_ds_column_name"])
    linked_ds = dataiku.Dataset(linked_record["ds_name"], project_key)
    linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
    editable_df = editable_df.join(linked_df, on=linked_record["name"])
    for c in range(0, len(lookup_column_names)):
        editable_df.rename(columns={lookup_column_names_in_linked_ds[c]: lookup_column_names[c]}, inplace=True)
print("Lookup columns OK")


# 3.2. Define columns to use in the DataTable component

pd_cols = editable_df.columns.tolist()
# pd_cols.insert(0, primary_key)
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
                data=editable_df[pd_cols].to_dict('records'),
                editable=True,
                style_cell_conditional=[
                    {
                        'if': {'column_id': c},
                        'backgroundColor': '#d8e3ed'
                    } for c in editable_column_names
                ],
                style_as_list_view=True
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

    # Update table data if a linked record was edited: refresh corresponding lookup columns
    for linked_record in linked_records:
        if (column_name==linked_record["name"]):
            # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
            # IDEA: add linked_record["linked_key"] as an INDEX to speed up the query
            lookup_column_names_in_linked_ds = []
            for lookup_column in linked_record["lookup_columns"]:
                lookup_column_names_in_linked_ds.append(lookup_column["linked_ds_column_name"])
            
            linked_ds = dataiku.Dataset(linked_record["ds_name"], project_key)
            linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
            value_cast = value
            if (linked_record["type"] == "int"):
                value_cast = int(value)
            select_df = linked_df.loc[linked_df.index==value_cast]

            # Update table_data with these values — note that column names are different in table_data and in the linked record's table
            for lookup_column in linked_record["lookup_columns"]:
                table_data[row_id][lookup_column["name"]] = select_df[lookup_column["linked_ds_column_name"]].iloc[0]

    # Set the date of the change and the user behind it
    tz = pytz.timezone("UTC")
    d = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    current_user_settings = client.get_own_user().get_settings().get_raw()
    u = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""
    
    # Add to editlog
    # if the type of column_name is a boolean, make sure we read it correctly
    for col in schema:
        if (col["name"]==column_name):
            if (col["type"]=="bool" or col["type"]=="boolean"):
                value = str(json.loads(value.lower()))
            break
    edit_df = DataFrame(data={"key": [str(primary_key_value)], "column_name": [column_name], "value": [str(value)], "date": [d], "user": [u]})
    editlog_ds.write_dataframe(edit_df)

    message = f"""Updated column {column_name} where {primary_key} is {primary_key_value}. New value: {value}."""
    print(message)

    return message, table_data


# Run Dash app in debug mode when outside of Dataiku
if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
