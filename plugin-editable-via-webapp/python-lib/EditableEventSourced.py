import logging
from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from dataiku_utils import recipe_already_exists
from pandas import DataFrame
from commons import (
    get_user_identifier,
    get_original_df,
    get_editlog_df,
    write_empty_editlog,
    get_display_column_names,
    merge_edits_from_log_pivoted_df,
    pivot_editlog,
    get_key_values_from_dict,
)
from webapp_utils import find_webapp_id, get_webapp_json
from editschema_utils import get_primary_keys, get_editable_column_names
from DatasetSQL import DatasetSQL
from os import getenv
from json import loads, dumps
from datetime import datetime
from pytz import timezone
from re import sub


class EditableEventSourced:
    """
    This class provides CRUD methods to make a dataset editable using the Event Sourcing pattern.

    Edits are stored in a separate dataset called the editlog. The source dataset is never changed. Both the source dataset and the editlog are used to compute the edited state.
    """

    def __set_ontology__(self, primary_keys, editable_column_names, linked_records):
        self.primary_keys = primary_keys
        # if no editable_column_names are provided, all columns except primary keys are editable
        if editable_column_names:
            self.editable_column_names = editable_column_names
        else:
            self.editable_column_names = [
                column["name"]
                for column in self.schema_columns
                if column["name"] not in self.primary_keys
            ]
        self.linked_records = linked_records

    def __save_custom_fields__(
        self,
        ds_name,
        original_ds=None,
        editlog_ds=None,
        primary_keys=None,
        editable_column_names=None,
        linked_records=None,
    ):
        """
        Save custom fields in a dataset's settings.

        Params:
        - ds_name: name of the dataset whose custom fields are to be saved
        - original_ds: value to set for the corresponding field (name of original dataset)
        - editlog_ds: value to set for the corresponding field (name of editlog dataset)
        - primary_keys: value to set for the corresponding field (list of primary keys)
        - editable_column_names: value to set for the corresponding field (list of editable column names-
        - linked_records: value to set for the corresponding field (list of linked records)
        """
        ds_settings = self.project.get_dataset(ds_name).get_settings()
        if original_ds:
            ds_settings.custom_fields["original_ds"] = original_ds
        if editlog_ds:
            ds_settings.custom_fields["editlog_ds"] = editlog_ds
        if primary_keys:
            ds_settings.custom_fields["primary_keys"] = primary_keys
        if editable_column_names:
            ds_settings.custom_fields["editable_column_names"] = editable_column_names
        if linked_records:
            ds_settings.custom_fields["linked_records"] = dumps(linked_records)
        ds_settings.save()

    def __load_custom_fields__(self):
        ds_settings = self.project.get_dataset(self.original_ds_name).get_settings()
        primary_keys = ds_settings.custom_fields.get("primary_keys")
        editable_column_names = ds_settings.custom_fields.get("editable_column_names")
        linked_records = loads(ds_settings.custom_fields.get("linked_records"))
        return primary_keys, editable_column_names, linked_records

    def __init_editlog__(self):
        editlog_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.editlog_ds_name
        )
        if editlog_ds_creator.already_exists():
            logging.debug("Found editlog")
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            editlog_df = self.get_editlog_df()
            if editlog_df.empty:
                # Make sure that the dataset's configuration is valid by writing an empty dataframe.
                # (The editlog dataset might already exist and have a schema, but its configuration might be invalid, for instance when the project was exported to a bundle and deployed to automation, and when using a SQL connection: the dataset exists but no table was created.)
                write_empty_editlog(self.editlog_ds)
        else:
            logging.debug("No editlog found, creating it...")
            editlog_ds_creator.with_store_into(connection=self.__connection_name__)
            editlog_ds_creator.create()
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            editlog_ds_schema = [
                # not using date type, in case the editlog is CSV
                {"name": "date", "type": "string", "meaning": "DateSource"},
                {"name": "user", "type": "string", "meaning": "Text"},
                # action can be "update", "create", or "delete"; currently it's ignored by the pivot method
                {"name": "action", "type": "string", "meaning": "Text"},
                {"name": "key", "type": "string", "meaning": "Text"},
                {"name": "column_name", "type": "string", "meaning": "Text"},
                {"name": "value", "type": "string", "meaning": "Text"},
            ]
            self.editlog_ds.write_schema(editlog_ds_schema)
            write_empty_editlog(self.editlog_ds)
            logging.debug("Done.")

    def __init_editlog_downstream__(self):
        editlog_pivoted_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.editlog_pivoted_ds_name
        )
        if editlog_pivoted_ds_creator.already_exists():
            logging.debug("Found editlog pivoted")
            unused_variable = None
        else:
            logging.debug("No editlog pivoted found, creating it...")
            editlog_pivoted_ds_creator.with_store_into(
                connection=self.__connection_name__
            )
            editlog_pivoted_ds_creator.create()
            self.editlog_pivoted_ds = Dataset(
                self.editlog_pivoted_ds_name, self.project_key
            )
            logging.debug("Done.")

        pivot_recipe_name = "compute_" + self.editlog_pivoted_ds_name
        pivot_recipe_creator = DSSRecipeCreator(
            "CustomCode_pivot-editlog", pivot_recipe_name, self.project
        )
        if recipe_already_exists(pivot_recipe_name, self.project):
            logging.debug("Found recipe to create editlog pivoted")
            pivot_recipe = self.project.get_recipe(pivot_recipe_name)
        else:
            logging.debug("No recipe to create editlog pivoted, creating it...")
            pivot_recipe = pivot_recipe_creator.create()
            pivot_settings = pivot_recipe.get_settings()
            pivot_settings.add_input("editlog", self.editlog_ds_name)
            pivot_settings.add_output("editlog_pivoted", self.editlog_pivoted_ds_name)
            pivot_settings.save()
            logging.debug("Done.")

        edited_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.edited_ds_name
        )
        if edited_ds_creator.already_exists():
            logging.debug("Found edited dataset")
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
        else:
            logging.debug("No edited dataset found, creating it...")
            edited_ds_creator.with_store_into(connection=self.__connection_name__)
            edited_ds_creator.create()
            self.edited_ds = Dataset(self.edited_ds_name, self.project_key)
            logging.debug("Done.")

        merge_recipe_name = "compute_" + self.edited_ds_name
        merge_recipe_creator = DSSRecipeCreator(
            "CustomCode_merge-edits", merge_recipe_name, self.project
        )
        if recipe_already_exists(merge_recipe_name, self.project):
            logging.debug("Found recipe to create edited dataset")
            merge_recipe = self.project.get_recipe(merge_recipe_name)
        else:
            logging.debug("No recipe to create edited dataset, creating it...")
            merge_recipe = merge_recipe_creator.create()
            merge_settings = merge_recipe.get_settings()
            merge_settings.add_input("original", self.original_ds_name)
            merge_settings.add_input("editlog_pivoted", self.editlog_pivoted_ds_name)
            merge_settings.add_output("edited", self.edited_ds_name)
            merge_settings.save()
            logging.debug("Done.")

    def __init__(
        self,
        original_ds_name,
        primary_keys=None,
        editable_column_names=None,
        linked_records=None,
        editschema_manual=None,
        project_key=None,
        editschema=None,
        authorized_users=None,
    ):
        """
        Initializes the EditableDataset object.

        :param original_ds_name: the name of the original dataset

        :param primary_keys (optional): the list of primary keys of the original dataset.
        - When provided, it will be stored in the original dataset's custom fields, along with editable_column_names and linked_records.
        - If not provided, the primary keys will be retrieved from the original dataset's custom fields.

        :param editable_column_names (optional): the list of editable columns of the original dataset. If not provided, the editable columns will be read from the original dataset's custom fields; if none are found, all columns except primary keys will be made editable.

        :param linked_records (optional): the list of linked records of the original dataset. If not provided, the linked records will be read from the original dataset's custom fields. @TODO: implement this.

        :param editschema_manual: a list of dictionaries providing further information on the editing behaviour of columns.

        :param project_key (optional): the key of the project where the original dataset is located. If not provided, the current project will be used.

        :param editschema (deprecated): a list of dictionaries specifying the role and editing behavior (if any) of columns in the original dataset. This parameter is deprecated and may be removed in a future version. Please use primary_keys, editable_column_names, and linked_records instead.
        """

        client = api_client()
        if project_key is None:
            self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        else:
            self.project_key = project_key
        self.project = client.get_project(self.project_key)
        self.original_ds_name = original_ds_name
        self.original_ds = Dataset(self.original_ds_name, self.project_key)
        self.schema_columns = self.original_ds.get_config().get("schema").get("columns")
        self.__connection_name__ = (
            self.original_ds.get_config().get("params").get("connection")
        )
        if self.__connection_name__ is None:
            self.__connection_name__ = "filesystem_managed"

        self.editlog_ds_name = self.original_ds_name + "_editlog"
        self.editlog_pivoted_ds_name = self.editlog_ds_name + "_pivoted"
        self.edited_ds_name = self.original_ds_name + "_edited"

        if primary_keys:
            self.__set_ontology__(primary_keys, editable_column_names, linked_records)
            self.__save_custom_fields__(
                ds_name=self.original_ds_name,
                original_ds=self.original_ds_name,
                editlog_ds=self.editlog_ds_name,
                primary_keys=self.primary_keys,
                editable_column_names=self.editable_column_names,
                linked_records=self.linked_records,
            )
            self.__init_editlog__()
            self.__save_custom_fields__(
                ds_name=self.editlog_ds_name,
                original_ds=self.original_ds_name,
                primary_keys=self.primary_keys,
                editable_column_names=self.editable_column_names,
            )
            self.__init_editlog_downstream__()
        else:
            # if no primary keys are provided, read them + editable columns names + linked records from the original dataset's custom fields
            (
                primary_keys,
                editable_column_names,
                linked_records,
            ) = self.__load_custom_fields__()
            self.__set_ontology__(primary_keys, editable_column_names, linked_records)
            self.__init_editlog__()
            self.__init_editlog_downstream__()

        if self.linked_records:
            # For each linked record, add linked dataset/dataframe as attribute
            if len(self.linked_records) > 0:
                self.linked_records_df = DataFrame(data=self.linked_records).set_index(
                    "name"
                )
                for linked_record in self.linked_records:
                    linked_ds_name = linked_record["ds_name"]
                    linked_ds = Dataset(linked_ds_name, self.project_key)
                    # Get the connection type of the linked dataset
                    connection_name = (
                        linked_ds.get_config().get("params").get("connection")
                    )
                    if connection_name:
                        connection_type = (
                            client.get_connection(connection_name).get_info().get_type()
                        )
                    else:
                        connection_type = ""
                    # Get the number of records in the linked dataset
                    count_records = None
                    try:
                        metrics = self.project.get_dataset(
                            linked_ds_name
                        ).compute_metrics(metric_ids=["records:COUNT_RECORDS"])[
                            "result"
                        ][
                            "computed"
                        ]
                        for m in metrics:
                            if m["metric"]["metricType"] == "COUNT_RECORDS":
                                count_records = int(m["value"])
                    except:
                        pass

                    # If the linked dataset is on an SQL connection and if it has more than 1000 records, load it as a DatasetSQL object
                    if "SQL" in connection_type or "snowflake" in connection_type:
                        if count_records is not None and count_records <= 1000:
                            logging.debug(
                                f"""Loading linked dataset "{linked_ds_name}" in memory since it has less than 1000 records"""
                            )
                            linked_record["df"] = linked_ds.get_dataframe()
                        else:
                            logging.debug(
                                f"""Loading linked dataset "{linked_ds_name}" as a DatasetSQL object since it has more than 1000 records or an unknown number of records"""
                            )
                            linked_record["ds"] = DatasetSQL(
                                linked_ds_name, self.project_key
                            )
                    else:
                        logging.debug(
                            f"""Loading linked dataset "{linked_ds_name}" in memory since it isn't on an SQL connection"""
                        )
                        if count_records is None:
                            logging.warning(
                                f"Unknown number of records for linked dataset {linked_ds_name}"
                            )
                        elif count_records > 1000:
                            logging.warning(
                                f"Linked dataset {linked_ds_name} has {count_records} records — capping at 1,000 rows to avoid memory issues"
                            )
                        # get the first 1000 rows of the dataset
                        linked_record["df"] = linked_ds.get_dataframe(
                            sampling="head", limit=1000
                        )

        self.editschema_manual = editschema_manual

        if editschema:
            self.primary_keys = get_primary_keys(editschema)
            self.editable_column_names = get_editable_column_names(editschema)
            self.editschema_manual = editschema
        if self.editschema_manual:
            self.editschema_manual_df = DataFrame(
                data=self.editschema_manual
            ).set_index("name")
        else:
            self.editschema_manual_df = DataFrame(
                data={}
            )  # this will be an empty dataframe

        self.authorized_users = authorized_users

        self.display_column_names = get_display_column_names(
            self.schema_columns, self.primary_keys, self.editable_column_names
        )

    # Read methods

    def get_original_df(self):
        """Get original data without edits"""
        return get_original_df(self.original_ds)

    def get_editlog_df(self):
        """Get log of edits"""
        return get_editlog_df(self.editlog_ds)

    def empty_editlog(self):
        """Empty the edit log: remove all rows of the dataset while keeping its schema"""
        self.editlog_ds.spec_item["appendMode"] = False
        write_empty_editlog(self.editlog_ds)

    def get_edited_df(self):
        """Get original data with edited values"""
        return merge_edits_from_log_pivoted_df(
            self.original_ds, self.get_edited_cells_df()
        )

    def get_edited_df_indexed(self):
        """Get original data with edited values, indexed by primary keys"""
        return self.get_edited_df().set_index(self.primary_keys)

    def get_edited_cells_df(self) -> DataFrame:
        """Get only rows and columns that were edited"""
        return pivot_editlog(
            self.editlog_ds, self.primary_keys, self.editable_column_names
        )

    def get_edited_cells_df_indexed(self):
        """Get only rows and columns that were edited, indexed by primary keys"""
        return self.get_edited_cells_df().set_index(self.primary_keys)

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

    # Write methods

    def __log_edit__(self, key, column, value, action="update"):
        """
        Persist an edit made via a web interface, by logging it in the edit log

        Params:
        - key: dictionary containing values for all primary keys defined in the initial data editing setup, which identifies the row that was edited. Example:
            ```python
            {
                "key1": "cat",
                "key2": "2022-12-21",
            }
            ```
        - column: name of the column that was edited
        - value: new value for the cell identified by the key and column
        - action: type of edit, can be "update", "create" or "delete"
        """

        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.schema_columns:
            if col["name"] == column:
                if type(value) == str and col.get("type") == "boolean":
                    if value == "":
                        value = None
                    else:
                        value = str(loads(value.lower()))
                break

        # store value as a string, unless it's None
        if value != None:
            value_string = str(value)
        else:
            value_string = value

        user_identifier = get_user_identifier()
        if self.authorized_users and not user_identifier in self.authorized_users:
            info = "Unauthorized"
        else:
            if column in self.editable_column_names or action == "delete":
                # add to the editlog
                self.editlog_ds.spec_item["appendMode"] = True
                self.editlog_ds.write_dataframe(
                    DataFrame(
                        data={
                            "action": [action],
                            "key": [str(key)],
                            "column_name": [column],
                            "value": [value_string],
                            "date": [datetime.now(timezone("UTC")).isoformat()],
                            "user": [user_identifier],
                        }
                    )
                )
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
            self.__log_edit__(
                key=key, column=col, value=column_values.get(col), action="create"
            )
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
