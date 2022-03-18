import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html
from dash.dependencies import Input, Output, State


# Access parameters that end-users filled in using webapp config

DATASET_NAME = get_webapp_config()['input_dataset']


# Create change log dataset and editable dataset, if they don't already exist

client = dataiku.api_client()
project = client.get_default_project()

original_ds = dataiku.Dataset(DATASET_NAME)
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
    changes_ds = dataiku.Dataset(changes_ds_name)
    editable_ds = dataiku.Dataset(editable_ds_name)

editable_df = editable_ds.get_dataframe()


# Initialize the SQL executor and name of table to edit

executor = SQLExecutor2(connection=connection_name)
table_name = editable_ds.get_config()['params']['table']
    

# Define the layout of the webapp

app.layout = html.Div([
    html.H4("Edit " + DATASET_NAME),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=dash_table.DataTable(
                id='editable-table',
                columns=([{"name": i, "id": i} for i in editable_df.columns]),
                data=editable_df.to_dict('records'),
                editable=True
            ),
        ),
        html.Pre(id='output')
    ])
])

@app.callback(Output('output', 'children'),
              [State('editable-table', 'active_cell'),
              Input('editable-table', 'data')], prevent_initial_call=True)
def update_db(cell_coordinates, table_data):
    cell_coordinates["row"] = cell_coordinates["row"]-1
    row_id = cell_coordinates["row"]
    col_id = cell_coordinates["column_id"]
    val = table_data[row_id][col_id]
    
    cell_update_info = "This cell was updated: " + str(cell_coordinates) + "\n" + "New value: " + str(val) + "\n\n"

    # run update query
    query = "UPDATE " + table_name + " SET " + col_id + "='" + str(val) + "' WHERE index='" + str(row_id) + "' RETURNING index, " + col_id + ";"
    db_response = executor.query_to_df(query) # TODO: make sure I can display the response as a dataframe in the webapp

    # add to list of changes
    # pd.DataFrame(rows).to_csv("changes.csv", mode="a", header=False, index=False) # TODO: use Dataiku API and Dataset to write change log

    return cell_update_info, db_response

