from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from pandas import DataFrame
from commons import get_primary_keys, get_editable_column_names, merge_edits, pivot_editlog, tabulator_row_key_values
from os import getenv
from json5 import loads
from datetime import datetime
from pytz import timezone
from dash_extensions.javascript import Namespace
from urllib.parse import urlparse

def get_lookup_column_names(linked_record):
    lookup_column_names = []
    lookup_column_names_in_linked_ds = []
    for lookup_column in linked_record["lookup_columns"]:
        lookup_column_names.append(lookup_column["name"])
        lookup_column_names_in_linked_ds.append(lookup_column["linked_ds_column_name"])
    return lookup_column_names, lookup_column_names_in_linked_ds

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
        settings.save()

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

        # Second pass to create the lookup columns for each linked record
        # for col in self.editschema_manual:
        #     if col.get("editable_type")=="lookup_column":
        #         for linked_record in self.linked_records:
        #             if linked_record["name"]==col.get("linked_record_col"):
        #                 linked_record["lookup_columns"].append({
        #                     "name": col.get("name"),
        #                     "linked_ds_column_name": col.get("linked_ds_column_name")
        #                 })

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
        _, lookup_column_names_in_linked_ds = get_lookup_column_names(linked_record)
        linked_ds = Dataset(linked_record["ds_name"], self.project_key)
        linked_df = linked_ds.get_dataframe().set_index(linked_record["ds_key"])[lookup_column_names_in_linked_ds]
        # value_cast = linked_record_value
        # if (linked_record["type"] == "int"):
        #    value_cast = int(linked_record_value)
        return linked_df.loc[linked_df.index==linked_record_value]
        # IDEA: add linked_record["linked_key"] as an INDEX to speed up the query

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
            print("Found editlog")
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
        else:
            print("No editlog found, creating it...")
            editlog_ds_creator.with_store_into(connection=self.__connection_name__)
            editlog_ds_creator.create()
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            print("Done.")

        # make sure that editlog is in append mode
        self.editlog_ds.spec_item["appendMode"] = True
        
        # make sure that editlog has the right editschema in its custom field
        self.__save_custom_fields__(self.editlog_ds_name)

    def __setup_editlog_downstream__(self):
        editlog_pivoted_ds_schema, edited_ds_schema = self.__get_editlog_pivoted_ds_schema__()
        editlog_pivoted_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.editlog_pivoted_ds_name)
        if (editlog_pivoted_ds_creator.already_exists()):
            print("Found editlog pivoted")
        else:
            print("No editlog pivoted found, creating it...")
            editlog_pivoted_ds_creator.with_store_into(connection=self.__connection_name__)
            editlog_pivoted_ds_creator.create()
            self.editlog_pivoted_ds = Dataset(self.editlog_pivoted_ds_name, self.project_key)
            cols = self.primary_keys + self.editable_column_names + ["last_edit_date"]
            editlog_pivoted_df = DataFrame(columns=cols)
            self.editlog_pivoted_ds.write_schema(editlog_pivoted_ds_schema)
            self.editlog_pivoted_ds.write_dataframe(editlog_pivoted_df)
            print("Done.")

        pivot_recipe_name = "compute_" + self.editlog_pivoted_ds_name
        pivot_recipe_creator = DSSRecipeCreator("CustomCode_pivot-editlog", pivot_recipe_name, self.project)
        if (recipe_already_exists(pivot_recipe_name, self.project)):
            print("Found recipe to create editlog pivoted")
            pivot_recipe = self.project.get_recipe(pivot_recipe_name)
            self.pivot_settings = pivot_recipe.get_settings()
        else:
            print("No recipe to create editlog pivoted, creating it...")
            pivot_recipe = pivot_recipe_creator.create()
            self.pivot_settings = pivot_recipe.get_settings()
            pivot_settings.add_input("editlog", self.editlog_ds_name)
            pivot_settings.add_output("editlog_pivoted", self.editlog_pivoted_ds_name)
            pivot_settings.save()
            print("Done.")

        edited_ds_creator = DSSManagedDatasetCreationHelper(self.project, self.edited_ds_name)
        if (edited_ds_creator.already_exists()):
            print("Found edited dataset")
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
        else:
            print("No edited dataset found, creating it...")
            edited_ds_creator.with_store_into(connection=self.__connection_name__)
            edited_ds_creator.create()
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
            edited_df = DataFrame(columns=self.edited_df_cols)
            self.edited_ds.write_schema(edited_ds_schema)
            self.edited_ds.write_dataframe(edited_df)
            print("Done.")

        merge_recipe_name = "compute_" + self.edited_ds_name
        merge_recipe_creator = DSSRecipeCreator("CustomCode_merge-edits", merge_recipe_name, self.project)
        if (recipe_already_exists(merge_recipe_name, self.project)):
            print("Found recipe to create edited dataset")
            merge_recipe = self.project.get_recipe(merge_recipe_name)
            self.merge_settings = merge_recipe.get_settings()
        else:
            print("No recipe to create edited dataset, creating it...")
            merge_recipe = merge_recipe_creator.create()
            self.merge_settings = merge_recipe.get_settings()
            merge_settings.add_input("original", self.original_ds_name)
            merge_settings.add_input("editlog_pivoted", self.editlog_pivoted_ds_name)
            merge_settings.add_output("edited", self.edited_ds_name)
            merge_settings.save()
            print("Done.")

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
        client = api_client()
        self.project = client.get_project(self.project_key)
        self.original_ds = Dataset(self.original_ds_name, self.project_key)

        self.editlog_ds_name = self.original_ds_name + "_editlog"
        self.editlog_pivoted_ds_name = self.editlog_ds_name + "_pivoted"
        self.edited_ds_name = self.original_ds_name + "_edited"

        self.__connection_name__ = self.original_ds.get_config().get("params").get("connection")
        self.__schema__ = self.original_ds.get_config().get("schema").get("columns")
        if (primary_keys):
            self.primary_keys = primary_keys
        # else: it's in the custom field
        if (editable_column_names):
            self.editable_column_names = editable_column_names
        self.editschema_manual = editschema_manual
        if (editschema):
            self.primary_keys = get_primary_keys(editschema)
            self.editable_column_names = get_editable_column_names(editschema)
        self.display_column_names = [col.get("name") for col in self.__schema__ if col.get("name") not in self.primary_keys + self.editable_column_names]
        self.edited_df_cols = self.primary_keys + self.display_column_names + self.editable_column_names

        # make sure that original dataset has up-to-date custom fields
        self.__save_custom_fields__(self.original_ds_name)
        self.__setup_linked_records__()
        self.__setup_editlog__()
        self.__setup_editlog_downstream__()
        self.load_data()

    def get_edited_df_indexed(self):
        return self.__edited_df_indexed__

    def get_edited_df(self):
        return self.get_edited_df_indexed().reset_index()

    def get_data_tabulator(self):
        return self.get_edited_df().to_dict('records')

    def get_columns_tabulator(self, freeze_editable_columns=False):
        # Setup columns to be used by data table
        # Add "editor" to editable columns. Possible values include: "input", "textarea", "number", "tickCross", "list". See all options at options http://tabulator.info/docs/5.2/edit.
        # IDEA: improve this code with a dict to do matching (instead of if/else)?
        ns = Namespace("myNamespace", "tabulator")
        t_cols = [] # columns for tabulator
        schema_df = DataFrame(data=self.__schema__).set_index("name") # turn __schema__ into a DataFrame with "name" as index, and thus easily get the type for a given name
        if (len(self.linked_records) > 0):
            linked_records_df = DataFrame(data=self.linked_records).set_index("name")
        for col_name in self.edited_df_cols:
            t_col = {"field": col_name, "headerFilter": True, "resizable": True, "headerContextMenu": ns("headerMenu")}
            t_type = "string"
            col_type = schema_df.loc[col_name, "type"]
            if "meaning" in schema_df.columns.to_list():
                col_meaning = schema_df.loc[col_name, "meaning"]
            else:
                col_meaning = None
            if col_meaning and col_meaning==col_meaning: # this tests that col_meaning isn't None and that it isn't a nan
                if col_meaning=="Boolean": t_type = "boolean"
                if col_meaning=="DoubleMeaning" or col_meaning=="LongMeaning" or col_meaning=="IntMeaning": t_type = "number"
            else:
                if col_type=="boolean": t_type = "boolean"
                if col_type in ["tinyint", "smallint", "int", "bigint", "float", "double"]: t_type = "number"
            if t_type=="boolean":
                t_col["formatter"] = "tickCross"
                t_col["formatterParams"] = {"allowEmpty": True}
                t_col["hozAlign"] = "center"
                t_col["headerFilterParams"] = {"tristate": True}
                # t_col["headerFilterEmptyCheck"] = "function(value){return value === null;}"
            if t_type=="number":
                t_col["headerFilter"] = ns("minMaxFilterEditor")
                t_col["headerFilterFunc"] = ns("minMaxFilterFunction")
                t_col["headerFilterLiveFilter"] = False

            if col_name in self.editable_column_names:
                t_col["title"] = "🖊 " + col_name
                if (freeze_editable_columns): t_col["frozen"] = True # freeze editable columns to the right
                
                # if col.get("type")=="list": # detect if it's categorical - via the count of unique values?
                #    t_col["editor"] = "list"
                #    t_col["editorParams"] = {"values": col["values"]}

                if col_name in self.linked_record_names:
                    linked_ds_name = linked_records_df.loc[col_name, "ds_name"]
                    linked_ds_key = linked_records_df.loc[col_name, "ds_key"]
                    linked_ds_label = linked_records_df.loc[col_name, "ds_label"]
                    linked_ds_lookup_columns = linked_records_df.loc[col_name, "ds_lookup_columns"]
                    linked_columns = [linked_ds_key]
                    if (linked_ds_label!=linked_ds_key):
                        linked_columns += [linked_ds_label]
                    linked_df = Dataset(linked_ds_name).get_dataframe()
                    linked_df["description"] = linked_df.apply(lambda row: " - ".join(row[linked_ds_lookup_columns]), axis=1)
                    linked_columns += ["description"]
                    values_df = linked_df[linked_columns]
                    if (linked_ds_label!=linked_ds_key):
                        values_df.sort_values(linked_ds_label, inplace=True)
                        formatter_lookup_param = values_df.set_index(linked_ds_key)[linked_ds_label].to_dict()
                        formatter_lookup_param["null"] = ""
                        t_col["formatter"] = "lookup"
                        t_col["formatterParams"] = formatter_lookup_param

                    editor_values_param = values_df.rename(columns={linked_ds_key:"value", linked_ds_label:"label"}).to_dict("records")
                    t_col["editor"] = "list"
                    t_col["editorParams"] = {
                        "values": editor_values_param,
                        "autocomplete": True,
                        "freetext": True,
                        "filterFunc": ns("filterFunc"),
                        "listOnEmpty": False,
                        "clearable": True,
                        "itemFormatter": ns("itemFormatter")
                        # "placeholderEmpty": "empty",
                        # "placeholderLoading": "loading"
                    }
                else:
                    if t_type=="boolean":
                        t_col["editor"] = t_col["formatter"]
                        t_col["editorParams"] = {"tristate": True}
                        t_col["headerFilter"] = "input"
                        t_col["headerFilterParams"] = {}
                    elif t_type=="number":
                        t_col["editor"] = "number"
                    else:
                        t_col["editor"] = "input"
            else:
                t_col["title"] = col_name
                if col_name in self.primary_keys:
                    t_col["frozen"] = True

            t_cols.append(t_col)
        return t_cols

    def add_edit(self, primary_key_values, column_name, value, user):
        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.__schema__:
            if (col["name"]==column_name):
                if type(value)==str and col.get("type")=="boolean":
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

    def set_url(self):
        from commons import find_webapp_id, get_webapp_json
        webapp_id = find_webapp_id(self.original_ds_name)
        webapp_name = get_webapp_json(id).get("name")
        url = f"/projects/{self.project_key}/webapps/{webapp_id}_{webapp_name}/edit"

        # see save_custom_fields method for inspiration

        # editlog
        # pivoted
        # edited
        # editlog_ds.get_config()["customFields"]["primary_keys"]
        self.pivot_settings.custom_fields["webapp_url"] = url
        self.pivot_settings.save()
        self.merge_settings.custom_fields["webapp_url"] = url
        self.merge_settings.save()
