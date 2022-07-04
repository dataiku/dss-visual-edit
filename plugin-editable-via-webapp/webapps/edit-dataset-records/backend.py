# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# - Get webapp parameters (original dataset, primary keys and editable columns)
# - Instantiate editable event-sourced dataset
# - Define webapp layout and components

#%%
# Get original dataset name and editschema

from os import getenv
from dash import Dash, html

stylesheets = ["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = ["https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js"]

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    stylesheets += ["https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/style.css"] # this points to a copy of assets/style.css (which is ignored by Dataiku's Dash)
    scripts += ["https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/custom_tabulator.js"] # same for assets/custom_tabulator.js

    from dataiku.customwebapp import get_webapp_config
    from json5 import loads
    original_ds_name = get_webapp_config().get("original_dataset")
    primary_keys = get_webapp_config().get("primary_keys")
    editable_column_names = get_webapp_config().get("editable_column_names")
    freeze_editable_columns = False
    editschema_manual_raw = get_webapp_config().get("editschema")
    if (editschema_manual_raw and editschema_manual_raw!=""):
        editschema_manual = loads(editschema_manual_raw)
    else:
        editschema_manual = {}

else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"

    # Get original dataset name as an environment variable
    # Get primary keys and editable column names from the custom fields of that dataset
    import dataiku
    from json5 import load
    original_ds_name = getenv("ORIGINAL_DATASET")
    client = dataiku.api_client()
    project = client.get_project(getenv("DKU_CURRENT_PROJECT_KEY"))
    settings = project.get_dataset(original_ds_name).get_settings()
    primary_keys = settings.custom_fields.get("primary_keys")
    editable_column_names = settings.custom_fields.get("editable_column_names")
    freeze_editable_columns = settings.custom_fields.get("freeze_editable_columns")
    if (freeze_editable_columns==None): freeze_editable_columns = False
    try:
        editschema_manual = load(open("example-editschemas/" + original_ds_name + ".json"))
    except:
        editschema_manual = {}
    
    from flask import Flask
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)

app.config.external_stylesheets = stylesheets
app.config.external_scripts = scripts

#%%
from EditableEventSourced import EditableEventSourced
ees = EditableEventSourced(original_ds_name, primary_keys, editable_column_names, editschema_manual)

#%%
from commons import get_user_details
user = get_user_details()

#%%
# Define the webapp layout and components

import dash_tabulator
from dash.dependencies import Input, Output

def serve_layout():
    return html.Div(children=[
        dash_tabulator.DashTabulator(
            id="datatable",
            columns=ees.get_columns_tabulator(freeze_editable_columns),
            data=ees.get_data_tabulator(),
            theme="semantic-ui/tabulator_semantic-ui",
            options={
                "selectable": 1,
                "layout": "fitDataTable",
                "pagination": "local",
                "paginationSize": 20,
                "paginationSizeSelector":[10, 20, 50, 100],
                "movableColumns": True
            }
        ),
        html.Div(id="edit-info", children="", style={"display": "none"}),
    ], style={})
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
