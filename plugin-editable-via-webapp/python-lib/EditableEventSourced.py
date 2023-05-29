import logging
from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from dataiku_utils import recipe_already_exists
from pandas import DataFrame
from commons import get_user_identifier, get_original_df, get_editlog_df, write_empty_editlog, get_editlog_ds_schema, get_display_column_names, merge_edits_from_log_pivoted_df, pivot_editlog, get_key_values_from_dict
from webapp_utils import find_webapp_id, get_webapp_json
from editschema_utils import get_primary_keys, get_editable_column_names
from DatasetSQL import DatasetSQL
from os import getenv
from json import loads
from datetime import datetime
from pytz import timezone
from re import sub

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
            editlog_df = self.get_editlog_df()
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

        # make sure that editlog has the right custom field values
        self.__save_custom_fields__(self.editlog_ds_name)

    def __setup_editlog_downstream__(self):
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

        self.schema_columns = self.original_ds.get_config().get("schema").get("columns")
        # turn __schema__ into a DataFrame with "name" as index, and thus easily get the type for a given name
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
                for linked_record in self.linked_records:
                    linked_record["ds"] = DatasetSQL(linked_record["ds_name"], self.project_key)
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

        self.display_column_names = get_display_column_names(
            self.schema_columns, self.primary_keys, self.editable_column_names)

        # make sure that original dataset has up-to-date custom fields (editlog and datasets/recipes that follow may not - TODO: change this?)
        self.__save_custom_fields__(self.original_ds_name)
        self.__setup_editlog__()
        self.__setup_editlog_downstream__()

    def get_original_df(self):
        """Get original data without edits"""
        return get_original_df(self.original_ds)

    def get_editlog_df(self):
        return get_editlog_df(self.editlog_ds)

    def empty_editlog(self):
        self.editlog_ds.spec_item["appendMode"] = False
        write_empty_editlog(self.editlog_ds)

    def get_edited_df_indexed(self):
        return self.get_edited_df().set_index(self.primary_keys)

    def get_edited_df(self):
        """Get original data with edited values"""
        return merge_edits_from_log_pivoted_df(
            self.original_ds,
            self.get_edited_cells_df()
        )

    def get_edited_cells_df_indexed(self):
        return self.get_edited_cells_df().set_index(self.primary_keys)

    def get_edited_cells_df(self):
        """Get only rows and columns that were edited"""
        return pivot_editlog(
            self.editlog_ds,
            self.primary_keys,
            self.editable_column_names
        )

    def get_row(self, primary_keys):
        """
        Read a row that was created, updated or deleted (as indicated by the editlog)

        Params:
        - primary_keys: dictionary containing values for all primary keys defined in the initial data editing setup; the set of values must be unique. Example:
            ```python
            {
                "key1": "cat",
                "key2": "2022-12-21",
            }
            ```

        Returns: single-row dataframe containing the values of editable columns.

        Notes:
        - If some rows of the dataset were created, then by definition all columns are editable (including primary keys) .
        - If no row was created, editable columns are those defined in the initial data editing setup.
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        # TODO: implementation can be optimized, so that we only load one row of the original dataset, and only load rows of the editlog that match the provided primary key values
        # TODO: read row that was not edited too! This can be done via Dataiku API
        return self.get_edited_cells_df_indexed().loc[key]

    def __log_edit__(self, key, column, value, action="update"):
        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.schema_columns:
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

        if column in self.editable_column_names or action == "delete":

            # add to the editlog
            self.editlog_ds.spec_item["appendMode"] = True
            self.editlog_ds.write_dataframe(DataFrame(data={
                "action": [action],
                "key": [str(key)],
                "column_name": [column],
                "value": [value_string],
                "date": [datetime.now(timezone("UTC")).isoformat()],
                "user": [get_user_identifier()]
            }))
            info = f"""Updated column {column} where {self.primary_keys} is {key}. New value: {value}."""

        else:

            info = f"""{column} isn't an editable column"""

        logging.info(info)
        return info

    def create_row(self, primary_keys, column_values):
        """
        Create a new row.

        Params:
        - primary_keys: dictionary containing values for all primary keys (the set of values must be unique). Example:
            ```python
            {
                "id": "My new unique id"
            }
            ```
        - column_values: dictionary containing values for all other columns. Example:
            ```python
            {
                "col1": "hey",
                "col2": 42,
                "col3": true
            }
            ```

        Note: this method doesn't implement data validation / it doesn't check that the values are allowed for the specified columns.
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        for col in column_values.keys():
            self.__log_edit__(key=key, column=col, value=column_values.get(
                col), action="create")
        return "Created row"

    def update_row(self, primary_keys, column, value):
        """
        Update a row

        Params:
        - primary_keys: dictionary containing primary key(s) value(s) that identify the row to update (see get_row method)
        - column: name of the column to update
        - value: value to set for the cell identified by key and column
        ```

        Note: this method doesn't implement data validation / it doesn't check that the value is allowed for the specified column.
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        return self.__log_edit__(key, column, value, action="update")

    def delete_row(self, primary_keys):
        """
        Delete a row

        Params:
        - primary_keys: dictionary containing primary key(s) value(s) that identify the row to delete (see get_row method)
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        self.__log_edit__(key, None, None, action="delete")
        return f"""Deleted row"""
