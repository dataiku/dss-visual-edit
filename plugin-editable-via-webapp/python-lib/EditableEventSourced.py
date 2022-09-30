from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from pandas import DataFrame
from commons import get_primary_keys, get_editable_column_names, merge_edits, pivot_editlog, tabulator_row_key_values, find_webapp_id, get_webapp_json
from os import getenv
from json5 import loads
from datetime import datetime
from pytz import timezone
from dash_extensions.javascript import Namespace
from urllib.parse import urlparse
from re import sub

# TODO: clean up - this isn't used anymore
# def get_lookup_column_names(linked_record):
#     lookup_column_names = []
#     lookup_column_names_in_linked_ds = []
#     for lookup_column in linked_record["lookup_columns"]:
#         lookup_column_names.append(lookup_column["name"])
#         lookup_column_names_in_linked_ds.append(lookup_column["linked_ds_column_name"])
#     return lookup_column_names, lookup_column_names_in_linked_ds

def recipe_already_exists(recipe_name, project):
    try:
        project.get_recipe(recipe_name).get_status()
        return True
    except:
        return False

class EditableEventSourced:

    def __save_custom_fields__(self, dataset_name):
        settings = self.project.get_dataset(dataset_name).get_settings()
        settings.custom_fields["original_ds"] = self.original_ds_name
        settings.custom_fields["editlog_ds"] = self.editlog_ds_name
        settings.custom_fields["primary_keys"] = self.primary_keys
        settings.custom_fields["editable_column_names"] = self.editable_column_names
        if (self.webapp_url): settings.custom_fields["webapp_url"] = self.webapp_url
        settings.save()
    
    def __init_webapp_url__(self):
        try:
            webapp_id = find_webapp_id(self.original_ds_name)
            webapp_name = sub(r'[\W_]+', '-', get_webapp_json(webapp_id).get("name").lower())
            self.webapp_url = f"/projects/{self.project_key}/webapps/{webapp_id}_{webapp_name}/edit"
            self.webapp_url_public = f"/public-webapps/{self.project_key}/{webapp_id}/"
        except:
            self.webapp_url = None
            self.webapp_url_public = "/"

    def __setup_linked_records__(self):
        self.linked_records = []
        self.linked_record_names = []
        for col in self.editschema_manual:
            if col.get("editable_type")=="linked_record":
                linked_ds_key = col.get("linked_ds_key")
                linked_ds_label = col.get("linked_ds_label")
                linked_ds_lookup_columns = col.get("linked_ds_lookup_columns")
                if not linked_ds_key: linked_ds_key = col.get("name")
                if not linked_ds_label: linked_ds_label = linked_ds_key
                if not linked_ds_lookup_columns: linked_ds_lookup_columns = []
                self.linked_records.append(
                    {
                        "name": col.get("name"),
                        "ds_name": col.get("linked_ds_name"),
                        "ds_key": linked_ds_key,
                        "ds_label": linked_ds_label,
                        "ds_lookup_columns": linked_ds_lookup_columns
                    }
                )
                self.linked_record_names.append(col.get("name"))
        if (len(self.linked_records) > 0):
            self.linked_records_df = DataFrame(data=self.linked_records).set_index("name")
        
        # TODO: clean up
        # Second pass to create the lookup columns for each linked record
        # for col in self.editschema_manual:
        #     if col.get("editable_type")=="lookup_column":
        #         for linked_record in self.linked_records:
        #             if linked_record["name"]==col.get("linked_record_col"):
        #                 linked_record["lookup_columns"].append({
        #                     "name": col.get("name"),
        #                     "linked_ds_column_name": col.get("linked_ds_column_name")
        #                 })

    # TODO: clean up - this isn't used anymore
    # def __extend_with_lookup_columns__(self, df):
    #     for linked_record in self.linked_records:
    #         lookup_column_names, lookup_column_names_in_linked_ds = get_lookup_column_names(linked_record)
    #         linked_ds = Dataset(linked_record["ds_name"], self.project_key)
    #         linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
    #         df = df.join(linked_df, on=linked_record["name"])
    #         for c in range(0, len(lookup_column_names)):
    #             df.rename(columns={lookup_column_names_in_linked_ds[c]: lookup_column_names[c]}, inplace=True)
    #     return df

    # TODO: clean up - this isn't used anymore
    # def __get_lookup_values__(self, linked_record, linked_record_value):
    #     _, lookup_column_names_in_linked_ds = get_lookup_column_names(linked_record)
    #     linked_ds = Dataset(linked_record["ds_name"], self.project_key)
    #     linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
    #     # value_cast = linked_record_value
    #     # if (linked_record["type"] == "int"):
    #     #    value_cast = int(linked_record_value)
    #     return linked_df.loc[linked_df.index==linked_record_value]
    #     # IDEA: add linked_record["linked_key"] as an INDEX to speed up the query

    def __get_editlog_pivoted_ds_schema__(self):
        # see commons.get_editlog_ds_schema
        editlog_pivoted_ds_schema = []
        edited_ds_schema = []
        for col in self.__schema__:
            new_col = {}
            new_col["name"] = col.get("name")
            type = col.get("type")
            if (type): new_col["type"] = type
            meaning = col.get("meaning")
            if (meaning): new_col["meaning"] = meaning
            edited_ds_schema.append(new_col)
            if (col.get("name") in self.primary_keys + self.editable_column_names):
                editlog_pivoted_ds_schema.append(new_col)
        editlog_pivoted_ds_schema.append({"name": "last_edit_date", "type": "string", "meaning": "DateSource"})
        return editlog_pivoted_ds_schema, edited_ds_schema

    def __setup_editlog__(self):
        editlog_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.editlog_ds_name)
        if (editlog_ds_creator.already_exists()):
            # print("Found editlog")
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
        else:
            # print("No editlog found, creating it...")
            editlog_ds_creator.with_store_into(connection=self.__connection_name__)
            editlog_ds_creator.create()
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            # print("Done.")

        # make sure that editlog is in append mode
        self.editlog_ds.spec_item["appendMode"] = True
        
        # make sure that editlog has the right custom field values
        self.__save_custom_fields__(self.editlog_ds_name)

    def __setup_editlog_downstream__(self):
        editlog_pivoted_ds_schema, edited_ds_schema = self.__get_editlog_pivoted_ds_schema__()
        editlog_pivoted_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.editlog_pivoted_ds_name)
        if (editlog_pivoted_ds_creator.already_exists()):
            # print("Found editlog pivoted")
            unused_variable = None
        else:
            # print("No editlog pivoted found, creating it...")
            editlog_pivoted_ds_creator.with_store_into(connection=self.__connection_name__)
            editlog_pivoted_ds_creator.create()
            self.editlog_pivoted_ds = Dataset(self.editlog_pivoted_ds_name, self.project_key)
            cols = self.primary_keys + self.editable_column_names + ["last_edit_date"]
            editlog_pivoted_df = DataFrame(columns=cols)
            self.editlog_pivoted_ds.write_schema(editlog_pivoted_ds_schema)
            self.editlog_pivoted_ds.write_dataframe(editlog_pivoted_df)
            # print("Done.")

        pivot_recipe_name = "compute_" + self.editlog_pivoted_ds_name
        pivot_recipe_creator = DSSRecipeCreator("CustomCode_pivot-editlog", pivot_recipe_name, self.project)
        if (recipe_already_exists(pivot_recipe_name, self.project)):
            # print("Found recipe to create editlog pivoted")
            pivot_recipe = self.project.get_recipe(pivot_recipe_name)
        else:
            # print("No recipe to create editlog pivoted, creating it...")
            pivot_recipe = pivot_recipe_creator.create()
            pivot_settings = pivot_recipe.get_settings()
            pivot_settings.add_input("editlog", self.editlog_ds_name)
            pivot_settings.add_output("editlog_pivoted", self.editlog_pivoted_ds_name)
            pivot_settings.custom_fields["webapp_url"] = self.webapp_url
            pivot_settings.save()
            # print("Done.")

        edited_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.edited_ds_name)
        if (edited_ds_creator.already_exists()):
            # print("Found edited dataset")
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
        else:
            # print("No edited dataset found, creating it...")
            edited_ds_creator.with_store_into(connection=self.__connection_name__)
            edited_ds_creator.create()
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
            edited_df = DataFrame(columns=self.edited_df_cols)
            self.edited_ds.write_schema(edited_ds_schema)
            self.edited_ds.write_dataframe(edited_df)
            # print("Done.")

        merge_recipe_name = "compute_" + self.edited_ds_name
        merge_recipe_creator = DSSRecipeCreator("CustomCode_merge-edits", merge_recipe_name, self.project)
        if (recipe_already_exists(merge_recipe_name, self.project)):
            # print("Found recipe to create edited dataset")
            merge_recipe = self.project.get_recipe(merge_recipe_name)
        else:
            # print("No recipe to create edited dataset, creating it...")
            merge_recipe = merge_recipe_creator.create()
            merge_settings = merge_recipe.get_settings()
            merge_settings.add_input("original", self.original_ds_name)
            merge_settings.add_input("editlog_pivoted", self.editlog_pivoted_ds_name)
            merge_settings.add_output("edited", self.edited_ds_name)
            merge_settings.custom_fields["webapp_url"] = self.webapp_url
            merge_settings.save()
            # print("Done.")

    def load_data(self):
        self.__original_df__ = self.original_ds.get_dataframe()[self.edited_df_cols]
        self.__edited_df_indexed__ = merge_edits(
                                        self.__original_df__,
                                        pivot_editlog(
                                            self.editlog_ds,
                                            self.primary_keys,
                                            self.editable_column_names
                                        ),
                                        self.primary_keys
                                     )
        # self.__edited_df_indexed__ = self.__extend_with_lookup_columns__(self.__edited_df_indexed__)
        self.__edited_df_indexed__.set_index(self.primary_keys, inplace=True) # index makes it easier to id values in the DataFrame

    def __init__(self, original_ds_name, primary_keys=None, editable_column_names=None, editschema_manual={}, project_key=None, editschema=None):

        self.original_ds_name = original_ds_name
        if (project_key is None): self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        else: self.project_key = project_key
        self.__init_webapp_url__()
        client = api_client()
        self.project = client.get_project(self.project_key)
        self.original_ds = Dataset(self.original_ds_name, self.project_key)

        self.editlog_ds_name = self.original_ds_name + "_editlog"
        self.editlog_pivoted_ds_name = self.editlog_ds_name + "_pivoted"
        self.edited_ds_name = self.original_ds_name + "_edited"

        self.__connection_name__ = self.original_ds.get_config().get("params").get("connection")
        if self.__connection_name__==None: self.__connection_name__ = "filesystem_managed"
        
        self.__schema__ = self.original_ds.get_config().get("schema").get("columns")
        self.__schema_df__ = DataFrame(data=self.__schema__).set_index("name") # turn __schema__ into a DataFrame with "name" as index, and thus easily get the type for a given name
        if (primary_keys):
            self.primary_keys = primary_keys
        # else: it's in the custom field
        if (editable_column_names):
            self.editable_column_names = editable_column_names
        self.editschema_manual = editschema_manual
        if (editschema):
            self.primary_keys = get_primary_keys(editschema)
            self.editable_column_names = get_editable_column_names(editschema)
            self.editschema_manual = editschema
        if self.editschema_manual!={}:
            self.editschema_manual_df = DataFrame(data=self.editschema_manual).set_index("name")
        else:
            self.editschema_manual_df = DataFrame(data=self.editschema_manual) # this will be an empty dataframe

        self.display_column_names = [col.get("name") for col in self.__schema__ if col.get("name") not in self.primary_keys + self.editable_column_names]
        self.edited_df_cols = self.primary_keys + self.display_column_names + self.editable_column_names

        # make sure that original dataset has up-to-date custom fields (editlog and datasets/recipes that follow may not - TODO: change this?)
        self.__save_custom_fields__(self.original_ds_name)
        self.__setup_linked_records__()
        self.__setup_editlog__()
        self.__setup_editlog_downstream__()

        self.load_data()

        self.__ns__ = Namespace("myNamespace", "tabulator") # used to reference javascript functions in custom_tabulator.js



    def get_edited_df_indexed(self):
        return self.__edited_df_indexed__

    def get_edited_df(self):
        return self.get_edited_df_indexed().reset_index()

    def get_data_tabulator(self):
        return self.get_edited_df().to_dict('records')



    def __get_column_tabulator_type__(self, col_name):
        # Determine column type as string, boolean, boolean_tick, or number
        # - based on the type given in editschema_manual, if any
        # - the dataset's schema, otherwise
        ###

        t_type = "string" # default type
        if not self.editschema_manual_df.empty and "type" in self.editschema_manual_df.columns and col_name in self.editschema_manual_df.index:
            editschema_manual_type = self.editschema_manual_df.loc[col_name, "type"]
        else:
            editschema_manual_type = None

        if editschema_manual_type and editschema_manual_type==editschema_manual_type: # this tests that 1) editschema_manual_type isn't None, and 2) it isn't a nan
            t_type = editschema_manual_type
        else:
            if "meaning" in self.__schema_df__.columns.to_list():
                schema_meaning = self.__schema_df__.loc[col_name, "meaning"]
            else:
                schema_meaning = None
            # If a meaning has been defined, we use it to infer t_type
            if schema_meaning and schema_meaning==schema_meaning:
                if schema_meaning=="Boolean": t_type = "boolean"
                if schema_meaning=="DoubleMeaning" or schema_meaning=="LongMeaning" or schema_meaning=="IntMeaning": t_type = "number"
            else:
                schema_type = self.__schema_df__.loc[col_name, "type"] # type coming from schema
                if schema_type=="boolean": t_type = "boolean"
                if schema_type in ["tinyint", "smallint", "int", "bigint", "float", "double"]: t_type = "number"

        return t_type

    def __get_column_tabulator_formatter__(self, t_type):
        # IDEA: improve this code with a dict to do matching (instead of if/else)?
        t_col = {}
        if t_type=="boolean":
            t_col["formatter"] = "tickCross"
            t_col["formatterParams"] = {"allowEmpty": True}
            t_col["hozAlign"] = "center"
            t_col["headerFilterParams"] = {"tristate": True}
        elif t_type=="boolean_tick":
            t_col["formatter"] = "tickCross"
            t_col["formatterParams"] = {"allowEmpty": True, "crossElement": " "}
            t_col["hozAlign"] = "center"
        elif t_type=="number":
            t_col["headerFilter"] = self.__ns__("minMaxFilterEditor")
            t_col["headerFilterFunc"] = self.__ns__("minMaxFilterFunction")
            t_col["headerFilterLiveFilter"] = False
        return t_col

    def __get_column_tabulator_editor__(self, t_type):
        t_col = {}
        if t_type=="boolean":
            t_col["editor"] = "list"
            t_col["editorParams"] = {"values": {
                "true": "True",
                "false": "False",
                "": "(empty)"
            }}
            t_col["headerFilter"] = "input"
            t_col["headerFilterParams"] = {}
        elif t_type=="boolean_tick":
            t_col["editor"] = "tickCross"
        elif t_type=="number":
            t_col["editor"] = "number"
        else:
            t_col["editor"] = "input"
        return t_col

    def __get_values_from_linked_ds__(self, linked_ds_name, linked_ds_key, linked_ds_label, linked_ds_lookup_columns):

        linked_columns = [linked_ds_key]
        if (linked_ds_label!=linked_ds_key):
            linked_columns += [linked_ds_label]
        
        linked_df = Dataset(linked_ds_name).get_dataframe()

        # Concatenate lookup column values (if any) into a description column
        if linked_ds_lookup_columns!=[]:
            linked_df["description"] = linked_df.apply(lambda row: " - ".join(row[linked_ds_lookup_columns]), axis=1) # TODO: fix this in case values for the lookup columns aren't defined (nan)
            linked_columns += ["description"]

        return linked_df[linked_columns].sort_values(linked_ds_label)

    def __get_column_tabulator_editor_linked_record__(self, linked_record_name):
        """Define Tabulator editor settings for a column whose type is linked record"""
        
        # Use a list editor
        t_col = {}
        t_col["editor"] = "list"
        t_col["editorParams"] = {
            # "freetext": True,
            "listOnEmpty": False,
            "clearable": True,
            "placeholderEmpty": "no results",
            "placeholderLoading": "loading"
        }

        # If lookup columns have been provided, use an item formatter in the editor
        linked_ds_lookup_columns = self.linked_records_df.loc[linked_record_name, "ds_lookup_columns"]
        if linked_ds_lookup_columns!=[]:
            t_col["editorParams"]["itemFormatter"] = self.__ns__("itemFormatter")

        # Define possible values in the list
        linked_ds_name = self.linked_records_df.loc[linked_record_name, "ds_name"]
        if (True): # TODO: implement a condition to see if the linked dataset is big
            # TODO: don't need ds_key and ds_label here? (they're used when dataset is loaded in memory)
            t_col["editorParams"]["valuesURL"] = "lookup/" + linked_ds_name
            
        else:
            # The dataset can be loaded in memory
            linked_ds_key = self.linked_records_df.loc[linked_record_name, "ds_key"]
            linked_ds_label = self.linked_records_df.loc[linked_record_name, "ds_label"]
            values_df = self.__get_values_from_linked_ds__(linked_ds_name, linked_ds_key, linked_ds_label, linked_ds_lookup_columns)
            if (linked_ds_label==linked_ds_key):
                editor_values_param = values_df[linked_ds_key].to_list()
            else:
                # A label column was provided: use labels in the editor...
                editor_values_param = values_df.rename(columns={linked_ds_key: "value", linked_ds_label: "label"}).to_dict("records")
                # ... and in the formatter too, instead of the keys; for this we provide a "lookup" parameter which looks like this: {"key1": "label1", "key2": "label2", "null": ""}
                t_col["formatter"] = "lookup"
                formatter_lookup_param = values_df.set_index(linked_ds_key)[linked_ds_label].to_dict()
                formatter_lookup_param["null"] = "" # use empty label when key is missing
                t_col["formatterParams"] = formatter_lookup_param
            t_col["editorParams"]["values"] = editor_values_param
            t_col["editorParams"]["autocomplete"] = True
            t_col["editorParams"]["filterDelay"] = 300
            t_col["editorParams"]["filterFunc"] = self.__ns__("filterFunc")
        
        return t_col

    def get_columns_tabulator(self, freeze_editable_columns=False):
        # Columns' settings for tabulator

        t_cols = []
        for col_name in self.edited_df_cols:

            # Properties to be shared by all columns
            t_col = {"field": col_name, "headerFilter": True, "resizable": True, "headerContextMenu": self.__ns__("headerMenu")}

            # Define formatter and header filters based on type
            t_type = self.__get_column_tabulator_type__(col_name)
            t_col.update(self.__get_column_tabulator_formatter__(t_type))
            if col_name in self.primary_keys: t_col["frozen"] = True

            # Define editor, if it's an editable column
            if col_name in self.editable_column_names:
                if (freeze_editable_columns): t_col["frozen"] = True # freeze to the right
                if col_name in self.linked_record_names:
                    t_col.update(self.__get_column_tabulator_editor_linked_record__(col_name))
                else:
                    t_col.update(self.__get_column_tabulator_editor__(t_type))

            t_cols.append(t_col)

        return t_cols



    def add_edit(self, primary_key_values, column_name, value, user):
        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.__schema__:
            if (col["name"]==column_name):
                if type(value)==str and col.get("type")=="boolean":
                    if (value==""):
                        value = None
                    else:
                        value = str(loads(value.lower()))
                break
        
        # store value as a string, unless it's None
        if (value!=None): value = str(value)

        # add to the editlog
        self.editlog_ds.write_dataframe(DataFrame(data={
            "key": [str(primary_key_values)],
            "column_name": [column_name],
            "value": [value],
            "date": [datetime.now(timezone("UTC")).isoformat()],
            "user": [user]
        }))

        # Note: do we want ees to maintain a live, up-to-date copy of the editlog, or the editlog pivoted, or the edited dataset? Here we choose the latter, but this may change if the original dataset doesn't fit in memory.

        # Update live copy of the edited dataset
        self.__edited_df_indexed__.loc[primary_key_values, column_name] = value # Might need to change primary_key_values from a list to a tuple — see this example: df.loc[('cobra', 'mark i'), 'shield'] from https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.loc.html ?

        # Update lookup columns if a linked record was edited
        # for linked_record in self.linked_records:
        #     if (column_name==linked_record["name"]):
        #         # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
        #         lookup_values = self.__get_lookup_values__(linked_record, value)

        #         # Update table_data with lookup values — note that column names are different in table_data and in the linked record's table
        #         for lookup_column in linked_record["lookup_columns"]:
        #             self.__edited_df_indexed__.loc[primary_key_values, lookup_column["name"]] = lookup_values[lookup_column["linked_ds_column_name"]].iloc[0]
        
        info = f"""Updated column {column_name} where {self.primary_keys} is {primary_key_values}. New value: {value}."""
        print(info)
        return info

    def add_edit_tabulator(self, cell, user):
        return self.add_edit(
            tabulator_row_key_values(cell["row"], self.primary_keys),
            cell["column"],
            cell["value"],
            user
        )
