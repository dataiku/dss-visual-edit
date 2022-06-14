# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Get webapp parameters (original dataset name and editschema)
# 1. Get editable dataset
# 2. Define webapp layout and components


#%%
from EditableEventSourced import EditableEventSourced
from dash import html
from dash_tabulator import DashTabulator
from dash.dependencies import Input, Output
from commons import get_user_details


#%%
# Get original dataset name and editschema
from os import getenv

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"

    from dataiku.customwebapp import get_webapp_config
    from json5 import loads
    original_ds_name = get_webapp_config().get("original_dataset")
    editschema = loads(get_webapp_config().get("editschema"))

else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"

    from json5 import load
    original_ds_name = getenv("ORIGINAL_DATASET")
    editschema = load(open(getenv("EDITSCHEMA_PATH")))
    
    from flask import Flask
    from dash import Dash
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)


#%%
ees = EditableEventSourced(original_ds_name, editschema)
user = get_user_details()


#%%
# Define the webapp layout and components
def serve_layout():
    return html.Div(children=DashTabulator(
                id='datatable',
                columns=ees.get_editschema_tabulator(),
                data=ees.get_editable_tabulator(),
                theme='bootstrap/tabulator_bootstrap4',
                options={"selectable": 1, "layout": "fitDataTable"}
            ))
app.layout = serve_layout

@app.callback(Output('datatable', 'data'),
              Input('datatable', 'cellEdited'),
              prevent_initial_call=True)
def update(cell):
    return ees.add_edit_tabulator(cell, user)

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
