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
    params = load(open("../../../example-settings/" + original_ds_name + ".json"))

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
