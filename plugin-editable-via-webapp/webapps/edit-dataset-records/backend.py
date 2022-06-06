# -*- coding: utf-8 -*-

import dataiku
from os import getenv
from dataiku.customwebapp import get_webapp_config
from flask import Flask
from dash import html, Dash
from dash_tabulator import DashTabulator
from dash.dependencies import Input, Output
from EditableEventSourced import EditableEventSourced
# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')


# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 1. Get editable dataset
# 2. Define webapp layout and components


if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    original_ds_name = get_webapp_config().get("original_dataset")
else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    original_ds_name = getenv("ORIGINAL_DATASET")
    f_app = Flask(__name__)
    app = Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"], external_scripts=["https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js"], server=f_app)
    # TODO: how do we pass external stylesheets when using Dataiku?
    application = app.server


client = dataiku.api_client()


# 0. Get user name
# TODO: fix this with https://doc.dataiku.com/dss/latest/webapps/security.html#identifying-users-from-within-a-webapp
current_user_settings = client.get_own_user().get_settings().get_raw()
user = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""


# 1. Get editable dataset

ees = EditableEventSourced(original_ds_name)


# 2. Define the webapp layout and components

def serve_layout(): # see https://dash.plotly.com/live-updates
    return html.Div([
    html.H3("Edit"),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=DashTabulator(
                id='datatable',
                columns=ees.get_schema_tabulator(),
                data=ees.get_editable_tabulator(),
                theme='bootstrap/tabulator_bootstrap4',
                options={"selectable": 1, "layout": "fitDataTable"},
                # see http://tabulator.info/docs/5.2/options#columns for layout options
                # IDEA: groupby option is interesting for Fuzzy Join use case - see https://github.com/preftech/dash-tabulator
            ),
        )
        ])
    ])

app.layout = serve_layout

@app.callback(Output('datatable', 'data'),
               Input('datatable', 'cellEdited'), prevent_initial_call=True)
def update(cell):
    primary_key_value = cell["row"][ees.get_primary_key()]
    column_name = cell["column"]
    value = cell["value"]
    ees.add_edit(primary_key_value, column_name, value, user)
    return ees.get_editable_tabulator()

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
