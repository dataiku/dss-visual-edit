# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
#
# This code is structured as follows:
# 0. Imports and variable initializations.
# 1. Get webapp parameters (original dataset, primary keys, editable columns, linked records...).
#    Depending if it is running inside DSS or not, parameters are fetched from a launch.json file (outside DSS) or an environment variable (inside).
#    In case we start the app outside DSS, we start a flask web server.
# 2. Instantiate editable event-sourced dataset.
# 3. Define Dash webapp layout and components.
from __future__ import annotations
import logging
from webapp.config.models import LinkedRecord
import webapp.logging.setup  # noqa: F401 necessary to setup logging basicconfig before dataiku module sets a default config
from datetime import datetime
from pandas import concat
from pandas.api.types import is_integer_dtype, is_float_dtype
from commons import get_last_build_date, try_get_user_identifier
from dash import Dash, Input, Output, State, dcc, html
from dataiku.core.schema_handling import CASTERS
from dataiku_utils import (
    get_linked_dataframe_filtered,
    get_linked_label,
    client as dss_client,
)
from DataEditor import (
    EditFreezed,
    EditSuccess,
    EditFailure,
    EditUnauthorized,
    DataEditor,
)
from flask import Flask, jsonify, make_response, request
from tabulator_utils import get_columns_tabulator, get_formatted_items_from_linked_df

from webapp.config.loader import WebAppConfig

import dash_tabulator

webapp_config = WebAppConfig()

logging.info(f"Web app starting inside DSS:{webapp_config.running_in_dss}.")

if webapp_config.running_in_dss:
    server = app.server
else:
    server = Flask(__name__)
    app = Dash(__name__, server=server)
    app.enable_dev_tools(debug=True, dev_tools_ui=True)

project_key = webapp_config.project_key
project = dss_client.get_project(project_key)

editable_column_names = webapp_config.editable_column_names
authorized_users = webapp_config.authorized_users
freeze_edits = webapp_config.freeze_edits
original_ds_name = webapp_config.original_ds_name

de = DataEditor(
    original_ds_name=original_ds_name,
    project_key=project_key,
    primary_keys=webapp_config.primary_keys,
    editable_column_names=editable_column_names,
    linked_records=webapp_config.linked_records,
    editschema_manual=webapp_config.editschema_manual,
    authorized_users=authorized_users,
    freeze_edits=freeze_edits,
)


columns = get_columns_tabulator(
    de, webapp_config.show_header_filter, webapp_config.freeze_editable_columns
)

last_build_date_initial = ""
last_build_date_ok = False


def __edit_result_to_message__(
    r: EditSuccess | EditFailure | EditUnauthorized,
) -> str:
    if isinstance(r, EditSuccess):
        return "Row successfully updated"
    elif isinstance(r, EditFailure):
        return r.message
    elif isinstance(r, EditUnauthorized):
        return "Unauthorized"
    elif isinstance(r, EditFreezed):
        return "Edits are disabled."
    else:
        return "Unexpected update result"


def serve_layout():  # This function is called upon loading/refreshing the page in the browser
    global last_build_date_initial, last_build_date_ok
    try:
        last_build_date_initial = get_last_build_date(original_ds_name, project)
        last_build_date_ok = True
    except Exception:
        logging.warning(
            f"Failed to get last build date of {original_ds_name}. Serve layout without this information.",
            exc_info=True,
        )
        last_build_date_initial = ""
        last_build_date_ok = False

    user_id = try_get_user_identifier()

    # no specific authorized users configured or match in the list of authorized users grant you access to the layout.
    if not authorized_users or (user_id is not None and user_id in authorized_users):
        logging.debug(f"User '{user_id}' is being served layout.")
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
                    data=de.get_edited_df().to_dict(
                        "records"
                    ),  # this gets the most up-to-date edited data
                    groupBy=webapp_config.group_column_names,
                ),
                html.Div(
                    id="edit-info",
                    children="Info zone for tabulator",
                    style={
                        "display": "none" if webapp_config.running_in_dss else "block"
                    },
                ),
            ]
        )
    # specific authorized users configured but failure to get current user info.
    elif authorized_users and user_id is None:
        return html.Div(
            "Failed to fetch your user information. Try refreshing the page."
        )
    else:
        return html.Div("Unauthorized")


app.layout = serve_layout


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

    If the cell is in a validation column, we also update values for all other editable columns in the same row (except Comments). The values in these columns are generated by the upstream data flow and subject to change. We record them, in case the user didn't edit them before marking the row as valid.
    """

    row_dic = cell["row"]
    updated_field = cell["field"]
    updated_value = cell["value"]
    results = de.update_row(row_dic, updated_field, updated_value)

    info = ""
    for res in results:
        info += __edit_result_to_message__(res) + "\n"

    return info


# CRUD endpoints
###


@server.route("/create", methods=["POST"])
def create_endpoint():
    """
    Create a new row.

    Params:
    - primaryKeys: dict containing values for all primary keys defined in the initial Visual Edit setup; the set of values must be unique.
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
    de.create_row(primary_keys_values, column_values)
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
    - If no row was created, editable columns are those defined in the initial Visual Edit setup.
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
    response = de.get_row(primary_keys_values).to_json()
    return response


