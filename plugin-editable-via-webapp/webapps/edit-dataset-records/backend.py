# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Get webapp parameters (original dataset name and editschema)
# 1. Get user info
# 2. Get editable dataset
# 3. Define webapp layout and components

#%%
# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')
# original_ds_name = ...
# project_key = ...
from json import load, loads
import dataiku
from os import getenv
from dataiku.customwebapp import get_webapp_config
from flask import Flask
from dash import html, Dash
from dash_tabulator import DashTabulator
from dash.dependencies import Input, Output
from EditableEventSourced import EditableEventSourced
from pandas import DataFrame


#%%
if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    original_ds_name = get_webapp_config().get("original_dataset")
    editschema = loads(get_webapp_config().get("editschema"))
else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    original_ds_name = getenv("ORIGINAL_DATASET")
    editschema = load(open(getenv("EDITSCHEMA_PATH")))
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)
    # TODO: how do we pass external stylesheets when using Dataiku?
    application = app.server


# 0. Get user name
#%%
client = dataiku.api_client()
current_user_settings = client.get_own_user().get_settings().get_raw()
user = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""


# 1. Instantiate editable dataset
#%%
ees = EditableEventSourced(original_ds_name, editschema)


# 2. Define the webapp layout and components
#%%
def serve_layout():
    return html.Div([
    html.H3("Edit"),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=DashTabulator(
                id='datatable',
                columns=ees.get_editschema_tabulator(),
                data=ees.get_editable_tabulator(),
                theme='bootstrap/tabulator_bootstrap4',
                options={"selectable": 1, "layout": "fitDataTable"}
            ),
        )
        ])
    ])

app.layout = serve_layout

@app.callback(Output('datatable', 'data'),
               Input('datatable', 'cellEdited'), prevent_initial_call=True)
def update(cell):
    primary_key_values = DataFrame(
                            data=cell["row"],
                            index=[0]
                         ).set_index(ees.get_primary_keys()).index[0]
    column_name = cell["column"]
    value = cell["value"]
    ees.add_edit(primary_key_values, column_name, value, user)
    return ees.get_editable_tabulator()

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
