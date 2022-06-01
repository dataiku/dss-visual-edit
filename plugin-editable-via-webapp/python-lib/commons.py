import dataiku, dataikuapi
import datetime, pytz
from pandas import DataFrame, concat, pivot_table
from json import loads
from os import getenv
import requests


### Editlog utils

def get_editlog_schema():
    return [
        {"name": "date", "type": "string", "meaning": "DateSource"}, # not using date type, in case the editlog is CSV
        {"name": "user", "type": "string", "meaning": "Text"},
        {"name": "key", "type": "string"},
        {"name": "column_name", "type": "string", "meaning": "Text"},
        {"name": "value", "type": "string"}
    ]

def get_editlog_columns():
    return ["date", "user", "key", "column_name", "value"]

def get_editlog_df(editlog_ds):
    # Try to get dataframe from editlog dataset, if it's not empty. Otherwise, create empty dataframe.
    try:
        editlog_df = editlog_ds.get_dataframe()
    except:
        editlog_df = DataFrame(columns=get_editlog_columns())
        editlog_ds.write_schema(get_editlog_schema())
        editlog_ds.write_dataframe(editlog_df)
    return editlog_df

def get_editlog(input_dataset_name, project_key):
    client = dataiku.api_client()
    project = client.get_project(project_key)
    editlog_ds_name = input_dataset_name + "_editlog"
    editlog_ds_creator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, editlog_ds_name)
    if (editlog_ds_creator.already_exists()):
        print("Found editlog")
        editlog_ds = dataiku.Dataset(editlog_ds_name, project_key)
    else:
        print("No editlog found, creating one")
        connection_name = dataiku.Dataset(input_dataset_name, project_key).get_config()['params']['connection'] # using the same connection as the input dataset
        editlog_ds_creator.with_store_into(connection=connection_name)
        editlog_ds_creator.create()
        editlog_ds = dataiku.Dataset(editlog_ds_name)
    editlog_df = get_editlog_df(editlog_ds)
    editlog_ds.spec_item["appendMode"] = True # make sure that editlog is in append mode
    return editlog_ds, editlog_df


### Recipe utils

def pivot_editlog(editlog_df, editable_column_names):
    # Create empty dataframe that has all editable columns
    # This will help make sure that the pivoted editlog always has the right schema
    # (even if some columns of the input dataset were never edited)
    cols = ["key"] + editable_column_names + ["date"]
    all_editable_columns_df = DataFrame(columns=cols)
    all_editable_columns_df.set_index("key", inplace=True)

    if (not editlog_df.size): # i.e. if empty editlog
        editlog_pivoted_df = all_editable_columns_df
    else:
        editlog_df.set_index("key", inplace=True)
        # For each named column, we only keep the last value
        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("date"), # ordering by edit date
            index="key",
            columns="column_name",
            values="value",
            aggfunc="last"
        ).join(
            editlog_df[["date"]].groupby("key").last() # join the last edit date for each key
        )
        editlog_pivoted_df = concat([all_editable_columns_df, editlog_pivoted_df])

    return editlog_pivoted_df.reset_index()

def merge_edits(input_df, editlog_pivoted_df, primary_key):
    input_df.set_index(primary_key, inplace=True)
    if (not editlog_pivoted_df.size): # i.e. if empty editlog
        edited_df = input_df
    else:
        editlog_pivoted_df.set_index("key", inplace=True)

        # We don't need the date column in the rest
        editlog_pivoted_df = editlog_pivoted_df.drop(columns=["date"])

        # Change types of columns to match input_df?
        # for col in editlog_pivoted_df.columns.tolist():
        #     editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(input_df[col].dtype)

        # Join -> this adds _value_last columns
        editlog_pivoted_df.index.names = [primary_key]
        edited_df = input_df.join(editlog_pivoted_df, rsuffix="_value_last")

        # "Merge" -> this creates _original columns
        editable_column_names = editlog_pivoted_df.columns.tolist() # "date" column has already been dropped
        for col in editable_column_names:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"])

        # Drop the _original and _value_last columns -> this gets us back to the original schema
        edited_df = edited_df[edited_df.columns[:-2*len(editable_column_names)]]

    return edited_df.reset_index()

def get_editable_column_names(schema):
    editable_column_names = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
    return editable_column_names

def get_primary_key(schema):
    for col in schema:
        if col.get("editable_type")=="key":
            return col.get("name"), col.get("type")

def get_webapp_json(webapp_ID):
    project_key = getenv("DKU_CURRENT_PROJECT_KEY")
    return loads(
        requests.get(
            url="http://127.0.0.1:" + dataiku.base.remoterun.get_env_var("DKU_BASE_PORT") + "/public/api/projects/" + project_key + "/webapps/" + webapp_ID,
            headers=dataiku.core.intercom.get_auth_headers(),
            verify=False
        ).text)