@server.route("/read-all-edits", methods=["GET"])
def read_all_edits_endpoint():
    """
    Read all rows edited or created via webapp or API

    Returns: CSV-formatted dataset with rows that were created or edited, and values of primary key and editable columns. See remarks of the `read` endpoint.
    """
    response = make_response(de.get_edited_cells_df_indexed().to_csv())
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
    results = de.update_row(primary_keys_values, column, value)
    info = ""
    for res in results:
        info += __edit_result_to_message__(res) + "\n"
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
    result = de.delete_row(primary_keys)
    response = jsonify({"msg": __edit_result_to_message__(result)})
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

    # Get request parameters
    if request.method == "POST":
        key = request.get_json().get("key")
    else:
        key = request.args.get("key", "")

    # Find the linked record whose linked dataset is requested
    linked_record: LinkedRecord | None = None
    for lr in de.linked_records:
        if linked_ds_name == lr.ds_name:
            linked_record = lr
            break
    if linked_record is None:
        return "Unknown linked dataset.", 404

    # Return data only when linked_ds_name corresponds to a linked dataset; if we've reached this point in the code, it means that this is the case

    # Cast provided key value into appropriate type (necessary for integers for example)
    linked_key_type = de.schema_columns_df.loc[linked_record.name, "type"]
    linked_key_dtype = CASTERS.get(linked_key_type)
    try:
        if linked_key_dtype and is_integer_dtype(linked_key_dtype):
            key = int(key)
        if linked_key_dtype and is_float_dtype(linked_key_dtype):
            key = float(key)
    except Exception:
        return "Invalid key type.", 400

    return get_linked_label(linked_record, key)


@server.route("/lookup/<linked_ds_name>", methods=["GET", "POST"])
def lookup_endpoint(linked_ds_name):
    """
    Get label and lookup values in a linked dataset

    This endpoint is used by Tabulator when editing a linked record. The values it returns are read by the `itemFormatter` function of the Tabulator table, which displays a dropdown list of linked records whose labels match the search term.

    If a search term is provided, return a list of options that match this term. Otherwise, return a single option corresponding to the provided key.

    Params:
    - key: the primary key for the current linked record
    - term: the search term to filter linked records

    Returns: a list of matching options
    """

    # Get request parameters
    if request.method == "POST":
        key = request.get_json().get("key")
        term = request.get_json().get("term")
    else:
        key = request.args.get("key", "")
        term = request.args.get("term", "")
    term = term.strip().lower()
    logging.info(
        f"""Received a request to get options from linked dataset "{linked_ds_name}" matching key "{key}" or search term "{term}" ({len(term)} characters)"""
    )

    # Find the linked record whose linked dataset is requested
    linked_record: LinkedRecord | None = None
    for lr in de.linked_records:
        if linked_ds_name == lr.ds_name:
            linked_record = lr
            break
    if linked_record is None:
        return "Unknown linked dataset.", 404

    # Return data only when it's a linked dataset; if we've reached this point, it means that this is the case

    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label
    linked_ds_lookup_columns = linked_record.ds_lookup_columns

    if term != "":
        # when a search term is provided, show a limited number of options matching this term
        n_options = 10
    else:
        # otherwise, show many options to choose from
        n_options = 1000

    # Get a dataframe of the linked dataset filtered by the search term or the key
    linked_df_filtered = get_linked_dataframe_filtered(
        linked_record=linked_record,
        project_key=project_key,
        filter_term=term,
        n_results=n_options,
    )

    # when a key is provided, make sure to include an option corresponding to this key
    # if not already the case, get the label for this key and use it as search term to filter the linked dataframe
    if key != "" and key != "null":
        linked_row = linked_df_filtered[linked_df_filtered[linked_ds_key] == key]
        if linked_row.empty:
            label = get_linked_label(linked_record, key).lower()
            linked_row = get_linked_dataframe_filtered(
                linked_record=linked_record,
                project_key=project_key,
                filter_term=label,
                n_results=1,
            )
            linked_df_filtered = concat([linked_row, linked_df_filtered])

    editor_values_param = get_formatted_items_from_linked_df(
        linked_df=linked_df_filtered,
        key_col=linked_ds_key,
        label_col=linked_ds_label,
        lookup_cols=linked_ds_lookup_columns,
    )
    return jsonify(editor_values_param)


logging.info("Webapp OK")
