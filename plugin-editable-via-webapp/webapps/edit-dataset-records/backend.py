import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html
from dash.dependencies import Input, Output, State

# TODO: remove this
from dash import Dash
app = Dash(__name__)

# Access parameters that end-users filled in using webapp config

# TODO: change back
# DATASET_NAME = get_webapp_config()['input_dataset']
# UNIQUE_KEY = get_webapp_config()['key']
DATASET_NAME = "iris"
UNIQUE_KEY = "index"


# Create change log dataset and editable dataset, if they don't already exist

# TODO: change back
# client = dataiku.api_client()
# project = client.get_default_project()
HOST = "http://localhost:11200/"
APIKEY = "7TDhU6vLOHA3dAY7EONeLDHpd0JGQAtd"
dataiku.set_remote_dss(HOST, APIKEY)
client = dataiku.api_client()
project = client.get_project("EDITABLE")
project_key = project.project_key
import os
os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key

original_ds = dataiku.Dataset(DATASET_NAME, project_key)
original_df = original_ds.get_dataframe()
connection_name = original_ds.get_config()['params']['connection'] # name of the connection to the original dataset, to use for the editable dataset too

changes_ds_name = DATASET_NAME + "_changes"
editable_ds_name = DATASET_NAME + "_editable"

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
    
    recipe_creator = dataikuapi.dss.recipe.DSSRecipeCreator("CustomCode_sync-and-apply-changes", "compute_" + editable_ds_name, project)
    recipe = recipe_creator.create()
    settings = recipe.get_settings()
    settings.add_input("input", DATASET_NAME)
    settings.add_input("changes", changes_ds_name)
    settings.add_output("editable", editable_ds_name)
    settings.raw_params["customConfig"] = {"key": get_webapp_config()['key']}
    settings.save()
else:
    changes_ds = dataiku.Dataset(changes_ds_name, project_key)
    editable_ds = dataiku.Dataset(editable_ds_name, project_key)

editable_df = editable_ds.get_dataframe()
cols = ([{"name": i, "id": i} for i in editable_df.columns])


# Initialize the SQL executor and name of table to edit

executor = SQLExecutor2(connection=connection_name)
# table_name = editable_ds.get_config()['params']['table']
table_name = project_key + "_" + editable_ds_name


# Define the layout of the webapp

app.layout = html.Div([
    html.H3("Edit " + DATASET_NAME),
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
    ]),
    html.H4("Change df"),
    dash_table.DataTable(id="change_df", columns=cols, editable=False)
])

@app.callback([Output('output', 'children'),
              Output('change_df', 'data')], # TODO: test having a 2nd output is ok
              [State('editable-table', 'active_cell'),
              Input('editable-table', 'data')], prevent_initial_call=True)
def update_db(cell_coordinates, table_data):
    cell_coordinates["row"] = cell_coordinates["row"]-1
    row_id = cell_coordinates["row"]
    col_id = cell_coordinates["column_id"]
    val = table_data[row_id][col_id]
    
    cell_update_info = "This cell was updated: " + str(cell_coordinates) + "\n" + "New value: " + str(val) + "\n\n"

    # run update query
    query = """UPDATE \"%s\" SET %s=%s
            WHERE %s=%s
            RETURNING %s, %s;
            """ % (table_name, col_id, val, UNIQUE_KEY, row_id, UNIQUE_KEY, col_id)
    change_df = executor.query_to_df("""SELECT * FROM \"%s\"
                                    LIMIT 1
                                    """ % table_name, pre_queries=[query])
    
    changes_ds.write_dataframe(change_df) # TODO: fix this

    # TODO: WORK IN PROGRESS, based on https://doc.dataiku.com/dss/latest/code_recipes/python.html#writing
    from collections import Counter
    origin_count = Counter()
    row = change_df.iloc[0].to_dict()
    origin_count[row["origin"]] += 1
    with changes_ds.get_writer() as writer:
        for (origin,count) in origin_count.items():
                writer.write_row_array((origin,count))

    return cell_update_info, change_df.to_dict('records')

# TODO: remove this
if __name__ == "__main__":
    app.run_server(debug=True)