### EditableEventSourced
class EditableEventSourced:
    def _parse_schema(self):
        """Parse editable schema"""

        # First pass at the list of columns
        self.editable_column_names = get_editable_column_names(self.schema)
        self.primary_key, self.primary_key_type = get_primary_key(self.schema)
        self.display_column_names = []
        self.linked_records = []
        for col in self.schema:
            if col.get("editable"):
                if col.get("editable_type")=="linked_record":
                    self.linked_records.append(
                        {
                            "name": col.get("name"),
                            "type": col.get("type"),
                            "ds_name": col.get("linked_ds_name"),
                            "ds_key": col.get("linked_ds_key"),
                            "lookup_columns": []
                        }
                    )
            else:
                if col.get("editable_type")!="key":
                    self.display_column_names.append(col.get("name"))

        # Second pass to create the lookup columns for each linked record
        for col in self.schema:
            if col.get("editable_type")=="lookup_column":
                for linked_record in self.linked_records:
                    if linked_record["name"]==col.get("linked_record_col"):
                        linked_record["lookup_columns"].append({
                            "name": col.get("name"),
                            "linked_ds_column_name": col.get("linked_ds_column_name")
                        })

    def _get_lookup_column_names(linked_record):
        lookup_column_names = []
        lookup_column_names_in_linked_ds = []
        for lookup_column in linked_record["lookup_columns"]:
            lookup_column_names.append(lookup_column["name"])
            lookup_column_names_in_linked_ds.append(lookup_column["linked_ds_column_name"])
        return lookup_column_names, lookup_column_names_in_linked_ds

    def _extend_with_lookup_columns(self, df):
        for linked_record in self.linked_records:
            lookup_column_names, lookup_column_names_in_linked_ds = self._get_lookup_column_names(linked_record)
            linked_ds = dataiku.Dataset(linked_record["ds_name"], self.project_key)
            linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
            df = df.join(linked_df, on=linked_record["name"])
            for c in range(0, len(lookup_column_names)):
                df.rename(columns={lookup_column_names_in_linked_ds[c]: lookup_column_names[c]}, inplace=True)
        return df

    def __init__(self, input_ds_name, project_key, schema):
        self.input_ds_name = input_ds_name
        self.project_key = project_key
        self.schema = schema
        self._parse_schema()
        self.input_ds = dataiku.Dataset(input_ds_name, project_key)
        self.input_df = self.input_ds.get_dataframe()[[self.primary_key] + self.display_column_names + self.editable_column_names]
        self.editlog_ds, self.editlog_df = get_editlog(input_ds_name, project_key)
        self._editable_df_indexed = self._extend_with_lookup_columns(
                                    merge_edits(
                                        self.input_df,
                                        pivot_editlog(self.editlog_df, self.editable_column_names),
                                        self.primary_key
                                    )
                                    ).set_index(self.primary_key) # index makes it easier to id values in the DataFrame

    def get_editable_df(self):
        return self.get_editable_df_indexed().reset_index()

    def get_editable_df_indexed(self):
        return self._editable_df_indexed

    def get_editable_tabulator(self):
        return self.get_editable_df().to_dict('records')

    def add_edit(self, primary_key_value, column_name, value, user):
        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.schema:
            if (col["name"]==column_name):
                if type(value)==str and (col["type"]=="bool" or col["type"]=="boolean"):
                    value = str(loads(value.lower()))
                break
        
        # store value as a string, unless it's None
        if (value!=None): value = str(value)

        # add to the editlog
        self.editlog_ds.write_dataframe(DataFrame(data={
            "key": [str(primary_key_value)],
            "column_name": [column_name],
            "value": [value],
            "date": [datetime.datetime.now(pytz.timezone("UTC")).isoformat()],
            "user": [user]
        }))

        # update editable_df
        self._editable_df_indexed.loc[primary_key_value, column_name] = value

        # Update lookup columns if a linked record was edited
        for linked_record in self.linked_records:
            if (column_name==linked_record["name"]):
                # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
                lookup_values = self.get_lookup_values(linked_record, value)

                # Update table_data with lookup values — note that column names are different in table_data and in the linked record's table
                for lookup_column in linked_record["lookup_columns"]:
                    self._editable_df_indexed.loc[primary_key_value, lookup_column["name"]] = lookup_values[lookup_column["linked_ds_column_name"]].iloc[0]
        
        print(f"""Updated column {column_name} where {self.primary_key} is {primary_key_value}. New value: {value}.""")

    def get_lookup_values(self, linked_record, linked_record_value):
        _, lookup_column_names_in_linked_ds = self._get_lookup_column_names(linked_record)
        linked_ds = dataiku.Dataset(linked_record["ds_name"], self.project_key)
        linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
        value_cast = linked_record_value
        if (linked_record["type"] == "int"):
            value_cast = int(linked_record_value)
        return linked_df.loc[linked_df.index==value_cast]
        # IDEA: add linked_record["linked_key"] as an INDEX to speed up the query

    def get_schema(self):
        return self.schema

    def get_editable_column_names(self):
        return self.editable_column_names

    def get_display_column_names(self):
        return self.display_column_names

    def get_linked_records(self):
        return self.linked_records

    def get_primary_key(self):
        return self.primary_key

    def get_primary_key_type(self):
        return self.primary_key_type

    def get_editlog_df(self):
        return self.editlog_df

    def get_editlog_ds(self):
        return self.editlog_ds


### Other utils

def get_table_name(dataset, project_key):
    return dataset.get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", dataiku.get_custom_variables().get("NODE"))
