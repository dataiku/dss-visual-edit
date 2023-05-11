# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Imports and variable initializations
# 1. Get webapp parameters (original dataset, primary keys, editable columns, linked records...)
# 2. Instantiate editable event-sourced dataset
# 3. Define webapp layout and components

# %% 0. Imports and variable initializations
###

from commons import get_values_from_linked_df, get_user_identifier, get_last_build_date
from tabulator_utils import get_columns_tabulator
from json import dumps
from flask import Flask, request, jsonify, current_app, make_response
from pandas import DataFrame
from dataikuapi.utils import DataikuStreamedHttpUTF8CSVReader
from datetime import datetime
import dash_tabulator
from EditableEventSourced import EditableEventSourced
import logging
from dataiku import api_client
from os import getenv
from dash import Dash, html, dcc, Input, Output, State, callback_context

stylesheets = [
    "https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = ["https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js",
           "https://cdn.jsdelivr.net/npm/luxon@3.0.4/build/global/luxon.min.js"]
client = api_client()
project_key = getenv("DKU_CURRENT_PROJECT_KEY")
project = client.get_project(project_key)


# %% 1. Get webapp parameters
###

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    run_context = "dataiku"
    # this points to a copy of assets/style.css (which is ignored by Dataiku's Dash)
    stylesheets += ["https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/style.css"]
    # same for assets/custom_tabulator.js
    scripts += ["https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/custom_tabulator.js"]
    info_display = "none"

    from dataiku.customwebapp import get_webapp_config
    original_ds_name = get_webapp_config().get("original_dataset")
    params = get_webapp_config()
    if bool(params.get("debug_mode")):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.info("Webapp is being run in Dataiku")

    from json import loads
    editschema_manual_raw = params.get("editschema")
    if (editschema_manual_raw and editschema_manual_raw != ""):
        editschema_manual = loads(editschema_manual_raw)
    else:
        editschema_manual = {}

    server = app.server

else:
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Webapp is being run outside of Dataiku")
    run_context = "local"
    info_display = "block"

    # Get original dataset name as an environment variable
    # Get primary keys and editable column names from the custom fields of that dataset
    from json import load
    original_ds_name = getenv("ORIGINAL_DATASET")
    params = load(open("../../../example-settings/" +
                  original_ds_name + ".json"))

    editschema_manual = params.get("editschema")
    if (not editschema_manual):
        editschema_manual = {}

    server = Flask(__name__)
    app = Dash(__name__, server=server)
    app.enable_dev_tools(debug=True, dev_tools_ui=True)

app.config.external_stylesheets = stylesheets
app.config.external_scripts = scripts

primary_keys = params.get("primary_keys")
editable_column_names = params.get("editable_column_names")
freeze_editable_columns = params.get("freeze_editable_columns")
group_column_names = params.get("group_column_names")
linked_records_count = params.get("linked_records_count")
linked_records = []
if (linked_records_count > 0):
    for c in range(1, linked_records_count+1):
        name = params.get(f"linked_record_name_{c}")
        ds_name = params.get(f"linked_record_ds_name_{c}")
        ds_key = params.get(f"linked_record_key_{c}")
        ds_label = params.get(f"linked_record_label_column_{c}")
        ds_lookup_columns = params.get(f"linked_record_lookup_columns_{c}")
        if not ds_label:
            ds_label = ds_key
        if not ds_lookup_columns:
            ds_lookup_columns = []
        linked_records.append(
            {
                "name": name,
                "ds_name": ds_name,
                "ds_key": ds_key,
                "ds_label": ds_label,
                "ds_lookup_columns": ds_lookup_columns
            }
        )

# %% 2. Instantiate editable event-sourced dataset
###

ees = EditableEventSourced(original_ds_name, primary_keys,
                           editable_column_names, linked_records, editschema_manual)

# %% 3. Define webapp layout and components
###

if run_context == "local":
    user = "local"
else:
    user = get_user_identifier()

columns = get_columns_tabulator(ees, freeze_editable_columns)

last_build_date_initial = ""
last_build_date_ok = False

