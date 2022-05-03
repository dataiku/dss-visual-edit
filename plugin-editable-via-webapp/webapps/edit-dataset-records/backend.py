# -*- coding: utf-8 -*-

import dataiku
import dataikuapi
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *
from dash import dash_table, html, Dash
from dash.dependencies import Input, Output, State
from flask import Flask
from pandas import DataFrame
import datetime
import os


# Dash webapp to edit dataset records
# This code is structured as follows:
# 1. Access parameters that end-users filled in using webapp config
# 2. Initialize Dataiku client and project
# 3. Create change log dataset and editable dataset, if they don't already exist
# 4. Initialize the SQL executor and name of table to edit
# 5. Define the layout of the webapp and the DataTable component
# 6. Define the callback function that updates the editable and change log when cell values get edited


# 1. Access parameters that end-users filled in using webapp config

# Define edit type
if (os.getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    edit_type = get_webapp_config()['edit_type'] # TODO: delete edit_type
else:
    edit_type = "simple" # default edit type when running the Dash app in debug mode outside of Dataiku

# Define project key
project_key = os.getenv("DKU_CURRENT_PROJECT_KEY")
if (not project_key or project_key==""):
    if (edit_type=="simple"):
        project_key = "EDITABLE"
    elif (edit_type=="join"):
        project_key = "JOIN_COMPANIES"
os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key

# Define dataset names
if (os.getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    if (edit_type=="simple"):
        input_dataset = get_webapp_config()['input_dataset']
        input_key = get_webapp_config()['input_key']
    elif (edit_type=="join"):
        ref_dataset_DELETE = get_webapp_config()['ref_dataset']
        ref_key_DELETE = get_webapp_config()['ref_key']
        ref_lookup_columns_DELETE = get_webapp_config()['ref_lookup_columns']
        ext_dataset = get_webapp_config()['ext_dataset']
        ext_key = get_webapp_config()['ext_key']
        ext_lookup_columns = get_webapp_config()['ext_lookup_columns']
else:
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)
    application = app.server
    if (edit_type=="simple"):
        input_dataset = "transactions_categorized"
        input_key = "id"
    elif (edit_type=="join"):
        ref_dataset_DELETE = "companies_ref"
        ref_key_DELETE = "id"
        ref_lookup_columns_DELETE = ["name", "city", "country"]
        ext_dataset = "companies_ext"
        ext_key = "id"
        ext_lookup_columns = ["name", "city", "country"]


# 2. Initialize Dataiku client and project

client = dataiku.api_client()
project = client.get_project(project_key)


# 3.1. Create change log dataset and editable dataset, if they don't already exist

if (edit_type=="simple"):
    original_ds = dataiku.Dataset(input_dataset, project_key)
    original_df = original_ds.get_dataframe()
    connection_name = original_ds.get_config()['params']['connection'] # name of the connection to the original dataset, to use for the editable dataset too

    changes_ds_name = input_dataset + "_editlog"
    editable_ds_name = input_dataset + "_editable"

    changes_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, changes_ds_name)
    editable_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, editable_ds_name)

    if (not changes_ds_creator.already_exists()):
        changes_ds_creator.with_store_into(connection="filesystem_managed")
        changes_ds_creator.create()
        changes_ds = dataiku.Dataset(changes_ds_name)
        changes_ds.write_schema_from_dataframe(df=original_df) # TODO: add suffix "_edited" to each column name
        
        editable_ds_creator.with_store_into(connection=connection_name)
        editable_ds_creator.create()
        editable_ds = dataiku.Dataset(editable_ds_name)
        editable_ds.write_with_schema(original_df)
        
        recipe_creator = dataikuapi.dss.recipe.DSSRecipeCreator("CustomCode_replay-edits", "compute_" + editable_ds_name, project)
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
    ext_ds = dataiku.Dataset(ext_dataset, project_key)
    # TODO: write code to create these datasets if they don't already exist, and the recipes to connect them
    ext_tablename = ext_ds.get_config()['params']['table'].replace("${projectKey}", project_key)

changes_ds.spec_item["appendMode"] = True # make sure that we append to that dataset (and don't write over it)
editable_df = editable_ds.get_dataframe()


# 3.2. Define columns to use in the DataTable component later on

# create new column ext_key in editable_df whose value is the same as column ext_key_edited when not empty, and the same as ext_key_original when empty
ext_key_column_name = "ext_" + ext_key
ext_key_original_column_name = ext_key_column_name + "_original"
ext_key_edited_column_name = ext_key_column_name + "_edited"
editable_df.loc[:, ext_key_column_name] = editable_df[ext_key_edited_column_name].where(editable_df[ext_key_edited_column_name].notnull(), editable_df[ext_key_original_column_name])

# IDEA: loop over columns identified as keys, and lookup columns for each key
pd_cols = editable_df.columns
for col in ext_lookup_columns: pd_cols.append("ext_" + col) # TODO: how is ext_lookup_columns defined?
pd_cols.append("reviewed")
pd_cols.append("date")
pd_cols.append("user")
dash_cols = ([{"name": i, "id": i} for i in pd_cols]) # columns for dash


