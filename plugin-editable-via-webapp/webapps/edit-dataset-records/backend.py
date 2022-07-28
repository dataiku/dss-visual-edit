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
from dash import Dash, html, dcc, Input, Output, State, callback_context

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
# Define the webapp layout and components

import dash_tabulator
from datetime import datetime
from commons import get_user_details

columns = ees.get_columns_tabulator(freeze_editable_columns)
data = ees.get_data_tabulator()

def serve_layout():
    return html.Div(children=[
        dcc.Location(id="url", refresh=False), # represents the browser address bar and doesn't render anything
        html.Div(id="url-div", style={"display": "none"}),
        html.Div(id="refresh-div", children=[
            html.Div(id="ds_update_msg", children="The original dataset has changed. Do you want to refresh? (Your edits will persist.)", className="ui warning message"),
            html.Div(id="last_build_date", children=str(get_last_build_date()), style={"display": "none"}),
            html.Div(id="refresh-date", children="", style={"display": "none"}),
            html.Button("Refresh", id="refresh-btn", n_clicks=0, className="ui button", style={})
        ], style={"display": "none"}),
        dcc.Interval(
                id="interval-component-iu",
                interval=20*1000, # in milliseconds
                n_intervals=0
        ),
        dash_tabulator.DashTabulator(
            id="datatable",
            columns=columns,
            data=data
        ),
        html.Div(id="edit-info", children="Info zone for tabulator", style={"display": info_display})
    ])
app.layout = serve_layout

@app.callback(
    Output("url-div", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    msg = f"Webapp URL: {pathname}"
    print(msg)
    return msg

@app.callback(
    [
        Output("refresh-div", "style"),
        Output("last_build_date", "children")
    ],
    [
        Input("interval-component-iu", "n_intervals"),
        Input("refresh-date", "children"),
        State("refresh-div", "style"),
        State("last_build_date", "children")
    ],
    prevent_initial_call=True)
def check_data_update(n_intervals, refresh_date, refresh_div_style, last_build_date):
    style_new = refresh_div_style
    style_new["display"] = "none"
    if (callback_context.triggered_id=="interval-component-iu"):
        last_build_date_new = str(project.get_dataset(original_ds_name).get_last_metric_values().get_metric_by_id("reporting:BUILD_START_DATE").get("lastValues")[0].get("computed"))
        if int(last_build_date_new)>int(last_build_date):
            print("The original dataset has changed.")
            last_build_date_new_fmtd = datetime.utcfromtimestamp(int(last_build_date_new)/1000).isoformat()
            last_build_date_fmtd = datetime.utcfromtimestamp(int(last_build_date)/1000).isoformat()
            print(f"""Last build date: {last_build_date_new_fmtd} — previously {last_build_date_fmtd}""")
            style_new["display"] = "block"
    else:
        print("Datatable has been refreshed -> hiding refresh div")
        last_build_date_new = last_build_date
        style_new["display"] = "none"
    return style_new, last_build_date_new

@app.callback(
    [
        Output("refresh-date", "children"),
        Output("datatable", "data"),
    ],
    [
        Input("refresh-btn", "n_clicks")
    ],
    prevent_initial_call=True)
def refresh(n_clicks):
    print("Refreshing the data...")
    ees.load_data() # this loads the original df again, pivots the editlog and merges edits
    data = ees.get_data_tabulator()
    print("Done.")
    return datetime.now().isoformat(), data

@app.callback(
    Output("edit-info", "children"),
    Input("datatable", "cellEdited"),
    prevent_initial_call=True)
def update(cell):
    if run_context=="local": user = "local"
    else: user = get_user_details()
    return ees.add_edit_tabulator(cell, user)

# if run_context=="local":
#     print("Running in debug mode")
#     app.run_server(debug=True)

print("Webapp OK")
