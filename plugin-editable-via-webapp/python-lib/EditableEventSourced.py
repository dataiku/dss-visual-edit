import logging
from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from pandas import DataFrame
from commons import *
from os import getenv
from json import loads
from datetime import datetime
from pytz import timezone
from dash_extensions.javascript import Namespace
from urllib.parse import urlparse
from re import sub


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
        if (self.webapp_url):
            settings.custom_fields["webapp_url"] = self.webapp_url
        settings.save()

    def __init_webapp_url__(self):
        try:
            webapp_id = find_webapp_id(self.original_ds_name)
            webapp_name = sub(
                r'[\W_]+', '-', get_webapp_json(webapp_id).get("name").lower())
            self.webapp_url = f"/projects/{self.project_key}/webapps/{webapp_id}_{webapp_name}/edit"
            self.webapp_url_public = f"/public-webapps/{self.project_key}/{webapp_id}/"
        except:
            self.webapp_url = None
            self.webapp_url_public = "/"

    

    def __setup_editlog__(self):
        editlog_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.editlog_ds_name)
        if (editlog_ds_creator.already_exists()):
            logging.debug("Found editlog")
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            editlog_df = get_editlog_df(self.editlog_ds)
            if (editlog_df.empty):
                # Make sure that the dataset's configuration is valid by writing an empty dataframe.
                # (The editlog dataset might already exist and have a schema, but its configuration might be invalid, for instance when the project was exported to a bundle and deployed to automation, and when using a SQL connection: the dataset exists but no table was created.)
                write_empty_editlog(self.editlog_ds)
        else:
            logging.debug("No editlog found, creating it...")
            editlog_ds_creator.with_store_into(
                connection=self.__connection_name__)
            editlog_ds_creator.create()
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            self.editlog_ds.write_schema(get_editlog_ds_schema())
            write_empty_editlog(self.editlog_ds)
            logging.debug("Done.")

        # make sure that editlog is in append mode
        self.editlog_ds.spec_item["appendMode"] = True

        # make sure that editlog has the right custom field values
        self.__save_custom_fields__(self.editlog_ds_name)

    def __setup_editlog_downstream__(self):
        editlog_pivoted_ds_schema, edited_ds_schema = get_editlog_pivoted_ds_schema(self.__schema__, self.primary_keys, self.editable_column_names)
        editlog_pivoted_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.editlog_pivoted_ds_name)
        if (editlog_pivoted_ds_creator.already_exists()):
            logging.debug("Found editlog pivoted")
            unused_variable = None
        else:
            logging.debug("No editlog pivoted found, creating it...")
            editlog_pivoted_ds_creator.with_store_into(
                connection=self.__connection_name__)
            editlog_pivoted_ds_creator.create()
            self.editlog_pivoted_ds = Dataset(
                self.editlog_pivoted_ds_name, self.project_key)
            cols = self.primary_keys + \
                self.editable_column_names + ["last_edit_date", "last_action", "first_action"]
            editlog_pivoted_df = DataFrame(columns=cols)
            self.editlog_pivoted_ds.write_schema(editlog_pivoted_ds_schema)
            self.editlog_pivoted_ds.write_dataframe(editlog_pivoted_df, infer_schema=False)
            logging.debug("Done.")

        pivot_recipe_name = "compute_" + self.editlog_pivoted_ds_name
        pivot_recipe_creator = DSSRecipeCreator(
            "CustomCode_pivot-editlog", pivot_recipe_name, self.project)
        if (recipe_already_exists(pivot_recipe_name, self.project)):
            logging.debug("Found recipe to create editlog pivoted")
            pivot_recipe = self.project.get_recipe(pivot_recipe_name)
        else:
            logging.debug(
                "No recipe to create editlog pivoted, creating it...")
            pivot_recipe = pivot_recipe_creator.create()
            pivot_settings = pivot_recipe.get_settings()
            pivot_settings.add_input("editlog", self.editlog_ds_name)
            pivot_settings.add_output(
                "editlog_pivoted", self.editlog_pivoted_ds_name)
            pivot_settings.custom_fields["webapp_url"] = self.webapp_url
            pivot_settings.save()
            logging.debug("Done.")

        edited_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.edited_ds_name)
        if (edited_ds_creator.already_exists()):
            logging.debug("Found edited dataset")
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
        else:
            logging.debug("No edited dataset found, creating it...")
            edited_ds_creator.with_store_into(
                connection=self.__connection_name__)
            edited_ds_creator.create()
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
            edited_df = DataFrame(columns=self.edited_df_cols)
            self.edited_ds.write_schema(edited_ds_schema)
            self.edited_ds.write_dataframe(edited_df, infer_schema=False)
            logging.debug("Done.")

        merge_recipe_name = "compute_" + self.edited_ds_name
        merge_recipe_creator = DSSRecipeCreator(
            "CustomCode_merge-edits", merge_recipe_name, self.project)
        if (recipe_already_exists(merge_recipe_name, self.project)):
            logging.debug("Found recipe to create edited dataset")
            merge_recipe = self.project.get_recipe(merge_recipe_name)
        else:
            logging.debug("No recipe to create edited dataset, creating it...")
            merge_recipe = merge_recipe_creator.create()
            merge_settings = merge_recipe.get_settings()
            merge_settings.add_input("original", self.original_ds_name)
            merge_settings.add_input(
                "editlog_pivoted", self.editlog_pivoted_ds_name)
            merge_settings.add_output("edited", self.edited_ds_name)
            merge_settings.custom_fields["webapp_url"] = self.webapp_url
            merge_settings.save()
            logging.debug("Done.")

    def __init__(self, original_ds_name, primary_keys=None, editable_column_names=None, linked_records={}, editschema_manual={}, project_key=None, editschema=None):

        self.original_ds_name = original_ds_name
        if (project_key is None):
            self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        else:
            self.project_key = project_key
        self.__init_webapp_url__()
        client = api_client()
        self.project = client.get_project(self.project_key)
        self.original_ds = Dataset(self.original_ds_name, self.project_key)

        self.editlog_ds_name = self.original_ds_name + "_editlog"
        self.editlog_pivoted_ds_name = self.editlog_ds_name + "_pivoted"
        self.edited_ds_name = self.original_ds_name + "_edited"

        self.__connection_name__ = self.original_ds.get_config().get(
            "params").get("connection")
        if self.__connection_name__ == None:
            self.__connection_name__ = "filesystem_managed"

        self.__schema__ = self.original_ds.get_config().get("schema").get("columns")
        # turn __schema__ into a DataFrame with "name" as index, and thus easily get the type for a given name
        self.__schema_df__ = DataFrame(data=self.__schema__).set_index("name")
        if (primary_keys):
            self.primary_keys = primary_keys
        # else: it's in the custom field
        if (editable_column_names):
            self.editable_column_names = editable_column_names
        if (linked_records):
            self.linked_records = linked_records
            if (len(self.linked_records) > 0):
                self.linked_records_df = DataFrame(
                    data=self.linked_records).set_index("name")
        self.editschema_manual = editschema_manual
        if (editschema):
            self.primary_keys = get_primary_keys(editschema)
            self.editable_column_names = get_editable_column_names(editschema)
            self.editschema_manual = editschema
        if self.editschema_manual != {}:
            self.editschema_manual_df = DataFrame(
                data=self.editschema_manual).set_index("name")
        else:
            self.editschema_manual_df = DataFrame(
                data=self.editschema_manual)  # this will be an empty dataframe

        display_column_names = get_display_column_names(self.__schema__, self.primary_keys, self.editable_column_names)
        self.edited_df_cols = self.primary_keys + display_column_names + self.editable_column_names

        # make sure that original dataset has up-to-date custom fields (editlog and datasets/recipes that follow may not - TODO: change this?)
        self.__save_custom_fields__(self.original_ds_name)
        self.__setup_editlog__()
        self.__setup_editlog_downstream__()

        # used to reference javascript functions in custom_tabulator.js
        self.__ns__ = Namespace("myNamespace", "tabulator")

        self.edited_cells_df = pivot_editlog(
            self.editlog_ds,
            self.primary_keys,
            self.editable_column_names
        )

    def get_edited_df_indexed(self):
        return self.get_edited_df().set_index(self.primary_keys)
        
    def get_edited_df(self):
        return merge_edits_from_log_pivoted_df(self.original_ds, self.edited_cells_df)

    def get_data_tabulator(self):
        # This loads the original dataset, the editlog, and replays edits
        return self.get_edited_df().to_dict('records')

    def __get_column_tabulator_type__(self, col_name):
        # Determine column type as string, boolean, boolean_tick, or number
        # - based on the type given in editschema_manual, if any
        # - the dataset's schema, otherwise
        ###

        t_type = "string"  # default type
        if not self.editschema_manual_df.empty and "type" in self.editschema_manual_df.columns and col_name in self.editschema_manual_df.index:
            editschema_manual_type = self.editschema_manual_df.loc[col_name, "type"]
        else:
            editschema_manual_type = None

        # this tests that 1) editschema_manual_type isn't None, and 2) it isn't a nan
        if editschema_manual_type and editschema_manual_type == editschema_manual_type:
            t_type = editschema_manual_type
        else:
            if "meaning" in self.__schema_df__.columns.to_list():
                schema_meaning = self.__schema_df__.loc[col_name, "meaning"]
            else:
                schema_meaning = None
            # If a meaning has been defined, we use it to infer t_type
            if schema_meaning and schema_meaning == schema_meaning:
                if schema_meaning == "Boolean":
                    t_type = "boolean"
                if schema_meaning == "DoubleMeaning" or schema_meaning == "LongMeaning" or schema_meaning == "IntMeaning":
                    t_type = "number"
                if schema_meaning == "Date":
                    t_type = "date"
            else:
                # type coming from schema
                schema_type = self.__schema_df__.loc[col_name, "type"]
                if schema_type == "boolean":
                    t_type = "boolean"
                if schema_type in ["tinyint", "smallint", "int", "bigint", "float", "double"]:
                    t_type = "number"
                if schema_type == "date":
                    t_type = "date"

        return t_type

    def __get_column_tabulator_formatter__(self, t_type):
        # IDEA: improve this code with a dict to do matching (instead of if/else)?
        t_col = {}
        if t_type == "boolean":
            t_col["formatter"] = "tickCross"
            t_col["formatterParams"] = {"allowEmpty": True}
            t_col["hozAlign"] = "center"
            t_col["headerFilterParams"] = {"tristate": True}
        elif t_type == "boolean_tick":
            t_col["formatter"] = "tickCross"
            t_col["formatterParams"] = {
                "allowEmpty": True, "crossElement": " "}
            t_col["hozAlign"] = "center"
        elif t_type == "number":
            t_col["headerFilter"] = self.__ns__("minMaxFilterEditor")
            t_col["headerFilterFunc"] = self.__ns__("minMaxFilterFunction")
            t_col["headerFilterLiveFilter"] = False
        elif t_type == "date":
            t_col["formatter"] = "datetime"
            t_col["formatterParams"] = {
                "inputFormat": "iso",
                "outputFormat": "yyyy-MM-dd"
            }
            t_col["headerFilterParams"] = {"format": "yyyy-MM-dd"}
        return t_col

    def __get_column_tabulator_editor__(self, t_type):
        t_col = {}
        if t_type == "boolean":
            t_col["editor"] = "list"
            t_col["editorParams"] = {"values": {
                "true": "True",
                "false": "False",
                "": "(empty)"
            }}
            t_col["headerFilter"] = "input"
            t_col["headerFilterParams"] = {}
        elif t_type == "boolean_tick":
            t_col["editor"] = "tickCross"
        elif t_type == "number":
            t_col["editor"] = "number"
        elif t_type == "date":
            t_col["editor"] = "date"
            t_col["editorParams"] = {"format": "yyyy-MM-dd"}
        else:
            t_col["editor"] = "input"
        return t_col

    def __get_column_tabulator_editor_linked_record__(self, linked_record_name):
        """Define Tabulator editor settings for a column whose type is linked record"""

        # Use a list editor
        t_col = {}
        t_col["editor"] = "list"
        t_col["editorParams"] = {
            "autocomplete": True,
            "filterDelay": 300,
            # "freetext": True,
            "listOnEmpty": False,
            "clearable": True
        }

        # If lookup columns have been provided, use an item formatter in the editor
        linked_ds_lookup_columns = self.linked_records_df.loc[linked_record_name,
                                                              "ds_lookup_columns"]
        if linked_ds_lookup_columns != []:
            t_col["editorParams"]["itemFormatter"] = self.__ns__(
                "itemFormatter")

        # Define possible values in the list
        linked_ds_name = self.linked_records_df.loc[linked_record_name, "ds_name"]
        linked_ds = self.project.get_dataset(linked_ds_name)
        metrics = linked_ds.compute_metrics(metric_ids=["records:COUNT_RECORDS"])[
            "result"]["computed"]
        for m in metrics:
            if (m["metric"]["metricType"] == "COUNT_RECORDS"):
                count_records = int(m["value"])
        if (count_records > 1000):
            # ds_key and ds_label would normally be used, when loading the linked dataset in memory, but here they will be fetched by the API endpoint who has access to an EditableEventSourced dataset and who's given linked_ds_name in the URL
            logging.debug(
                f"Using API to lookup values in {linked_ds_name} since this dataset has {count_records} rows")
            t_col["editorParams"]["filterRemote"] = True
            t_col["editorParams"]["valuesURL"] = "lookup/" + linked_ds_name

        else:
            # The dataset can be loaded in memory
            logging.debug(
                f"Loading {linked_ds_name} in memory since this dataset has {count_records} rows")
            linked_ds_key = self.linked_records_df.loc[linked_record_name, "ds_key"]
            linked_ds_label = self.linked_records_df.loc[linked_record_name, "ds_label"]
            linked_df = Dataset(linked_ds_name).get_dataframe()
            editor_values_param = get_values_from_linked_df(
                linked_df, linked_ds_key, linked_ds_label, linked_ds_lookup_columns)
            if (linked_ds_label != linked_ds_key):
                # A label column was provided: use labels in the formatter, instead of the keys; for this we provide a "lookup" parameter which looks like this: {"key1": "label1", "key2": "label2", "null": ""}
                t_col["formatter"] = "lookup"
                formatter_lookup_param = linked_df.set_index(
                    linked_ds_key)[linked_ds_label].to_dict()
                # use empty label when key is missing
                formatter_lookup_param["null"] = ""
                t_col["formatterParams"] = formatter_lookup_param
            t_col["editorParams"]["values"] = editor_values_param
            t_col["editorParams"]["filterFunc"] = self.__ns__("filterFunc")

        return t_col

    def get_columns_tabulator(self, freeze_editable_columns=False):
        # Columns' settings for tabulator

        try:
            linked_record_names = self.linked_records_df.index.values.tolist()
        except:
            linked_record_names = []

        t_cols = []
        for col_name in self.edited_df_cols:

            # Properties to be shared by all columns
            t_col = {"field": col_name, "title": col_name, "headerFilter": True,
                     "resizable": True, "headerContextMenu": self.__ns__("headerMenu")}

            # Define formatter and header filters based on type
            t_type = self.__get_column_tabulator_type__(col_name)
            t_col.update(self.__get_column_tabulator_formatter__(t_type))
            if col_name in self.primary_keys:
                t_col["frozen"] = True

            # Define editor, if it's an editable column
            if col_name in self.editable_column_names:
                if (freeze_editable_columns):
                    t_col["frozen"] = True  # freeze to the right
                if col_name in linked_record_names:
                    t_col.update(
                        self.__get_column_tabulator_editor_linked_record__(col_name))
                else:
                    t_col.update(self.__get_column_tabulator_editor__(t_type))

            t_cols.append(t_col)

        return t_cols

    def add_edit(self, key, column, value, user, action="update"):
        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.__schema__:
            if (col["name"] == column):
                if type(value) == str and col.get("type") == "boolean":
                    if (value == ""):
                        value = None
                    else:
                        value = str(loads(value.lower()))
                break

        # store value as a string, unless it's None
        if (value != None):
            value_string = str(value)
        else:
            value_string = value

        if column in self.editable_column_names:

            # add to the editlog (since it's in append mode)
            self.editlog_ds.write_dataframe(DataFrame(data={
                "action": [action],
                "key": [str(key)],
                "column_name": [column],
                "value": [value_string],
                "date": [datetime.now(timezone("UTC")).isoformat()],
                "user": [user]
            }))

            self.edited_cells_df.loc[key, column] = value

            # Update lookup columns if a linked record was edited
            # for linked_record in self.linked_records:
            #     if (column_name==linked_record["name"]):
            #         # Retrieve values of the lookup columns from the linked dataset, for the row corresponding to the edited value (linked_record["ds_key"]==value)
            #         lookup_values = self.__get_lookup_values__(linked_record, value)

            #         # Update table_data with lookup values — note that column names are different in table_data and in the linked record's table
            #         # Might need to change primary_key_values from a list to a tuple — see this example: df.loc[('cobra', 'mark i'), 'shield'] from https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.loc.html ?
            #         for lookup_column in linked_record["lookup_columns"]:
            #             self.__edited_df_indexed__.loc[primary_key_values, lookup_column["name"]] = lookup_values[lookup_column["linked_ds_column_name"]].iloc[0]

            info = f"""Updated column {column} where {self.primary_keys} is {key}. New value: {value}."""
        
        else:

            info = f"""{column} isn't an editable column"""

        logging.info(info)
        return info

    def add_edit_tabulator(self, cell, user):
        return self.add_edit(
            key=get_key_values_from_dict(cell["row"], self.primary_keys),
            column=cell["column"],
            value=cell["value"],
            user=user
        )
