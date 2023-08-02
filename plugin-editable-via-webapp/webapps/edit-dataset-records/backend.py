# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Imports and variable initializations
# 1. Get webapp parameters (original dataset, primary keys, editable columns, linked records...)
# 3. Define webapp layout and components

# 0. Imports and variable initializations
###

import logging
from os import getenv

import dataiku
from commons import get_user_identifier
from dash import Dash, Input, Output, State, dcc, html
from dataiku_utils import get_dataframe_filtered
from EditableEventSourced import EditableEventSourced
from DataTableAIO import DataTableAIO
from flask import Flask, current_app, jsonify, make_response, request
from linked_records_blueprint import linked_records_blueprint
from webapp_config_utils import get_linked_records

stylesheets = ["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = [
    "https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js",
    "https://code.jquery.com/jquery-3.5.1.min.js",  # used by inline javascript code found in tabulator_utils (__get_column_tabulator_formatter_linked_record__)
    "https://cdn.jsdelivr.net/npm/luxon@3.0.4/build/global/luxon.min.js",
]
logger = logging.getLogger(__name__)

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
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.info("Webapp is being run in Dataiku")

    from json import loads

    editschema_manual_raw = params.get("editschema")
    if editschema_manual_raw and editschema_manual_raw != "":
        editschema_manual = loads(editschema_manual_raw)
    else:
        editschema_manual = {}

    server = app.server
    server.register_blueprint(linked_records_blueprint)

else:
    logger.setLevel(logging.DEBUG)
    logger.info("Webapp is being run outside of Dataiku")
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
    server.register_blueprint(linked_records_blueprint)
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

# TODO: replace this with a call to initialize custom fields based on the parameters below
ees = EditableEventSourced(
    original_ds_name=original_ds_name,
    primary_keys=primary_keys,
    editable_column_names=editable_column_names,
    linked_records=linked_records,
    editschema_manual=editschema_manual,
    authorized_users=authorized_users,
)


def serve_layout():  # This function is called upon loading/refreshing the page in the browser
    # get user's email and check if it's in authorized_users; if not, return a div which says "unauthorized access"
    user_id = get_user_identifier()
    if not authorized_users or user_id in authorized_users:
        return html.Div(
            [
                DataTableAIO(
                    aio_id="dt",
                    ds_name=original_ds_name,
                    freeze_editable_columns=freeze_editable_columns,
                )
            ]
        )
    else:
        return html.Div("Unauthorized")


app.layout = serve_layout


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


logger.info("Webapp OK")
