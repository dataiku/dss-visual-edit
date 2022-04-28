import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html
from dash.dependencies import Input, Output, State
import datetime


# Dash webapp to edit dataset records
# This code is structured as follows:
# 1. Access parameters that end-users filled in using webapp config
# 2. Initialize Dataiku client and project
# 3. Create change log dataset and editable dataset, if they don't already exist
# 4. Initialize the SQL executor and name of table to edit
# 5. Define the layout of the webapp
# 6. Define the callback function that updates the editable and change log when cell values get edited


# Uncomment the following when running the Dash app in debug mode outside of Dataiku
# from dash import Dash
# app = Dash(__name__)


# 1. Access parameters that end-users filled in using webapp config

import os
if (os.getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    dataset_name = get_webapp_config()['input_dataset']
    unique_key = get_webapp_config()['key']
    # user_name = get_webapp_config()['user'] TODO: does this exist? or can we get it from an environment variable (DKU_CURRENT_USER?)
else:
    dataset_name = "iris"
    unique_key = "index"
project_key = os.getenv("DKU_CURRENT_PROJECT_KEY")
if (not project_key or project_key==""):
    project_key = "EDITABLE"
    os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key


# 2. Initialize Dataiku client and project

client = dataiku.api_client()
project = client.get_project(project_key)


# 3. Create change log dataset and editable dataset, if they don't already exist

original_ds = dataiku.Dataset(dataset_name, project_key)
original_df = original_ds.get_dataframe()
connection_name = original_ds.get_config()['params']['connection'] # name of the connection to the original dataset, to use for the editable dataset too

changes_ds_name = dataset_name + "_editlog"
editable_ds_name = dataset_name + "_webapp"

changes_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, changes_ds_name)
editable_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, editable_ds_name)

if (not changes_ds_creator.already_exists()):
    changes_ds_creator.with_store_into(connection="filesystem_managed")
    changes_ds_creator.create()
    changes_ds = dataiku.Dataset(changes_ds_name)
    changes_ds.write_schema_from_dataframe(df=original_df)
    
    editable_ds_creator.with_store_into(connection=connection_name)
    editable_ds_creator.create()
    editable_ds = dataiku.Dataset(editable_ds_name)
    editable_ds.write_with_schema(original_df)
    
    recipe_creator = dataikuapi.dss.recipe.DSSRecipeCreator("CustomCode_sync-and-apply-edits", "compute_" + editable_ds_name, project)
    recipe = recipe_creator.create()
    settings = recipe.get_settings()
    settings.add_input("input", dataset_name)
    settings.add_input("changes", changes_ds_name)
    settings.add_output("editable", editable_ds_name)
    settings.raw_params["customConfig"] = {"key": get_webapp_config()['key']}
    settings.save()
else:
    changes_ds = dataiku.Dataset(changes_ds_name, project_key)
    editable_ds = dataiku.Dataset(editable_ds_name, project_key)

editable_df = editable_ds.get_dataframe()
cols = ([{"name": i, "id": i} for i in editable_df.columns])


# 4. Initialize the SQL executor and name of table to edit

executor = SQLExecutor2(connection=connection_name)
# table_name = editable_ds.get_config()['params']['table']
table_name = project_key + "_" + editable_ds_name


# 5. Define the layout of the webapp

app.layout = html.Div([
    html.H3("Edit " + dataset_name),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=dash_table.DataTable(
                id='editable-table',
                columns=cols,
                data=editable_df.to_dict('records'),
                editable=True
            ),
        ),
        html.Pre(id='output')
    ])
])


# 6. Define the callback function that updates the editable and change log when cell values get edited

@app.callback(Output('output', 'children'),
              [State('editable-table', 'active_cell'),
              Input('editable-table', 'data')], prevent_initial_call=True)
def update(cell_coordinates, table_data):
    row_id = cell_coordinates["row"]-1
    idx = table_data[row_id][unique_key]
    col_id = cell_coordinates["column_id"]
    val = table_data[row_id][col_id]

    # IDEA: surround the following with try/catch?
    # Run update query on the editable
    query = """UPDATE \"{0}\" SET {1}={2}
            WHERE {3}={4}
            """.format(table_name, col_id, val, unique_key, idx)
    executor.query_to_df(query)
    select_change_query = """SELECT {0} FROM "{1}" WHERE "{2}"={3}""".format(col_id, table_name, unique_key, idx)
    change_df = executor.query_to_df(select_change_query)

    # Append the change to the log
    changes_ds.spec_item["appendMode"] = True
    changes_ds.write_dataframe(change_df)

    return "Value at row " + str(row_id) + ", column " + str(col_id) + " was updated. \n" + "New value: " + str(val) + "\n\n"


# Uncomment the following when running the Dash app in debug mode outside of Dataiku
# if __name__ == "__main__":
#   app.run_server(debug=True)
