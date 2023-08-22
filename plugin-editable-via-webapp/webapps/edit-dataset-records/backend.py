# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Imports and variable initializations
# 1. Get webapp parameters (original dataset, primary keys, editable columns, linked records...)
# 2. Instantiate editable event-sourced dataset
# 3. Define webapp layout and components

# 0. Imports and variable initializations
###

import logging
from datetime import datetime
from os import getenv

import dataiku
from commons import get_last_build_date, get_user_identifier
from dash import Dash, Input, Output, State, dcc, html
from dataiku_utils import get_dataframe_filtered
from DatasetSQL import DatasetSQL
from EditableEventSourced import EditableEventSourced
from flask import Flask, current_app, jsonify, make_response, request
from tabulator_utils import get_columns_tabulator, get_values_from_df
from webapp_config_utils import get_linked_records

import dash_tabulator

stylesheets = ["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = [
    "https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js",
    "https://code.jquery.com/jquery-3.5.1.min.js",  # used by inline javascript code found in tabulator_utils (__get_column_tabulator_formatter_linked_record__)
    "https://cdn.jsdelivr.net/npm/luxon@3.0.4/build/global/luxon.min.js",
]

client = dataiku.api_client()
project_key = getenv("DKU_CURRENT_PROJECT_KEY")
project = client.get_project(project_key)


# 1. Get webapp parameters
###

if getenv("DKU_CUSTOM_WEBAPP_CONFIG"):
    run_context = "dataiku"
    # this points to a copy of assets/style.css (which is ignored by Dataiku's Dash)
    stylesheets += [
        "https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/style.css"
    ]
    # same for assets/custom_tabulator.js
    scripts += [
        "https://plugin-editable-via-webapp.s3.eu-west-1.amazonaws.com/custom_tabulator.js"
    ]
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
    if editschema_manual_raw and editschema_manual_raw != "":
        editschema_manual = loads(editschema_manual_raw)
    else:
        editschema_manual = {}

    server = app.server

else:
    logging.basicConfig(level=logging.INFO)
    logging.info("Webapp is being run outside of Dataiku")
    run_context = "local"
    info_display = "block"

    # Get original dataset name as an environment variable
    # Get primary keys and editable column names from the custom fields of that dataset
    from json import load

    original_ds_name = getenv("ORIGINAL_DATASET")
    params = load(open("../../webapp-settings/" + original_ds_name + ".json"))

    editschema_manual = params.get("editschema")
    if not editschema_manual:
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
linked_records = get_linked_records(params, linked_records_count)
authorized_users = params.get("authorized_users")

ees = EditableEventSourced(
    original_ds_name=original_ds_name,
    project_key=project_key,
    primary_keys=primary_keys,
    editable_column_names=editable_column_names,
    linked_records=linked_records,
    editschema_manual=editschema_manual,
    authorized_users=authorized_users,
)


columns = get_columns_tabulator(ees, freeze_editable_columns)

last_build_date_initial = ""
last_build_date_ok = False


def serve_layout():  # This function is called upon loading/refreshing the page in the browser
    global last_build_date_initial, last_build_date_ok
    try:
        last_build_date_initial = get_last_build_date(original_ds_name, project)
        last_build_date_ok = True
    except:
        last_build_date_initial = ""
        last_build_date_ok = False

    # get user's email and check if it's in authorized_users; if not, return a div which says "unauthorized access"
    user_id = get_user_identifier()
    if not authorized_users or user_id in authorized_users:
        return html.Div(
            children=[
                html.Div(
                    id="refresh-div",
                    children=[
                        html.Div(
                            id="data-refresh-message",
                            children="The original dataset has changed, please refresh this page to load it here. (Your edits are safe.)",
                            style={"display": "inline"},
                        ),
                        html.Div(
                            id="last-build-date",
                            children=str(last_build_date_initial),
                            style={"display": "none"},
                        ),  # when the original dataset was last built
                    ],
                    className="ui compact warning message",
                    style={"display": "none"},
                ),
                dcc.Interval(
                    id="interval-component-iu",
                    interval=10 * 1000,  # in milliseconds
                    n_intervals=0,
                ),
                dash_tabulator.DashTabulator(
                    id="datatable",
                    datasetName=original_ds_name,
                    columns=columns,
                    data=ees.get_edited_df().to_dict(
                        "records"
                    ),  # this gets the most up-to-date edited data
                    groupBy=group_column_names,
                ),
                html.Div(
                    id="edit-info",
                    children="Info zone for tabulator",
                    style={"display": info_display},
                ),
            ]
        )
    else:
        return html.Div("Unauthorized")


