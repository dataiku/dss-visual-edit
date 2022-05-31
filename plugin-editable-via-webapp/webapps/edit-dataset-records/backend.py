# -*- coding: utf-8 -*-

import dataiku
from os import environ, getenv
from json import load, loads
from commons import EditableEventSourced
from dataiku.customwebapp import get_webapp_config
from flask import Flask
from dash import html, Dash
from dash_tabulator import DashTabulator
from dash.dependencies import Input, Output

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')


# Dash webapp to edit dataset records

# This code is structured as follows:
# 0. Init: get webapp settings, Dataiku client, and project
# 1. Get editable dataset and dataframe
# 2. Define the webapp layout and its "data table" (here we're using tabulator)
# 3. Define the callback function that updates the editlog when cell values get edited


# 0. Init: get webapp settings and Dataiku client

if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"
    project_key = getenv("DKU_CURRENT_PROJECT_KEY")

    # get parameters from webapp config (specific to the current webapp)
    input_dataset_name = get_webapp_config()["input_dataset"]
    schema = loads(get_webapp_config()["schema"])

else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    settings = load(open(getenv("EDIT_DATASET_RECORDS_SETTINGS"))) # define this env variable in VS Code launch config and have it point to a settings file that contains the project key
    project_key = settings["project_key"]
    environ["DKU_CURRENT_PROJECT_KEY"] = project_key # just in case

    # get parameters from settings file (specific to the current webapp)
    input_dataset_name = settings["input_dataset"]
    schema = settings["schema"]

    # instantiate Dash
    f_app = Flask(__name__)
    app = Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/semantic-ui@2/dist/semantic.min.css"], external_scripts=["https://cdn.jsdelivr.net/npm/semantic-ui-react/dist/umd/semantic-ui-react.min.js"], server=f_app) # using bootstrap css
    application = app.server

client = dataiku.api_client()


# 1. Get editable dataset and dataframe

ees = EditableEventSourced(input_dataset_name, project_key, schema)
editable_df = ees.get_editable_df()


# 2. Define the webapp layout and its DataTable 

def schema_to_tabulator(schema):
    # Setup columns to be used by data table
    # Add "editor" to editable columns. Possible values include: "input", "textarea", "number", "tickCross", "list". See all options at options http://tabulator.info/docs/5.2/edit.
    # TODO: improve this code with a dict to do matching (instead of if/else)?
    t_cols = [] # columns for tabulator
    for col in schema:
        t_col = {"field": col["name"], "headerFilter": True, "resizable": True}

        if col.get("type")=="bool" or col.get("type")=="boolean":
            t_col["formatter"] = "tickCross"
            t_col["formatterParams"] = {"allowEmpty": True}
            t_col["hozAlign"] = "center"

        if col.get("editable"):
            title = col.get("title")
            title = title if title else col["name"]
            t_col["title"] = "🖊 " + title
            if col.get("type")=="bool" or col.get("type")=="boolean":
                t_col["editor"] = t_col["formatter"]
                # t_col["editorParams"] = {"tristate": True}
            elif col.get("type")=="float" or col.get("type")=="double" or col.get("type")=="int" or col.get("type")=="integer":
                t_col["editor"] = "number"
            else:
                t_col["editor"] = "input"
        else:
            t_col["title"] = col["name"]
            if col.get("editable_type")=="key":
                t_col["frozen"] = True

        t_cols.append(t_col)
    return t_cols

t_cols = schema_to_tabulator(schema) # columns for tabulator
t_data = editable_df.to_dict('records') # data for tabulator
editable_df.set_index(ees.primary_key, inplace=True) # set index to make it easier to id values in the DataFrame

app.layout = html.Div([
    html.H3("Edit"),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=DashTabulator(
                id='datatable',
                columns=t_cols,
                data=t_data,
                theme='bootstrap/tabulator_bootstrap4',
                options={"selectable": 1, "layout": "fitDataTable"},
                # see http://tabulator.info/docs/5.2/options#columns for layout options
                # TODO: groupby option is interesting for Fuzzy Join use case - see https://github.com/preftech/dash-tabulator
            ),
        ),
        # html.Div(id='debug', children='Debug'),
        ])
    ])


# 3. Define the callback function that updates the editlog when cell values get edited

@app.callback([Output('debug', 'children'),
               Output('datatable', 'data')],
               Input('datatable', 'cellEdited'), prevent_initial_call=True)
def update(cell):
    primary_key_value = cell["row"][ees.primary_key]
    column_name = cell["column"]
    value = cell["value"]
    current_user_settings = client.get_own_user().get_settings().get_raw()
    user = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""
    ees.add_edit(primary_key_value, column_name, value, user)

    editable_df.loc[primary_key_value, column_name] = value

    # Update table data if a linked record was edited: refresh corresponding lookup columns
    for linked_record in ees.linked_records:
        if (column_name==linked_record["name"]):
            # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
            lookup_values = ees.get_lookup_values(linked_record, value)

            # Update table_data with lookup values — note that column names are different in table_data and in the linked record's table
            for lookup_column in linked_record["lookup_columns"]:
                editable_df.loc[primary_key_value, lookup_column["name"]] = lookup_values[lookup_column["linked_ds_column_name"]].iloc[0]

    message = f"""Updated column {column_name} where {ees.primary_key} is {primary_key_value}. New value: {value}."""
    print(message)

    return message, editable_df.reset_index().to_dict('records')


# Run Dash app in debug mode when outside of Dataiku

if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)

print("Webapp OK")