# 4. Initialize the SQL executor and name of table to edit

executor = SQLExecutor2(connection=connection_name)
editable_tablename = editable_ds.get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", dataiku.get_custom_variables()["NODE"])

# 5. Define the layout of the webapp

app.layout = html.Div([
    html.H3(edit_type),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=dash_table.DataTable(
                id='editable-table',
                columns=dash_cols,
                data=editable_df[pd_cols].to_dict('records'),
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
    # Set the date of the change and the user behind it
    d = datetime.date.today()
    current_user_settings = client.get_own_user().get_settings().get_raw()
    u = f"""{current_user_settings["displayName"]} <{current_user_settings["email"]}>"""

    # Determine the row and column of the cell that was edited
    row_id = cell_coordinates["row"]-1
    col_id = cell_coordinates["column_id"]

    if (edit_type=="simple"):
        idx = table_data[row_id][input_key]
        val = table_data[row_id][col_id]

        # TODO: review queries: quotation marks, and storing of date and user to add to the edit log
        # IDEA: add input_key as an INDEX to speed up the query (WHERE clause)
        query = f"""UPDATE \"{editable_tablename}\"
                    SET "{col_id}"='{val}'
                    WHERE "{input_key}"={idx};
                    COMMIT;"""
        executor.query_to_df(query)
        select_change_query = f"""SELECT {col_id}
                                  FROM "{editable_tablename}"
                                  WHERE "{input_key}"={idx}"""

        message = "Updated column " + str(col_id) \
                    + " where " + input_key + " is " + idx + ". \n" \
                    + "New value: " + str(val) + "\n\n"

        change_df = executor.query_to_df(select_change_query)
        changes_ds.write_dataframe(change_df)

    elif (edit_type=="join"):
        # Update table data TODO: this should also be used with simple edit type
        table_data[row_id]["date"] = d.strftime("%Y-%m-%d")
        table_data[row_id]["user"] = u

        ref_key_value = table_data[row_id][ref_key_DELETE]
        ext_key_original_value = int(editable_df[editable_df[ref_key_DELETE]==ref_key_value][ext_key_original_column_name]) # TODO: this fails when there are several rows with the same ref_key_value -> fix
        ext_key_edited_value = table_data[row_id][ext_key_column_name]
        editable_df.where(editable_df[ref_key_DELETE]==ref_key_value)

        if (col_id=="reviewed" and table_data[row_id]["reviewed"]=="true"):
            # Update the editable dataset
            if (ext_key_original_value==None):
                # IDEA: add ref_key as an INDEX to speed up the query
                update_query = f"""UPDATE "{editable_tablename}"
                                   SET "date"='{d.strftime("%Y-%m-%d")}', "user"='{u}', "reviewed"=TRUE
                                   WHERE "{ref_key_DELETE}"={str(ref_key_value)};
                                   COMMIT;"""
            else:
                # IDEA: add ext_key as an INDEX to speed up the query
                update_query = f"""UPDATE "{editable_tablename}"
                                   SET "date"='{d.strftime("%Y-%m-%d")}', "user"='{u}', "reviewed"=TRUE
                                   WHERE "ext_key_original_column_name"={str(ext_key_original_value)}
                                   AND "{ref_key_DELETE}"={str(ref_key_value)};
                                   COMMIT;"""
            executor.query_to_df(update_query)

            message = "Row is marked as reviewed, so it will be added to the edit log."
            
            # We only write to the change log when the reviewed column was just set to true
            change_df = DataFrame({ref_key_DELETE: [ref_key_value], ext_key_original_column_name: [ext_key_original_value], ext_key_edited_column_name: [ext_key_edited_value], 'date': [d], 'user': [u]})
            changes_ds.write_dataframe(change_df)

        if (col_id==ext_key_column_name):
            # Retrieve values of the lookup columns from the external dataset, for this ext_key_edited value
            select_query = f"""SELECT {", ".join(ext_lookup_columns)}
                               FROM "{ext_tablename}"
                               WHERE "{ext_key}"={ext_key_edited_value}"""
            select_df = executor.query_to_df(select_query)

            # Update table_data with these values — note that colum names in this dataset are prefixed by "ext_"
            for col in ext_lookup_columns: table_data[row_id]["ext_" + col] = select_df[col].iloc[0]

            # Update the editable dataset with these values
            sets = ", ".join(
                [ f""""ext_{col}"='{str(select_df[col].iloc[0])}'"""
                for col in ext_lookup_columns ]
            )
            update_query = f"""UPDATE "{editable_tablename}"
                               SET {sets}, "date"='{d.strftime("%Y-%m-%d")}', "user"='{u}'
                               WHERE "{ref_key_DELETE}"={ref_key_value};
                               COMMIT;"""
            executor.query_to_df(update_query)

            message = "Changed values of lookup columns"

    return message, table_data


# Run Dash app in debug mode when outside of Dataiku
if __name__ == "__main__":
    if app: app.run_server(debug=True)
