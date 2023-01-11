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

from commons import get_values_from_linked_df, get_user_details, get_last_build_date
from json import dumps
from flask import Flask, request, jsonify, current_app
from pandas import DataFrame
from dataikuapi.utils import DataikuStreamedHttpUTF8CSVReader
from datetime import datetime
import dash_tabulator
from EditableEventSourced import EditableEventSourced
import logging
from dataiku import api_client
from os import getenv
from dash import Dash, html, dcc, Input, Output, State, ctx

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


columns = ees.get_columns_tabulator(freeze_editable_columns)

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


    main_tabulator = dash_tabulator.DashTabulator(
        id="datatable",
        columns=columns,
        data=ees.get_data_tabulator(),  # this gets the most up-to-date edited data
        groupBy=group_column_names
    )

    bulk_edit_dialog = get_bulk_edit_dialog([])

    layout = html.Div(
        id="main-container",
        children=[
            html.Div(
                id="main-tabulator",
                children=[
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

                    html.Button(
                        children="Edit 0 items",
                        disabled=True,
                        id="bulk-edit-btn",
                        n_clicks=0,
                        style={
                            'marginBottom': '15px',
                        }
                    ),

                    main_tabulator,

                    html.Div(id="edit-info", children="Info zone for tabulator",
                            style={"display": info_display}),

                ]
            ),
            bulk_edit_dialog
    ])
    # This function is called upon loading/refreshing the page in the browser
    
    return layout

def get_bulk_edit_tabulator_data(selected_rows):
    editable_columns = []
    for c in columns:
        if c.get("editor"):
            editable_columns.append(c)

    values_per_columns = {}

    for c in editable_columns:
        column_name = c["field"]
        if not column_name in values_per_columns:
            values_per_columns[column_name] = set()

        for r in selected_rows:
            values_per_columns[column_name].add(
                r.get(column_name)
            )

    bulk_edit_tabulator_data = []
 
    for c in editable_columns:
        n_fields = len(values_per_columns[c["field"]])
        if n_fields == 0:
            new_row_value = "No value"
        elif n_fields == 1:
            new_row_value = list(values_per_columns[c["field"]])[0]
        else:
            new_row_value = "Multiple values"

        new_row = {
            "field": c["title"],
            "new_value": new_row_value
        }
        bulk_edit_tabulator_data.append(new_row)
    
    return bulk_edit_tabulator_data

def get_bulk_edit_tabulator_columns():
    new_value_editor = ees.__get_bulk_edit_column_editor__(columns)
    new_value_column = {
        "field": "new_value", 
        "title": "New value",
    }
    new_value_column.update(new_value_editor)

    bulk_edit_columns = [
        {
            "field": "field", 
            "title": "Field",
        },
        new_value_column
    ]

    return bulk_edit_columns


def build_bulk_edit_tabulator(selected_rows=None) -> dash_tabulator.DashTabulator:
    if selected_rows is None:
        selected_rows = []

    bulk_edit_columns = get_bulk_edit_tabulator_columns()
    bulk_edit_data = get_bulk_edit_tabulator_data([])

    bulk_edit_tabulator = dash_tabulator.DashTabulator(
        id="bulk-edit-datatable",
        columns=bulk_edit_columns,
        data=bulk_edit_data,
    )

    return bulk_edit_tabulator
    

def get_bulk_edit_dialog(items_to_edit):
    bulk_edit_tabulator = build_bulk_edit_tabulator()
    return html.Div(
        id="bulk-edit-dialog-wrapper",
        children=[
            html.Dialog(
                id="bulk-edit-dialog",
                children=[
                    html.H3(
                        id="bulk-edit-dialog-title",
                        children=f"Editing 0 rows"
                    ),
                    bulk_edit_tabulator,
                    html.Button(
                        children="Apply",
                        id="apply-bulk-edit",
                        n_clicks=0,
                        style={
                            'marginTop': '15px',
                        }
                    ),
                ],
                open=False,
                style={
                    "top": "50%",
                    "transform": "translate(0, -50%)",
                    "zIndex": "11",
                    "cursor": "default"
                },
                n_clicks=0
            )
        ],
        style={
            "position": "absolute",
            "top": "0px",
            "left": "0px",
            "zIndex": "10",
            "width": "100vw",
            "height": "100vh",
            "margin": "0",
            "backgroundColor": "#00000040",
            "cursor": "pointer"
        },
        n_clicks=0,
    )


app.layout = serve_layout

data_fresh = True

@app.callback([
    Output("bulk-edit-btn", "disabled"),
    Output("bulk-edit-btn", "children"),
    Output("bulk-edit-datatable", "data"),
    Output("bulk-edit-dialog-title", "children"),
    [
        Input('datatable', 'multiRowsClicked')
    ]
    ]
)
def editBulkEditButton(multiRowsClicked):
    rows_selected = multiRowsClicked or []
    rows_selected_count = len(rows_selected)

    bulk_edit_data = get_bulk_edit_tabulator_data(rows_selected)
    return (
        rows_selected_count == 0,
        f"Edit {rows_selected_count} rows",
        bulk_edit_data,
        f"Editing {rows_selected_count} rows",
    )

@app.callback([
    Output("bulk-edit-dialog-wrapper", "hidden"),
    Output("bulk-edit-dialog", "open"),
    Input("apply-bulk-edit", "n_clicks"),
    Input('bulk-edit-btn', 'n_clicks'),
    Input('bulk-edit-dialog-wrapper', 'n_clicks'),
    Input('bulk-edit-dialog', 'n_clicks'),
])
def openBulkEditDialog(*args):
    trigger_id = ctx.triggered_id
    is_dialog_opened = False
    if trigger_id == "bulk-edit-btn":
        is_dialog_opened = True
    elif trigger_id == "bulk-edit-dialog-wrapper":
        is_dialog_opened = False
    elif trigger_id == "bulk-edit-dialog":
        is_dialog_opened = True
    elif trigger_id == "apply-bulk-edit":
        is_dialog_opened = False
    return not is_dialog_opened, is_dialog_opened


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
    Output("datatable", "applyBulkEdit"),
    Input("apply-bulk-edit", "n_clicks"),
    Input("bulk-edit-datatable", "data"),
    Input('datatable', 'multiRowsClicked'),
    Input("datatable", "cellEdited"),
    prevent_initial_call=True)
def apply_edit(n_clicks, bulk_edit_datatable_data, rows_selected, cell_edited):
    trigger_id = ctx.triggered_id
    triggered_prop_ids = ctx.triggered_prop_ids
    """
    Record edit in editlog, once a cell has been edited
    """
    if run_context == "local":
        user = "local"
    else:
        user = get_user_details()

    if trigger_id == "datatable" and "cellEdited" in triggered_prop_ids:
        return ees.add_edit_tabulator(cell_edited, user)
    elif trigger_id == "apply-bulk-edit":
        old_data = get_bulk_edit_tabulator_data(rows_selected)
        return ees.bulk_edit_rows(rows_selected, bulk_edit_datatable_data, old_data, user)
    else:
        return "", None

@server.route("/dash")
def my_dash_app():
    return app.index()


@server.route("/flask", methods=['GET', 'POST'])
def dummy_endpoint():
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')
    return jsonify([term])


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
def my_flask_endpoint(linked_ds_name):
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


@server.route('/test')
def test_page():
    return current_app.send_static_file('values_url.html')


logging.info("Webapp OK")
