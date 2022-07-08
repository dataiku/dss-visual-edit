# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# - Get webapp parameters (original dataset, primary keys and editable columns)
# - Instantiate editable event-sourced dataset
# - Define webapp layout and components

#%%
# Get original dataset name and editschema

from dataiku import api_client
from os import getenv
from dash import Dash, html, dcc

stylesheets = ["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = ["https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js"]
client = api_client()
project = client.get_project(getenv("DKU_CURRENT_PROJECT_KEY"))

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    stylesheets += ["https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/style.css"] # this points to a copy of assets/style.css (which is ignored by Dataiku's Dash)
    scripts += ["https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/custom_tabulator.js"] # same for assets/custom_tabulator.js
    info_display = "none"

    from dataiku.customwebapp import get_webapp_config
    from json5 import loads
    original_ds_name = get_webapp_config().get("original_dataset")
    primary_keys = get_webapp_config().get("primary_keys")
    editable_column_names = get_webapp_config().get("editable_column_names")
    freeze_editable_columns = get_webapp_config().get("freeze_editable_columns")
    editschema_manual_raw = get_webapp_config().get("editschema")
    if (editschema_manual_raw and editschema_manual_raw!=""):
        editschema_manual = loads(editschema_manual_raw)
    else:
        editschema_manual = {}

else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    info_display = "block"

    # Get original dataset name as an environment variable
    # Get primary keys and editable column names from the custom fields of that dataset
    from json5 import load
    original_ds_name = getenv("ORIGINAL_DATASET")
    settings = project.get_dataset(original_ds_name).get_settings()
    primary_keys = settings.custom_fields.get("primary_keys")
    editable_column_names = settings.custom_fields.get("editable_column_names")
    freeze_editable_columns = False
    try:
        editschema_manual = load(open("../../../example-editschemas/" + original_ds_name + ".json"))
    except:
        editschema_manual = {}
    
    from flask import Flask
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)

def get_last_build_date(ds_name=original_ds_name):
    return project.get_dataset(ds_name).get_last_metric_values().get_metric_by_id("reporting:BUILD_START_DATE").get("lastValues")[0].get("computed")

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

columns = ees.get_columns_tabulator(freeze_editable_columns)
data = ees.get_data_tabulator()

def serve_layout():
    return html.Div(children=[
        html.Div(id="original_ds_update_msg", children=""),
        html.Div(id="last_build_date", children=str(get_last_build_date()), style={"display": "none"}),
        dcc.Interval(
                id="interval-component-iu",
                interval=3*1000, # in milliseconds TODO: increase this
                n_intervals=0
        ),
        dash_tabulator.DashTabulator(
            id="datatable",
            columns=columns,
            data=data,
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
        html.Div(id="edit-info", children="Info zone for tabulator", style={"display": info_display})
    ])
app.layout = serve_layout

@app.callback(
    [
        Output("original_ds_update_msg", "children"),
        Output("last_build_date", "children")
    ],
    [
        Input("interval-component-iu", "n_intervals"),
        State("refresh-btn", "style"),
        State("original_ds_update_msg", "children"),
        State("last_build_date", "children")
    ])
def check_original_data_update(n_intervals, style, original_ds_update_msg, last_build_date):
    msg = original_ds_update_msg
    style_new = style
    last_build_date_new = project.get_dataset(original_ds_name).get_last_metric_values().get_metric_by_id("reporting:BUILD_START_DATE").get("lastValues")[0].get("computed")
    print(f"""last build date: {last_build_date} - last build date new: {str(last_build_date_new)}""") # note: this is a number of milli-seconds -> divide by 1000 and use in datetime.datetime.utcfromtimestamp() to get a human-readable date
    if last_build_date_new>int(last_build_date):
        msg = "The original dataset has changed. Would you like to refresh the data?"
        style_new["display"] = "block"
    print(str(n_intervals) + " - " + msg + " - " + str(last_build_date_new))
    return style_new, msg, last_build_date_new

    ])
def check_original_data_update(n_intervals, last_build_date):
    last_build_date_new = last_build_date
    duration = 0
    # duration = get_last_build_date()-int(last_build_date)
    # if duration>0:
    #     last_build_date_new = str(get_last_build_date())
    #     # note: this is a number of milli-seconds -> divide by 1000 and use in datetime.datetime.utcfromtimestamp() to get a human-readable date
    print(str(n_intervals) + " - " + str(duration))
    return "The original dataset has changed. Would you like to refresh the data?", last_build_date_new

@app.callback(
    Output("info", "children"),
    Input("datatable", "cellEdited"),
    prevent_initial_call=True)
def update(cell):
    return ees.add_edit_tabulator(cell, user)

if __name__=="backend":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
