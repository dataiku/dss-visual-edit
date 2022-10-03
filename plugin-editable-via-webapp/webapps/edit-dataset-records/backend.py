# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# - Get webapp parameters (original dataset, primary keys and editable columns)
# - Instantiate editable event-sourced dataset
# - Define webapp layout and components

#%%
# Get original dataset name and editschema

import logging
from dataiku import api_client
from os import getenv
from dash import Dash, html, dcc, Input, Output, State, callback_context

logging.basicConfig(level=logging.INFO)
stylesheets = ["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = ["https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js"]
client = api_client()
project_key = getenv("DKU_CURRENT_PROJECT_KEY")
project = client.get_project(project_key)

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    logging.info("Webapp is being run in Dataiku")
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
    logging.info("Webapp is being run outside of Dataiku")
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
    app.enable_dev_tools(debug=True, dev_tools_ui=True)

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
    last_build_date_initial = get_last_build_date(original_ds_name, project)
    last_build_date_ok = True
except:
    last_build_date_initial = ""
    last_build_date_ok = False

def serve_layout():
    return html.Div(children=[
        html.Div(id="refresh-div", children=[
            html.Div(id="data-refresh-message", children="The original dataset has changed. Do you want to refresh? (Your edits are safe.)", style={"display": "inline"}),
            html.Div(id="last-build-date", children=str(last_build_date_initial), style={"display": "none"}), # when the original dataset was last built
            html.Div(id="last-refresh-date", children="", style={"display": "none"}), # when the data in the datatable was last refreshed
            html.Button("Refresh table", id="refresh-btn", n_clicks=0, className="ui compact yellow button", style={"marginLeft": "2em"})
        ], className="ui compact warning message", style={"display": "none"}),

        dcc.Interval(
                id="interval-component-iu",
                interval=10*1000, # in milliseconds
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

data_fresh = True

@app.callback(
    [
        Output("refresh-div", "style"),
        Output("last-build-date", "children")
    ],
    [
        # Changes in the Inputs trigger the callback
        Input("interval-component-iu", "n_intervals"),
        Input("last-refresh-date", "children"),
        # Changes in States don't trigger the callback
        State("refresh-div", "style"),
        State("last-build-date", "children")
    ])
def toggle_refresh_div_visibility(n_intervals, last_refresh_date, refresh_div_style, last_build_date):
    """
    Toggle visibility of refresh div, once...

    * The interval component has fired: check last build date of original dataset and if it's more recent than what we had, display the refresh div
    * The refresh date has changed: hide the refresh div
    """
    style_new = refresh_div_style
    if last_build_date_ok:
        if (callback_context.triggered_id==None): # initial call
            last_build_date_new = last_build_date
            global data_fresh
            if not data_fresh:
                style_new["display"] = "block"
        elif (callback_context.triggered_id=="interval-component-iu"):
            last_build_date_new = str(get_last_build_date(original_ds_name, project))
            if int(last_build_date_new)>int(last_build_date):
                logging.info("The original dataset has changed.")
                last_build_date_new_fmtd = datetime.utcfromtimestamp(int(last_build_date_new)/1000).isoformat()
                last_build_date_fmtd = datetime.utcfromtimestamp(int(last_build_date)/1000).isoformat()
                logging.info(f"""Last build date: {last_build_date_new} ({last_build_date_new_fmtd}) — previously {last_build_date} ({last_build_date_fmtd})""")
                style_new["display"] = "block"
                data_fresh = False
        else: # callback_context must be "last_refresh_date", i.e. that date has changed due to a click on "refresh table"
            logging.info("Datatable has been refreshed -> hiding refresh div")
            last_build_date_new = last_build_date
            style_new["display"] = "none"
            data_fresh = True
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
    logging.info("Refreshing the data...")
    ees.load_data() # this loads the original df again, pivots the editlog and merges edits
    data = ees.get_data_tabulator()
    logging.info("Done.")
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


@server.route("/dash")
def my_dash_app():
    return app.index()

from flask import request, jsonify
@server.route("/flask", methods=['GET', 'POST'])
def dummy_endpoint():
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')
    return jsonify([term])

from json import dumps
from dataikuapi.utils import DataikuStreamedHttpUTF8CSVReader
from pandas import DataFrame
def get_dataframe_filtered(ds_name, filter_column, filter_term, n_results):
    csv_stream = client._perform_raw(
            "GET" , f"/projects/{project_key}/datasets/{ds_name}/data/",
            params = {
                "format" : "tsv-excel-header",
                "filter" : f"""contains(toLowercase(strval("{filter_column}")), toLowercase("{filter_term}"))""",
                "sampling" : dumps({
                    "samplingMethod": "HEAD_SEQUENTIAL",
                    "maxRecords": n_results
                    })
            })
    ds = project.get_dataset(ds_name)
    csv_reader = DataikuStreamedHttpUTF8CSVReader(ds.get_schema()["columns"], csv_stream)
    rows = []
    for row in csv_reader.iter_rows():
        rows.append(row)
    return DataFrame(columns=rows[0], data=rows[1:])

from commons import get_values_from_linked_df
@server.route("/lookup/<linked_ds_name>", methods=['GET', 'POST'])
def my_flask_endpoint(linked_ds_name):
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')
    logging.info(f"""Received a request for dataset "{linked_ds_name}", term "{term}" """)
    response = jsonify({})
    
    # Return data only when it's a linked dataset
    if linked_ds_name in ees.linked_records_df["ds_name"].to_list(): 
        linked_record_row = ees.linked_records_df.loc[ees.linked_records_df["ds_name"]==linked_ds_name]
        linked_ds_lookup_columns = linked_record_row["ds_lookup_columns"][0]
        linked_ds_key = linked_record_row["ds_key"][0]
        linked_ds_label = linked_record_row["ds_label"][0]
        linked_df_filtered = get_dataframe_filtered(linked_ds_name, linked_ds_label, term, 10)
        editor_values_param = get_values_from_linked_df(
                linked_df_filtered, linked_ds_key, linked_ds_label, linked_ds_lookup_columns)
        response = jsonify(editor_values_param)

    return response

from flask import current_app
@server.route('/test')
def test_page():
    return current_app.send_static_file('values_url.html')

logging.info("Webapp OK")