def serve_layout():
    global last_build_date_initial, last_build_date_ok
    try:
        last_build_date_initial = get_last_build_date(
            original_ds_name, project)
        last_build_date_ok = True
    except:
        last_build_date_initial = ""
        last_build_date_ok = False

    # This function is called upon loading/refreshing the page in the browser
    return html.Div(children=[
        html.Div(id="refresh-div", children=[
            html.Div(id="data-refresh-message",
                     children="The original dataset has changed, please refresh this page to load it here. (Your edits are safe.)", style={"display": "inline"}),
            html.Div(id="last-build-date", children=str(last_build_date_initial),
                     style={"display": "none"})  # when the original dataset was last built
        ], className="ui compact warning message", style={"display": "none"}),

        dcc.Interval(
            id="interval-component-iu",
            interval=10*1000,  # in milliseconds
            n_intervals=0
        ),

        dash_tabulator.DashTabulator(
            id="datatable",
            columns=columns,
            data=ees.get_edited_df().to_dict('records'), # this gets the most up-to-date edited data
            groupBy=group_column_names
        ),

        html.Div(id="edit-info", children="Info zone for tabulator",
                 style={"display": info_display})
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
        # Changes in States don't trigger the callback
        State("refresh-div", "style"),
        State("last-build-date", "children")
    ], prevent_initial_call=True)
def toggle_refresh_div_visibility(n_intervals, refresh_div_style, last_build_date):
    """
    Toggle visibility of refresh div, when the interval component fires: check last build date of original dataset and if it's more recent than what we had, display the refresh div
    """
    global last_build_date_ok
    style_new = refresh_div_style
    if last_build_date_ok:
        last_build_date_new = str(
            get_last_build_date(original_ds_name, project))
        if int(last_build_date_new) > int(last_build_date):
            logging.info("The original dataset has changed.")
            last_build_date_new_fmtd = datetime.utcfromtimestamp(
                int(last_build_date_new)/1000).isoformat()
            last_build_date_fmtd = datetime.utcfromtimestamp(
                int(last_build_date)/1000).isoformat()
            logging.info(
                f"""Last build date: {last_build_date_new} ({last_build_date_new_fmtd}) — previously {last_build_date} ({last_build_date_fmtd})""")
            style_new["display"] = "block"
            data_fresh = False
    else:
        last_build_date_new = last_build_date
    return style_new, last_build_date_new


@app.callback(
    Output("edit-info", "children"),
    Input("datatable", "cellEdited"),
    prevent_initial_call=True)
def add_edit(cell):
    """
    Record edit in editlog, once a cell has been edited
    """
    return ees.update_row(cell["row"], cell["column"], cell["value"], user) # cell["row"] contains values for primary keys — and other columns too, but they'll be discarded


# CRUD endpoints
###

@server.route("/create", methods=['POST'])
def create_endpoint():
    """
    Create a new row.

    Params:
    - primaryKeys: dict containing values for all primary keys defined in the initial data editing setup; the set of values must be unique.
    - columnValues: dict containing values for all other columns.
    
    Example request JSON:
    ```json
    {
        "primaryKeys": {
            "id": "My new unique id"
        },
        "columnValues": {
            "col1": "hey",
            "col2": 42,
            "col3": true
        }
    }
    ```
    
    Returns a message confirming row creation.

    Note: this method doesn't implement data validation / it doesn't check that the values are allowed for the specified columns.
    """
    primary_keys_values = request.get_json().get("primaryKeys")
    column_values = request.get_json().get("columnValues")
    # TODO: check set of primary key values is unique?
    ees.create_row(primary_keys_values, column_values, user)
    response = jsonify({
        "msg": "New row created"
    })
    return response

@server.route("/read", methods=['POST'])
def read_endpoint():
    """
    Read a row that was created or edited via webapp or API

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to read

    Example request JSON:
    ```json
    {
        "primaryKeys": {
            "key1": "cat",
            "key2": "2022-12-21",
        }
    }
    ```

    Returns: JSON representation of the values of editable columns.
    - If some rows of the dataset were created, then by definition all columns are editable (including primary keys) .
    - If no row was created, editable columns are those defined in the initial data editing setup.
    - Example API response:
    ```json
    {
        "columnValues": {
            "col1": "hey",
            "col2": 42,
            "col3": true
        }
    }
    ```
    """
    primary_keys_values = request.get_json().get("primaryKeys")
    response = ees.get_row(primary_keys_values).to_json()
    return response

