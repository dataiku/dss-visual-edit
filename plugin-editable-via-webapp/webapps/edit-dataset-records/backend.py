# -*- coding: utf-8 -*-

import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html
from dash.dependencies import Input, Output, State
from pandas import DataFrame
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
from dash import Dash
from flask import Flask
f_app = Flask(__name__)
app = Dash(__name__, server=f_app)
application = app.server


# 1. Access parameters that end-users filled in using webapp config

import os
if (os.getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    edit_type = get_webapp_config()['edit_type']
    if (edit_type=="simple"):
        input_dataset = get_webapp_config()['input_dataset']
        input_key = get_webapp_config()['input_key']
    elif (edit_type=="join"):
        ref_dataset = get_webapp_config()['ref_dataset']
        ref_key = get_webapp_config()['ref_key']
        ref_lookup_columns = get_webapp_config()['ref_lookup_columns']
        ext_dataset = get_webapp_config()['ext_dataset']
        ext_key = get_webapp_config()['ext_key']
        ext_lookup_columns = get_webapp_config()['ext_lookup_columns']
    # user_name = get_webapp_config()['user'] IDEA: does this exist? or can we get it from an environment variable (DKU_CURRENT_USER?)
else:
    edit_type = "join"
    if (edit_type=="simple"):
        input_dataset = "iris"
        input_key = "index"
    elif (edit_type=="join"):
        ref_dataset = "companies_ref"
        ref_key = "id"
        ref_lookup_columns = ["name", "city", "country"]
        ext_dataset = "companies_ext"
        ext_key = "id"
        ext_lookup_columns = ["name", "city", "country"]
project_key = os.getenv("DKU_CURRENT_PROJECT_KEY")
if (not project_key or project_key==""):
    project_key = "EDITABLE"
    os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key


# 2. Initialize Dataiku client and project

client = dataiku.api_client()
project = client.get_project(project_key)


# 3. Create change log dataset and editable dataset, if they don't already exist

if (edit_type=="simple"):
    original_ds = dataiku.Dataset(input_dataset, project_key)
    original_df = original_ds.get_dataframe()
    connection_name = original_ds.get_config()['params']['connection'] # name of the connection to the original dataset, to use for the editable dataset too

    changes_ds_name = input_dataset + "_changes"
    editable_ds_name = input_dataset + "_editable"

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
        settings.add_input("input", input_dataset)
        settings.add_input("changes", changes_ds_name)
        settings.add_output("editable", editable_ds_name)
        settings.raw_params["customConfig"] = {"key": input_key}
        settings.save()
    else:
        changes_ds = dataiku.Dataset(changes_ds_name, project_key)
        editable_ds = dataiku.Dataset(editable_ds_name, project_key)
elif (edit_type=="join"):
    # IDEA: write code to create these datasets if they don't already exist, and the recipes to connect them
    changes_ds = dataiku.Dataset(ref_dataset + "_" + ext_dataset + "_editlog", project_key)
    editable_ds = dataiku.Dataset(ref_dataset + "_" + ext_dataset + "_editable", project_key)
    ext_ds = dataiku.Dataset(ext_dataset, project_key)
    ext_tablename = ext_ds.get_config()['params']['table'].replace("${projectKey}", project_key)

changes_ds.spec_item["appendMode"] = True # make sure that we append to that dataset (and not write over it)
editable_df = editable_ds.get_dataframe()
cols = ([{"name": i, "id": i} for i in editable_df.columns])


# 4. Initialize the SQL executor and name of table to edit

executor = SQLExecutor2(connection=connection_name)
editable_tablename = editable_ds.get_config()['params']['table'].replace("${projectKey}", project_key)


# 5. Define the layout of the webapp

app.layout = html.Div([
    html.H3("Edit " + input_dataset),
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

@app.callback([Output('output', 'children'),
               Output('editable-table', 'data')],
              [State('editable-table', 'active_cell'),
               Input('editable-table', 'data')], prevent_initial_call=True)
def update(cell_coordinates, table_data):
    row_id = cell_coordinates["row"]-1
    col_id = cell_coordinates["column_id"]
    
    if (edit_type=="simple"):
        idx = table_data[row_id][input_key]
        val = table_data[row_id][col_id]

        query = """UPDATE \"{0}\" SET {1}={2}
            WHERE {3}={4}
            COMMIT;
            """.format(editable_tablename, col_id, val, input_key, idx)
        executor.query_to_df(query)
        select_change_query = """SELECT {0} FROM \"{1}\" WHERE {2}={3}""".format(col_id, editable_tablename, input_key, idx)

        message = "Updated column " + str(col_id) \
                    + " where " + input_key + " is " + idx + ". \n" \
                    + "New value: " + str(val) + "\n\n"

        change_df = executor.query_to_df(select_change_query)
        changes_ds.write_dataframe(change_df)

    elif (edit_type=="join"):
        ref_key_value = table_data[row_id][ref_key]
        ext_key_original_column_name = "ext_" + ext_key + "_original"
        ext_key_reviewed_column_name = "ext_" + ext_key + "_reviewed"
        ext_key_original_value = table_data[row_id][ext_key_original_column_name]
        ext_key_reviewed_value = table_data[row_id][ext_key_reviewed_column_name]

        if (col_id=="reviewed" & table_data[row_id]["reviewed"]=="True"):
            message("Row is marked as reviewed, so it will be added to the edit log.")
            
            # We only write to the change log when the reviewed column was just set to true
            changes_ds.write_dataframe(
                DataFrame({ref_key: [ref_key_value], ext_key_original_column_name: [ext_key_original_value], ext_key_reviewed_column_name: [ext_key_reviewed_value]})
                )

        if (col_id==ext_key_reviewed_column_name):
            # Retrieve values of the lookup columns from the external dataset, for this ext_idx
            select_query = "SELECT " + ", ".join(ext_lookup_columns) + " FROM \"" + ext_tablename + "\" WHERE " + ext_key + "=" + ext_key_reviewed_value
            select_df = executor.query_to_df(select_query)

            # Update table_data with these values — note that colum names in this dataset are prefixed by "ext_"
            for col in ext_lookup_columns: table_data[row_id]["ext_" + col] = select_df[col].iloc[0]

            # Update the editable dataset with these values
            update_query = "UPDATE \"" + editable_tablename + "\" SET " + ", ".join(["ext_" + col + "=" + str(select_df[col].iloc[0]) for col in ext_lookup_columns]) + " WHERE " + ext_key_reviewed_column_name + "=" + ext_key_reviewed_value + "; COMMIT;"
            executor.query_to_df(update_query)

            message = "Changed values of lookup columns"

    
    # change_df["date"] = datetime.date.today().strftime("%Y-%m-%d") IDEA: first add the date field to the changes_ds schema
    # change_df["user"] = "anonymous"

    return message, table_data


# Uncomment the following when running the Dash app in debug mode outside of Dataiku
if __name__ == "__main__":
  app.run_server(debug=True)
