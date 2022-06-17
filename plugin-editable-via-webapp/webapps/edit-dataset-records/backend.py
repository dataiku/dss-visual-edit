# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Get webapp parameters (original dataset name and editschema)
# 1. Get editable dataset
# 2. Define webapp layout and components


#%%
# Get original dataset name and editschema

from os import getenv
from dash import Dash, html

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"

    from dataiku.customwebapp import get_webapp_config
    original_ds_name = get_webapp_config().get("original_dataset")
    primary_keys = get_webapp_config().get("primary_keys")
    editable_column_names = get_webapp_config().get("editable_column_names")

else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"

    from json5 import load
    from commons import get_primary_keys, get_editable_column_names
    original_ds_name = getenv("ORIGINAL_DATASET")
    editschema = load(open(getenv("EDITSCHEMA_PATH")))
    primary_keys = get_primary_keys(editschema)
    editable_column_names = get_editable_column_names(editschema)
    
    from flask import Flask
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)


#%%
from EditableEventSourced import EditableEventSourced
ees = EditableEventSourced(original_ds_name, primary_keys, editable_column_names)

#%%
from commons import get_user_details
user = get_user_details()


#%%
# Define the webapp layout and components
from dash_tabulator import DashTabulator
from dash.dependencies import Input, Output

def serve_layout():
    return html.Div([
        DashTabulator(
            id='datatable',
            columns=ees.get_columns_tabulator(),
            data=ees.get_data_tabulator(),
            theme='bootstrap/tabulator_bootstrap4',
            options={"selectable": 1, "layout": "fitDataTable", "pagination": "local", "paginationSize": 10, "paginationSizeSelector":[10, 25, 50, 100]}
        ),
        html.Div(id='edit-info', children="", style={"display": "none"}),
    ])
app.layout = serve_layout

@app.callback(
    Output('edit-info', 'children'),
    Input('datatable', 'cellEdited'),
    prevent_initial_call=True)
def update(cell):
    return ees.add_edit_tabulator(cell, user)

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