@server.route("/read-all-edits", methods=['GET'])
def read_all_edits_endpoint():
    """
    Read all rows edited or created via webapp or API

    Returns: CSV-formatted dataset with rows that were created or edited, and values of primary key and editable columns. See remarks of the `read` endpoint.
    """
    response = make_response(ees.get_edited_cells_df_indexed().to_csv())
    response.headers["Content-Disposition"] = "attachment; filename=" + original_ds_name + "_edits.csv"
    response.headers["Content-Type"] = "text/csv"
    response.headers["Cache-Control"] = "no-store"
    return response

@server.route("/update", methods=['GET', 'POST'])
def update_endpoint():
    """
    Update a row

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to update (see read endpoint)
    - column: name of the column to update
    - value: value to set for the cell identified by key and column

    Example responses:
    - if column is an editable column:
    ```json
    { "msg": "Updated column _column_ where _list of primary key names_ is _primaryKeys_. New value: _value_." }
    ````
    - otherwise:
    ```json
    { "msg": "_column_ isn't an editable column" }
    ```

    Note: this method doesn't implement data validation / it doesn't check that the value is allowed for the specified column.
    """
    if request.method == 'POST':
        primary_keys_values = request.get_json().get("primaryKeys")
        column = request.get_json().get("column")
        value = request.get_json().get("value")
    else:
        primary_keys_values = request.args.get("primaryKeys", "")
        column = request.args.get("column", "")
        value = request.args.get("value", "")
    info = ees.update_row(primary_keys_values, column, value, user)
    response = jsonify({"msg": info})
    return response

@server.route("/delete", methods=['GET', 'POST'])
def delete_endpoint():
    """
    Delete a row

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to delete (see read endpoint)

    Returns a message confirming row deletion.
    """
    if request.method == 'POST':
        primary_keys = request.get_json().get("primaryKeys")
    else:
        primary_keys = request.args.get("primaryKeys", "")
    info = ees.delete_row(primary_keys, user)
    response = jsonify({"msg": f"Row deleted"})
    return response


# Lookup endpoint
###

def get_dataframe_filtered(ds_name, filter_column, filter_term, n_results):
    logging.debug("Passing request to Dataiku's `data` API endpoint")
    csv_stream = client._perform_raw(
        "GET", f"/projects/{project_key}/datasets/{ds_name}/data/",
        params={
            "format": "tsv-excel-header",
            "filter": f"""startsWith(toLowercase(strval("{filter_column}")), "{filter_term}")""",
            "sampling": dumps({
                "samplingMethod": "HEAD_SEQUENTIAL",
                "maxRecords": n_results
            })
        })
    ds = project.get_dataset(ds_name)
    csv_reader = DataikuStreamedHttpUTF8CSVReader(
        ds.get_schema()["columns"], csv_stream)
    rows = []
    logging.debug("Reading streamed CSV")
    for row in csv_reader.iter_rows():
        rows.append(row)
    logging.debug("Done")
    return DataFrame(columns=rows[0], data=rows[1:])

@server.route("/lookup/<linked_ds_name>", methods=['GET', 'POST'])
def lookup_endpoint(linked_ds_name):
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')
    logging.info(
        f"""Received a request for dataset "{linked_ds_name}", term "{term}" ({len(term)} characters)""")
    response = jsonify({})

    # Return data only when it's a linked dataset
    if linked_ds_name in ees.linked_records_df["ds_name"].to_list():
        linked_record_row = ees.linked_records_df.loc[ees.linked_records_df["ds_name"] == linked_ds_name]
        linked_ds_lookup_columns = linked_record_row["ds_lookup_columns"][0]
        linked_ds_key = linked_record_row["ds_key"][0]
        linked_ds_label = linked_record_row["ds_label"][0]
        linked_df_filtered = get_dataframe_filtered(
            linked_ds_name, linked_ds_label, term.strip().lower(), 50)
        logging.debug(f"Found {linked_df_filtered.size} entries")
        editor_values_param = get_values_from_linked_df(
            linked_df_filtered, linked_ds_key, linked_ds_label, linked_ds_lookup_columns)
        response = jsonify(editor_values_param)
    else:
        logging.info(f"""Dataset {linked_ds_name} is not a linked dataset!""")

    return response


# Dummy endpoints
###

@server.route("/dash")
def my_dash_app():
    return app.index()

@server.route("/echo", methods=['GET', 'POST'])
def echo_endpoint():
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')
    return jsonify([term])

@server.route('/static')
def static_page():
    return current_app.send_static_file('values_url.html')


logging.info("Webapp OK")
