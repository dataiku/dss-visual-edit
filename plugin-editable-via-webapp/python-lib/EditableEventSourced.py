from commons import get_primary_key
from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from pandas import DataFrame
from commons import get_editlog_schema, merge_edits, pivot_editlog
from os import getenv
from json import loads
from datetime import datetime
from pytz import timezone

def get_editable_column_names(schema):
        editable_column_names = []
        for col in schema:
            if col.get("editable"):
                editable_column_names.append(col.get("name"))
        return editable_column_names

def get_lookup_column_names(linked_record):
        lookup_column_names = []
        lookup_column_names_in_linked_ds = []
        for lookup_column in linked_record["lookup_columns"]:
            lookup_column_names.append(lookup_column["name"])
            lookup_column_names_in_linked_ds.append(lookup_column["linked_ds_column_name"])
        return lookup_column_names, lookup_column_names_in_linked_ds

class EditableEventSourced:

    def __parse_schema__(self):
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

    def __extend_with_lookup_columns__(self, df):
        for linked_record in self.linked_records:
            lookup_column_names, lookup_column_names_in_linked_ds = get_lookup_column_names(linked_record)
            linked_ds = Dataset(linked_record["ds_name"], self.project_key)
            linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
            df = df.join(linked_df, on=linked_record["name"])
            for c in range(0, len(lookup_column_names)):
                df.rename(columns={lookup_column_names_in_linked_ds[c]: lookup_column_names[c]}, inplace=True)
        return df

    def __get_lookup_values__(self, linked_record, linked_record_value):
        _, lookup_column_names_in_linked_ds = self.__get_lookup_column_names__(linked_record)
        linked_ds = Dataset(linked_record["ds_name"], self.project_key)
        linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
        value_cast = linked_record_value
        if (linked_record["type"] == "int"):
            value_cast = int(linked_record_value)
        return linked_df.loc[linked_df.index==value_cast]
        # IDEA: add linked_record["linked_key"] as an INDEX to speed up the query

    def __get_editlog__(self):
        editlog_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.editlog_ds_name)
        if (editlog_ds_creator.already_exists()):
            print("Found editlog")
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
        else:
            print("No editlog found, creating it")
            editlog_ds_creator.with_store_into(connection=self.connection_name)
            editlog_ds_creator.create()
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)

        self.editlog_ds.spec_item["appendMode"] = True # make sure that editlog is in append mode

    def __setup_downstream_editlog__(self):
        editlog_pivoted_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.editlog_pivoted_ds_name)
        if (editlog_pivoted_ds_creator.already_exists()):
            print("Found editlog pivoted")
        else:
            print("No editlog pivoted found, creating it")
            editlog_pivoted_ds_creator.with_store_into(connection=self.connection_name)
            editlog_pivoted_ds_creator.create()
            self.editlog_pivoted_ds = Dataset(self.editlog_pivoted_ds_name, self.project_key)
            cols = ["key"] + get_editable_column_names(self.schema) + ["date"]
            editlog_pivoted_df = DataFrame(columns=cols)
            self.editlog_pivoted_ds.write_schema(get_editlog_schema())
            self.editlog_pivoted_ds.write_dataframe(editlog_pivoted_df)

        recipe_creator = DSSRecipeCreator("CustomCode_pivot-editlog", "compute_" + self.editlog_pivoted_ds_name, self.project)
        if (recipe_creator.already_exists()):
            print("Found recipe to create editlog pivoted")
        else:
            print("No recipe to create editlog pivoted, creating it")
            recipe = recipe_creator.create()
            settings = recipe.get_settings()
            settings.add_input("editlog", self.editlog_ds_name)
            settings.add_output("editlog_pivoted", self.editlog_pivoted_ds_name)
            settings.save()

        edited_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.edited_ds_name)
        if (edited_ds_creator.already_exists()):
            print("Found edited dataset")
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
        else:
            print("No edited dataset found, creating it")
            edited_ds_creator.with_store_into(connection=self.connection_name)
            edited_ds_creator.create()
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)

        recipe_creator = DSSRecipeCreator("CustomCode_merge-edits", "compute_" + self.edited_ds_name, self.project)
        if (recipe_creator.already_exists()):
            print("Found recipe to create edited dataset")
        else:
            print("No recipe to create edited dataset, creating it")
            recipe = recipe_creator.create()
            settings = recipe.get_settings()
            settings.add_input("original", self.original_ds_name)
            settings.add_input("editlog_pivoted", self.editlog_pivoted_ds_name)
            settings.add_output("edited", self.edited_ds_name)
            settings.save()

    def __init__(self, original_ds_name, project_key=None):
        self.original_ds_name = original_ds_name
        if (project_key is None): self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        else: self.project_key = project_key
        client = api_client()
        self.project = client.get_project(self.project_key)

        self.editlog_ds_name = self.original_ds_name + "_editlog"
        self.editlog_pivoted_ds_name = self.editlog_ds_name + "_pivoted"
        self.edited_ds_name = self.original_ds_name + "_edited"

        self.connection_name = Dataset(self.original_ds_name, self.project_key).get_config()['params']['connection']

        self.schema = loads(self.original_ds.get_config()["customFields"]["schema"])
        self.__parse_schema__() # Sets editable_column_names, display_column_names, primary key, primary_key_type, linked_records

        self.original_ds = Dataset(self.original_ds_name, self.project_key)
        self.original_df = self.original_ds.get_dataframe()[[self.primary_key] + self.display_column_names + self.editable_column_names]
        self.__get_editlog__()
        self.__editable_df_indexed__ = self.__extend_with_lookup_columns__(
                                        merge_edits(
                                            self.original_df,
                                            pivot_editlog(self.editlog_df, self.editable_column_names),
                                            self.primary_key
                                        )
                                    ).set_index(self.primary_key) # index makes it easier to id values in the DataFrame

    def get_editable_df_indexed(self):
        return self.__editable_df_indexed__

    def get_editable_df(self):
        return self.get_editable_df_indexed().reset_index()

    def get_editable_tabulator(self):
        return self.get_editable_df().to_dict('records')

    def get_schema(self):
        return self.schema

    def get_schema_tabulator(self):
        # Setup columns to be used by data table
        # Add "editor" to editable columns. Possible values include: "input", "textarea", "number", "tickCross", "list". See all options at options http://tabulator.info/docs/5.2/edit.
        # IDEA: improve this code with a dict to do matching (instead of if/else)?
        t_cols = [] # columns for tabulator
        for col in self.schema:
            t_col = {"field": col["name"], "headerFilter": True, "resizable": True}

            if col.get("type")=="bool" or col.get("type")=="boolean":
                t_col["formatter"] = "tickCross"
                t_col["formatterParams"] = {"allowEmpty": True}
                t_col["hozAlign"] = "center"
                t_col["headerFilter"] = "autocomplete"
                t_col["headerFilterParams"] = {"values": [
                    {
                        "label":"True",
                        "value":"True",
                    },
                    {
                        "label":"False",
                        "value":"False",
                    },
                    {
                        "label":"All",
                        "value":"",
                    },
                ]}
                # t_col["headerFilterEmptyCheck"] = "function(value){return value === null;}"

            if col.get("editable"):
                title = col.get("title")
                title = title if title else col["name"]
                t_col["title"] = "🖊 " + title
                if col.get("type")=="bool" or col.get("type")=="boolean":
                    t_col["editor"] = t_col["formatter"]
                    t_col["editorParams"] = {"tristate": True}
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

    def get_primary_key(self):
        return self.primary_key

    """
    def get_primary_key_type(self):
        return self.primary_key_type

    def get_editable_column_names(self):
        return self.editable_column_names

    def get_display_column_names(self):
        return self.display_column_names

    def get_linked_records(self):
        return self.linked_records

    def get_editlog_df(self):
        return self.editlog_df

    def get_editlog_ds(self):
        return self.editlog_ds
    """

    def add_edit(self, primary_key_value, column_name, value, user): # TODO: pass values for multiple keys
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
            "key": [str(primary_key_value)], # TODO: add all keys
            "column_name": [column_name],
            "value": [value],
            "date": [datetime.now(timezone("UTC")).isoformat()],
            "user": [user]
        }))

        # TODO: do we need ees to maintain a live copy of (and to update) editlog_df? when is edit log accessed?

        # update editable_df
        self.__editable_df_indexed__.loc[primary_key_value, column_name] = value # TODO: multi-indexing?

        # Update lookup columns if a linked record was edited
        for linked_record in self.linked_records:
            if (column_name==linked_record["name"]):
                # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
                lookup_values = self.__get_lookup_values__(linked_record, value)

                # Update table_data with lookup values — note that column names are different in table_data and in the linked record's table
                for lookup_column in linked_record["lookup_columns"]:
                    self.__editable_df_indexed__.loc[primary_key_value, lookup_column["name"]] = lookup_values[lookup_column["linked_ds_column_name"]].iloc[0] # TODO: multi-indexing?
        
        print(f"""Updated column {column_name} where {self.primary_key} is {primary_key_value}. New value: {value}.""") # TODO: multi-indexing?

