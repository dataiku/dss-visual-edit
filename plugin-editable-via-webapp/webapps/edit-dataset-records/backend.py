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
project_key = getenv("DKU_CURRENT_PROJECT_KEY")
project = client.get_project(project_key)

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
    group_column_names = get_webapp_config().get("group_column_names")
    editschema_manual_raw = get_webapp_config().get("editschema")
    if (editschema_manual_raw and editschema_manual_raw!=""):
        editschema_manual = loads(editschema_manual_raw)
    else:
        editschema_manual = {}

    server = app.server

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
    group_column_names = []
    try:
        editschema_manual = load(open("../../../example-editschemas/" + original_ds_name + ".json"))
    except:
        editschema_manual = {}
    
    from flask import Flask
    server = Flask(__name__)
    app = Dash(__name__, server=server)

app.config.external_stylesheets = stylesheets
app.config.external_scripts = scripts

#%%
from EditableEventSourced import EditableEventSourced
ees = EditableEventSourced(original_ds_name, primary_keys, editable_column_names, editschema_manual)

#%%
# Define the webapp layout and components

import dash_tabulator
from datetime import datetime
from commons import get_user_details, get_last_build_date

columns = ees.get_columns_tabulator(freeze_editable_columns)
data = ees.get_data_tabulator()

try:
    last_build_date = get_last_build_date(original_ds_name, project)
    last_build_date_ok = True
except:
    last_build_date = ""
    last_build_date_ok = False

def serve_layout():
    return html.Div(children=[
        html.Div(id="refresh-div", children=[
            html.Div(id="data-refresh-message", children="The original dataset has changed. Do you want to refresh? (Your edits are safe.)", style={"display": "inline"}),
            html.Div(id="last-build-date", children=str(last_build_date), style={"display": "none"}), # when the original dataset was last built
            html.Div(id="last-refresh-date", children="", style={"display": "none"}), # when the data in the datatable was last refreshed
            html.Button("Refresh", id="refresh-btn", n_clicks=0, className="ui compact yellow button", style={"margin-left": "2em", })
        ], className="ui compact warning message", style={"display": "none"}),

        dcc.Interval(
                id="interval-component-iu",
                interval=20*1000, # in milliseconds
                n_intervals=0
        ),

        dash_tabulator.DashTabulator(
            id="datatable",
            columns=columns,
            data=data,
            groupBy=group_column_names
        ),

        html.Div(id="edit-info", children="Info zone for tabulator", style={"display": info_display})
    ])
app.layout = serve_layout

@app.callback(
    [
        Output("refresh-div", "style"),
        Output("last-build-date", "children")
    ],
    [
        Input("interval-component-iu", "n_intervals"),
        Input("last-refresh-date", "children"),
        State("refresh-div", "style"),
        State("last-build-date", "children")
    ],
    prevent_initial_call=True)
def toggle_refresh_div_visibility(n_intervals, last_refresh_date, refresh_div_style, last_build_date):
    """
    Toggle visibility of refresh div, once...

    * The interval component has fired: check last build date of original dataset and if it's more recent than what we had, display the refresh div
    * The refresh date has changed: hide the refresh div
    """
    style_new = refresh_div_style
    if last_build_date_ok:
        if (callback_context.triggered_id=="interval-component-iu"):
            last_build_date_new = str(get_last_build_date(original_ds_name, project))
            if int(last_build_date_new)>int(last_build_date):
                print("The original dataset has changed.")
                last_build_date_new_fmtd = datetime.utcfromtimestamp(int(last_build_date_new)/1000).isoformat()
                last_build_date_fmtd = datetime.utcfromtimestamp(int(last_build_date)/1000).isoformat()
                print(f"""Last build date: {last_build_date_new_fmtd} — previously {last_build_date_fmtd}""")
                style_new["display"] = "block"
        else: # callback_context must be "last_refresh_date"
            print("Datatable has been refreshed -> hiding refresh div")
            last_build_date_new = last_build_date
            style_new["display"] = "none"
    return style_new, last_build_date_new

@app.callback(
    [
        Output("last-refresh-date", "children"),
        Output("datatable", "data"),
    ],
    [
        Input("refresh-btn", "n_clicks")
    ],
    prevent_initial_call=True)
def refresh_data(n_clicks):
    """
    Refresh datatable's contents based on the latest original and editlog datasets, once the refresh button has been clicked
    """
    print("Refreshing the data...")
    ees.load_data() # this loads the original df again, pivots the editlog and merges edits
    data = ees.get_data_tabulator()
    print("Done.")
    return datetime.now().isoformat(), data

@app.callback(
    Output("edit-info", "children"),
    Input("datatable", "cellEdited"),
    prevent_initial_call=True)
def add_edit(cell):
    """
    Record edit in editlog, once a cell has been edited
    """
    if run_context=="local": user = "local"
    else: user = get_user_details()
    return ees.add_edit_tabulator(cell, user)

# if run_context=="local":
#     print("Running in debug mode")
#     app.run_server(debug=True)

@server.route("/dash")
def my_dash_app():
    return app.index()

from flask import request, jsonify
from json import dumps
from dataikuapi.utils import DataikuStreamedHttpUTF8CSVReader
from pandas import DataFrame
@server.route("/lookup/<linked_ds_name>/", methods=['GET', 'POST'])
def my_flask_endpoint(linked_ds_name):
    response = jsonify({})
    if linked_ds_name in ees.linked_records_df["ds_name"].to_list(): # check that this is a linked dataset
        linked_record_row = ees.linked_records_df.loc[ees.linked_records_df["ds_name"]==linked_ds_name]
        linked_ds_lookup_columns = linked_record_row["ds_lookup_columns"][0]
        linked_ds_label = linked_record_row["ds_label"][0]
        linked_ds_key = linked_record_row["ds_key"][0]
        linked_ds = project.get_dataset(linked_ds_name)

        if request.method == 'POST':
            term = request.get_json().get("term")
        else:
            term = request.args.get('term', '')
        print(f"""Received a request for dataset "{linked_ds_name}", term "{term}" """)
        
        if (len(term)>=3):
            csv_stream = client._perform_raw(
                "GET" , f"/projects/{project_key}/datasets/{linked_ds_name}/data/",
                params = {
                    "format" : "tsv-excel-header",
                    "filter" : f"""contains(toLowercase(strval("{linked_ds_label}")), toLowercase("{term}"))""",
                    "sampling" : dumps({
                        "samplingMethod": "HEAD_SEQUENTIAL",
                        "maxRecords": 100
                        })
                })
            csv_reader = DataikuStreamedHttpUTF8CSVReader(linked_ds.get_schema()["columns"], csv_stream)
            rows = []
            for row in csv_reader.iter_rows():
                rows.append(row)
            linked_df_filtered = DataFrame(columns=rows[0], data=rows[1:]).sort_values(linked_ds_label)

            linked_columns = [linked_ds_key]
            if (linked_ds_label!=linked_ds_key):
                linked_columns += [linked_ds_label]
            if linked_ds_lookup_columns!=[]:
                linked_columns += linked_ds_lookup_columns

            if len(linked_columns)>1:
                result = linked_df_filtered[linked_columns].to_dict("records")
            else:
                result = linked_df_filtered[linked_columns[0]].to_list()
            
            response = jsonify(result)

    return response


print("Webapp OK")