app.layout = serve_layout

data_fresh = True


@app.callback(
    [Output("refresh-div", "style"), Output("last-build-date", "children")],
    [
        # Changes in the Inputs trigger the callback
        Input("interval-component-iu", "n_intervals"),
        # Changes in States don't trigger the callback
        State("refresh-div", "style"),
        State("last-build-date", "children"),
    ],
    prevent_initial_call=True,
)
def toggle_refresh_div_visibility(n_intervals, refresh_div_style, last_build_date):
    """
    Toggle visibility of refresh div, when the interval component fires: check last build date of original dataset and if it's more recent than what we had, display the refresh div
    """
    global last_build_date_ok
    style_new = refresh_div_style
    if last_build_date_ok:
        last_build_date_new = str(get_last_build_date(original_ds_name, project))
        if int(last_build_date_new) > int(last_build_date):
            logging.info("The original dataset has changed.")
            last_build_date_new_fmtd = datetime.utcfromtimestamp(
                int(last_build_date_new) / 1000
            ).isoformat()
            last_build_date_fmtd = datetime.utcfromtimestamp(
                int(last_build_date) / 1000
            ).isoformat()
            logging.info(
                f"""Last build date: {last_build_date_new} ({last_build_date_new_fmtd}) — previously {last_build_date} ({last_build_date_fmtd})"""
            )
            style_new["display"] = "block"
            data_fresh = False
    else:
        last_build_date_new = last_build_date
    return style_new, last_build_date_new


@app.callback(
    Output("edit-info", "children"),
    Input("datatable", "cellEdited"),
    prevent_initial_call=True,
)
def add_edit(cell):
    """
    Record edit in editlog, once a cell has been edited

    If the cell is in the Reviewed column, we also update values for all other editable columns in the same row (except Comments). The values in these columns are generated by the upstream data flow and subject to change. We record them, in case the user didn't edit them before marking the row as reviewed.
    """
    info = ""
    if cell["field"] == "Reviewed":
        for col in editable_column_names:
            if col != "Comments":
                info += (
                    ees.update_row(
                        primary_keys=cell[
                            "row"
                        ],  # contains values for primary keys — and other columns too, but they'll be discarded
                        column=col,
                        value=cell["row"][col],
                    )
                    + "\n"
                )
    else:
        info = ees.update_row(
            primary_keys=cell["row"], column=cell["field"], value=cell["value"]
        )
    return info


# CRUD endpoints
###


@server.route("/create", methods=["POST"])
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
    user = get_user_identifier()
    ees.create_row(primary_keys_values, column_values)
    response = jsonify({"msg": "New row created"})
    return response


@server.route("/read", methods=["POST"])
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


@server.route("/read-all-edits", methods=["GET"])
def read_all_edits_endpoint():
    """
    Read all rows edited or created via webapp or API

    Returns: CSV-formatted dataset with rows that were created or edited, and values of primary key and editable columns. See remarks of the `read` endpoint.
    """
    response = make_response(ees.get_edited_cells_df_indexed().to_csv())
    response.headers["Content-Disposition"] = (
        "attachment; filename=" + original_ds_name + "_edits.csv"
    )
    response.headers["Content-Type"] = "text/csv"
    response.headers["Cache-Control"] = "no-store"
    return response


@server.route("/update", methods=["GET", "POST"])
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
    if request.method == "POST":
        primary_keys_values = request.get_json().get("primaryKeys")
        column = request.get_json().get("column")
        value = request.get_json().get("value")
    else:
        primary_keys_values = request.args.get("primaryKeys", "")
        column = request.args.get("column", "")
        value = request.args.get("value", "")
    info = ees.update_row(primary_keys_values, column, value)
    response = jsonify({"msg": info})
    return response


