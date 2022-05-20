# -*- coding: utf-8 -*-

import dataiku
from os import environ, getenv
from json import load, loads
from commons import EditableDataset
from dataiku.customwebapp import get_webapp_config
from flask import Flask
from dash import dash_table, html, Dash
from dash.dependencies import Input, Output, State

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')


# Dash webapp to edit dataset records

# This code is structured as follows:
# 0. Init: get webapp settings, Dataiku client, and project
# 1. Get editable dataset and dataframe
# 2. Define the webapp layout and its DataTable
# 3. Define the callback function that updates the editlog when cell values get edited


# 0. Init: get webapp settings and Dataiku client

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    project_key = getenv("DKU_CURRENT_PROJECT_KEY")

    # get parameters from webapp config (specific to the current webapp)
    input_dataset_name = get_webapp_config()["input_dataset"]
    schema = loads(get_webapp_config()["schema"])

else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    settings = load(open(getenv("EDIT_DATASET_RECORDS_SETTINGS"))) # define this env variable in VS Code launch config and have it point to a settings file that contains the project key
    project_key = settings["project_key"]
    environ["DKU_CURRENT_PROJECT_KEY"] = project_key # just in case

    # get parameters from settings file (specific to the current webapp)
    input_dataset_name = settings["input_dataset"]
    schema = settings["schema"]

    # instantiate Dash
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)
    application = app.server

client = dataiku.api_client()


# 1. Get editable dataset and dataframe

eds = EditableDataset(input_dataset_name, project_key, schema)
editable_df = eds.get_editable_df()


# 2. Define the webapp layout and its DataTable 

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
                    } for c in eds.editable_column_names
                ],
                style_as_list_view=True
            ),
        ),
        html.Pre(id='output')
    ])
])


# 3. Define the callback function that updates the editlog when cell values get edited

@app.callback([Output('output', 'children'),
               Output('editable-table', 'data')],
              [State('editable-table', 'active_cell'),
               Input('editable-table', 'data')], prevent_initial_call=True)
def update(cell_coordinates, table_data):
    # Determine the row and column of the cell that was edited
    row_id = cell_coordinates["row"]-1
    column_name = cell_coordinates["column_id"]
    primary_key_value = table_data[row_id][eds.primary_key]
    value = table_data[row_id][column_name]

    # Update table data if a linked record was edited: refresh corresponding lookup columns
    for linked_record in eds.linked_records:
        if (column_name==linked_record["name"]):
            # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
            lookup_values = eds.get_lookup_values(linked_record, value)

            # Update table_data with lookup values — note that column names are different in table_data and in the linked record's table
            for lookup_column in linked_record["lookup_columns"]:
                table_data[row_id][lookup_column["name"]] = lookup_values[lookup_column["linked_ds_column_name"]].iloc[0]

    current_user_settings = client.get_own_user().get_settings().get_raw()
    user = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""

    eds.add_edit(primary_key_value, column_name, value, user)

    message = f"""Updated column {column_name} where {eds.primary_key} is {primary_key_value}. New value: {value}."""
    print(message)

    return message, table_data


# Run Dash app in debug mode when outside of Dataiku

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
