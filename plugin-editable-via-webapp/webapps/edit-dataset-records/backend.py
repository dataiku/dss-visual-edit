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
# when using interactive execution:
# sys.path.append('../../python-lib')


# Dash webapp to edit dataset records
# TODO: update this description
# This code is structured as follows:
# 0. Init: get webapp settings, Dataiku client, and project
# 1. Parse edit schema, load input and editlog dataframes
# 2. Create editable_df used in the webapp's DataTable
# 3. Define the webapp layout and its DataTable
# 4. Define the callback function that updates the editlog when cell values get edited


# 0. Init: get webapp settings, Dataiku client, and project

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


# 1. Parse edit schema, load input and editlog dataframes

editable_column_names, display_column_names, linked_records, primary_key, primary_key_type = commons.parse_schema(schema)

input_ds = dataiku.Dataset(input_dataset_name, project_key)
input_df = input_ds.get_dataframe(limit=100)
input_df = input_df[[primary_key] + display_column_names + editable_column_names]

editlog_ds, editlog_df = commons.get_editlog(input_dataset_name)


# 2. Create editable_df used in the webapp's DataTable:
#    -> Replay edits on input dataset
#    -> Add lookup columns

editable_df = commons.replay_edits(input_df, editlog_df, primary_key, editable_column_names)
print("Edits replayed OK")
editable_df = commons.add_lookup_columns(editable_df, linked_records)


# 3. Define the webapp layout and its DataTable

eds = EditableDataset(input_dataset_name, schema)
editable_df = eds.get_editable_df()

pd_cols = editable_df.columns.tolist()
dt_cols = ([{"name": i, "id": i} for i in pd_cols]) # columns for DataTable
dt_data = editable_df[pd_cols].to_dict('records') # data for DataTable

app.layout = html.Div([
    html.H3("Edit"),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=dash_table.DataTable(
                id='editable-table',
                columns=dt_cols,
                data=dt_data,
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


# 4. Define the callback function that updates the editlog when cell values get edited

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
            df = commons.get_lookup_values(linked_record, value)
            # Update table_data with these values — note that column names are different in table_data and in the linked record's table
            for lookup_column in linked_record["lookup_columns"]:
                table_data[row_id][lookup_column["name"]] = df[lookup_column["linked_ds_column_name"]].iloc[0]

    current_user_settings = client.get_own_user().get_settings().get_raw()
    eds.append_edit(column_name, value, current_user_settings)
    message = f"""Updated column {column_name} where {primary_key} is {primary_key_value}. New value: {value}."""
    print(message)

    return message, table_data


# Run Dash app in debug mode when outside of Dataiku

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
