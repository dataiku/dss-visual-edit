# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records
from __future__ import annotations
import logging
from webapp.config.models import LinkedRecord
import webapp.logging.setup  # noqa: F401 necessary to setup logging basicconfig before dataiku module sets a default config
from datetime import datetime
from pandas.api.types import is_integer_dtype, is_float_dtype
from commons import get_last_build_date, try_get_user_identifier
from dash import Dash, Input, Output, State, dcc, html
from dataiku_utils import get_dataframe_filtered, client as dss_client
from EditableEventSourced import (
    EditSuccess,
    EditFailure,
    EditUnauthorized,
    EditableEventSourced,
)
from flask import Flask, jsonify, make_response, request
from tabulator_utils import get_columns_tabulator, get_values_from_df

from webapp.config.loader import WebAppConfig

import dash_tabulator

webapp_config = WebAppConfig()

logging.info(f"Web app starting inside DSS:{webapp_config.running_in_dss}.")

stylesheets = ["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"]
scripts = [
    "https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js",
    "https://code.jquery.com/jquery-3.5.1.min.js",  # used by inline javascript code found in tabulator_utils (__get_column_tabulator_formatter_linked_record__)
    "https://cdn.jsdelivr.net/npm/luxon@3.0.4/build/global/luxon.min.js",
]

if webapp_config.running_in_dss:
    server = app.server
else:
    server = Flask(__name__)
    app = Dash(__name__, server=server)
    app.enable_dev_tools(debug=True, dev_tools_ui=True)

app.config.external_stylesheets = stylesheets
app.config.external_scripts = scripts

project_key = webapp_config.project_key
project = dss_client.get_project(project_key)

editable_column_names = webapp_config.editable_column_names
authorized_users = webapp_config.authorized_users
original_ds_name = webapp_config.original_ds_name

ees = EditableEventSourced(
    original_ds_name=original_ds_name,
    project_key=project_key,
    primary_keys=webapp_config.primary_keys,
    editable_column_names=editable_column_names,
    linked_records=webapp_config.linked_records,
    editschema_manual=webapp_config.editschema_manual,
    authorized_users=authorized_users,
)


columns = get_columns_tabulator(ees, webapp_config.freeze_editable_columns)

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
                    data=ees.get_edited_df().to_dict(
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

    If the cell is in the Reviewed column, we also update values for all other editable columns in the same row (except Comments). The values in these columns are generated by the upstream data flow and subject to change. We record them, in case the user didn't edit them before marking the row as reviewed.
    """

    info = ""
    if cell["field"] == "Reviewed" or cell["field"] == "reviewed":
        for col in editable_column_names:
            if col != "Comments" and col != "comments":
                result = ees.update_row(
                    primary_keys=cell[
                        "row"
                    ],  # contains values for primary keys — and other columns too, but they'll be discarded
                    column=col,
                    value=cell["row"][col],
                )
                info += __edit_result_to_message__(result) + "\n"
    else:
        result = ees.update_row(
            primary_keys=cell["row"], column=cell["field"], value=cell["value"]
        )
        info = __edit_result_to_message__(result)
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
    response = jsonify({"msg": __edit_result_to_message__(info)})
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
    result = ees.delete_row(primary_keys)
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

    if request.method == "POST":
        key = request.get_json().get("key")
    else:
        key = request.args.get("key", "")
    label = ""

    linked_record: LinkedRecord | None = None
    for lr in ees.linked_records:
        if linked_ds_name == lr.ds_name:
            linked_record = lr
            break

    if linked_record is None:
        return "Unnknown linked dataset.", 404

    # Return data only when it's a linked dataset
    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label

    # Cast provided key value into appropriate type, necessary for integers for example.
    original_df, primary_keys, display_columns, editable_columns = ees.get_original_df()

    key_dtype = original_df[linked_record.name].dtype
    try:
        if is_integer_dtype(key_dtype):
            key = int(key)
        if is_float_dtype(key_dtype):
            key = float(key)
    except Exception:
        return "Invalid key type.", 400

    # Return label only if a label column is defined (and different from the key column)
    if key != "" and linked_ds_label and linked_ds_label != linked_ds_key:
        if linked_record.ds:
            try:
                label = linked_record.ds.get_cell_value_sql_query(
                    linked_ds_key, key, linked_ds_label
                )
            except Exception:
                return "Something went wrong fetching label of linked value.", 500
        else:
            linked_record_df = linked_record.df
            if linked_record_df is None:
                return "Something went wrong. Try restarting the backend.", 500

            linked_df = linked_record_df.set_index(linked_ds_key)
            try:
                label = linked_df.loc[key, linked_ds_label]
            except Exception:
                return label
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

    term = term.strip().lower()
    if term != "":
        n_results = (
            10  # show a limited number of options when a search term is provided
        )
    else:
        n_results = 1000  # show more options if no search term is provided

    linked_record: LinkedRecord | None = None
    for lr in ees.linked_records:
        if linked_ds_name == lr.ds_name:
            linked_record = lr
            break

    if linked_record is None:
        return "Unknown linked dataset.", 404

    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label
    linked_ds_lookup_columns = linked_record.ds_lookup_columns
    if linked_record.ds:
        # Use the Dataiku API to filter the dataset
        linked_df_filtered = get_dataframe_filtered(
            linked_ds_name,
            project_key,
            linked_ds_label,
            term,
            n_results,
        )
    else:
        linked_df = linked_record.df  # note: this is already capped to 1000 rows
        if linked_df is None:
            return "Something went wrong. Try restarting the backend.", 500
        if term == "":
            linked_df_filtered = linked_df
        else:
            # Filter linked_df for rows whose label contains the search term
            linked_df_filtered = linked_df[
                linked_df[linked_ds_label].str.lower().str.contains(term)
            ].head(n_results)

    logging.debug(f"Found {linked_df_filtered.size} entries")
    editor_values_param = get_values_from_df(
        linked_df_filtered, linked_ds_key, linked_ds_label, linked_ds_lookup_columns
    )
    return jsonify(editor_values_param)


logging.info("Webapp OK")