@server.route("/delete", methods=["GET", "POST"])
def delete_endpoint():
    """
    Delete a row

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to delete (see read endpoint)

    Returns a message confirming row deletion.
    """
    if request.method == "POST":
        primary_keys = request.get_json().get("primaryKeys")
    else:
        primary_keys = request.args.get("primaryKeys", "")
    info = ees.delete_row(primary_keys)
    response = jsonify({"msg": f"Row deleted"})
    return response


# Label and lookup endpoints used by Tabulator when formatting or editing linked records
###


@server.route("/label/<linked_ds_name>", methods=["GET", "POST"])
def label_endpoint(linked_ds_name):
    """
    Return the label of a row in a linked dataset

    Params:
    - key: value of the primary key identifying the row to read

    Returns: the value of the column defined as label in the linked dataset
    """

    if request.method == "POST":
        key = request.get_json().get("key")
    else:
        key = request.args.get("key", "")
    label = ""

    # Return data only when it's a linked dataset
    for lr in ees.linked_records:
        if linked_ds_name == lr["ds_name"]:
            linked_ds_key = lr["ds_key"]
            linked_ds_label = lr["ds_label"]
            # Return label only if a label column is defined (and different from the key column)
            if key != "" and linked_ds_label and linked_ds_label != linked_ds_key:
                if lr.get("ds"):
                    label = lr["ds"].get_cell_value_sql_query(
                        linked_ds_key, key, linked_ds_label
                    )
                else:
                    linked_df = lr["df"].set_index(linked_ds_key)
                    label = linked_df.loc[key, linked_ds_label]
            else:
                label = key
    return label


@server.route("/lookup/<linked_ds_name>", methods=["GET", "POST"])
def lookup_endpoint(linked_ds_name):
    """
    Get label and lookup values in a linked dataset, matching a search term.

    This endpoint is used by Tabulator when editing a linked record. The values it returns are read by the `itemFormatter` function of the Tabulator table, which displays a dropdown list of linked records whose labels match the search term.
    """
    if request.method == "POST":
        term = request.get_json().get("term")
    else:
        term = request.args.get("term", "")
    logging.info(
        f"""Received a request for dataset "{linked_ds_name}", term "{term}" ({len(term)} characters)"""
    )
    response = jsonify({})

    # Return data only when it's a linked dataset
    n_results = 10
    for lr in ees.linked_records:
        if linked_ds_name == lr["ds_name"]:
            linked_ds_key = lr["ds_key"]
            linked_ds_label = lr["ds_label"]
            linked_ds_lookup_columns = lr["ds_lookup_columns"]
            if lr.get("ds"):
                # Use the Dataiku API to filter the dataset
                linked_df_filtered = get_dataframe_filtered(
                    linked_ds_name,
                    project_key,
                    linked_ds_label,
                    term.strip().lower(),
                    n_results,
                )
            else:
                linked_df = lr["df"].set_index(linked_ds_key)
                if term == "":
                    n_results = 100  # show more options if no search term is provided
                    linked_df_filtered = linked_df.head(n_results).reset_index()
                else:
                    # Filter linked_df for rows whose label contains the search term
                    linked_df_filtered = (
                        linked_df[
                            linked_df[linked_ds_label]
                            .str.lower()
                            .str.contains(term.strip().lower())
                        ]
                        .head(n_results)
                        .reset_index()
                    )
                logging.debug(f"Found {linked_df_filtered.size} entries")
                response = linked_df_filtered.to_json(orient="index")

        logging.debug(f"Found {linked_df_filtered.size} entries")
        editor_values_param = get_values_from_df(
            linked_df_filtered, linked_ds_key, linked_ds_label, linked_ds_lookup_columns
        )
        response = jsonify(editor_values_param)
    else:
        logging.info(f"""Dataset {linked_ds_name} is not a linked dataset!""")

    return response


# Dummy endpoints
###


@server.route("/dash")
def my_dash_app():
    return app.index()


@server.route("/echo", methods=["GET", "POST"])
def echo_endpoint():
    if request.method == "POST":
        term = request.get_json().get("term")
    else:
        term = request.args.get("term", "")
    return jsonify([term])


@server.route("/static")
def static_page():
    return current_app.send_static_file("values_url.html")


logging.info("Webapp OK")
