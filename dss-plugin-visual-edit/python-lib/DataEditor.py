from __future__ import annotations
import logging
from dataiku import Dataset, api_client
from dataikuapi.dss.dataset import DSSManagedDatasetCreationHelper
from dataikuapi.dss.recipe import DSSRecipeCreator
from dataiku_utils import is_sql_dataset, recipe_already_exists
from pandas import DataFrame
from commons import (
    try_get_user_identifier,
    get_original_df,
    get_dataframe,
    write_empty_editlog,
    get_display_column_names,
    apply_edits_from_df,
    replay_edits,
    get_key_values_from_dict,
)
from webapp.db.editlogs import EditLog, EditLogAppenderFactory
from webapp_utils import find_webapp_id, get_webapp_json
from editschema_utils import get_primary_keys, get_editable_column_names
from DatasetSQL import DatasetSQL
from os import getenv
from json import loads
from datetime import datetime
from pytz import timezone
from re import sub
from typing import List
from webapp.config.models import LinkedRecord, EditSchema


class EditSuccess:
    pass


class EditFailure:
    def __init__(self, message: str) -> None:
        self.message = message


class EditUnauthorized:
    pass


class DataEditor:
    """
    This class provides CRUD methods to edit data from a Dataiku Dataset using the Event Sourcing pattern: edits are stored in a separate Dataset called the editlog. The original Dataset is never changed. Both Datasets are used to compute the edited state of the data.
    """

    def __save_custom_fields__(self, dataset_name):
        settings = self.project.get_dataset(dataset_name).get_settings()
        settings.custom_fields["original_ds"] = self.original_ds_name
        settings.custom_fields["editlog_ds"] = self.editlog_ds_name
        settings.custom_fields["primary_keys"] = self.primary_keys
        settings.custom_fields["editable_column_names"] = self.editable_column_names
        if self.validation_column_name:
            settings.custom_fields["validation_column_name"] = (
                self.validation_column_name
            )
        if self.notes_column_name:
            settings.custom_fields["notes_column_name"] = self.notes_column_name
        if self.webapp_url:
            settings.custom_fields["webapp_url"] = self.webapp_url
        settings.save()

    def __init_webapp_url__(self):
        try:
            webapp_id = find_webapp_id(self.original_ds_name)
            webapp_name = sub(
                r"[\W_]+", "-", get_webapp_json(webapp_id).get("name").lower()
            )
            self.webapp_url = (
                f"/projects/{self.project_key}/webapps/{webapp_id}_{webapp_name}/edit"
            )
            self.webapp_url_public = f"/public-webapps/{self.project_key}/{webapp_id}/"
        except Exception:
            logging.exception("Failed to retrieve webapp url.")
            self.webapp_url = None
            self.webapp_url_public = "/"

    def __setup_editlog__(self):
        editlog_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.editlog_ds_name
        )
        if editlog_ds_creator.already_exists():
            logging.debug("Found editlog")
            self.editlog_ds = Dataset(self.editlog_ds_name, self.project_key)
            editlog_df = get_dataframe(self.editlog_ds)
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
                # action can be "validate", "comment", "update", "create", or "delete"
                {"name": "action", "type": "string", "meaning": "Text"},
                {"name": "key", "type": "string", "meaning": "Text"},
                {"name": "column_name", "type": "string", "meaning": "Text"},
                {"name": "value", "type": "string", "meaning": "Text"},
            ]
            self.editlog_ds.write_schema(editlog_ds_schema)
            write_empty_editlog(self.editlog_ds)
            logging.debug("Done.")

        self.editlog_columns = self.editlog_ds.get_config().get("schema").get("columns")

    def __setup_editlog_downstream__(self):
        edits_ds_creator = DSSManagedDatasetCreationHelper(
            self.project, self.edits_ds_name
        )
        if edits_ds_creator.already_exists():
            logging.debug("Found edits dataset")
        else:
            logging.debug("No edits dataset found, creating it...")
            edits_ds_creator.with_store_into(connection=self.__connection_name__)
            edits_ds_creator.create()
            self.edits_ds = Dataset(self.edits_ds_name, self.project_key)
            logging.debug("Done.")

        replay_recipe_name = "compute_" + self.edits_ds_name
        replay_recipe_creator = DSSRecipeCreator(
            "CustomCode_visual-edit-replay-edits", replay_recipe_name, self.project
        )
        if recipe_already_exists(replay_recipe_name, self.project):
            logging.debug("Found recipe to create edits dataset")
            replay_recipe = self.project.get_recipe(replay_recipe_name)
        else:
            logging.debug("No recipe to create edits dataset, creating it...")
            replay_recipe = replay_recipe_creator.create()
            replay_settings = replay_recipe.get_settings()
            replay_settings.add_input("editlog", self.editlog_ds_name)
            replay_settings.add_output("edits", self.edits_ds_name)
            replay_settings.custom_fields["webapp_url"] = self.webapp_url
            replay_settings.save()
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

        apply_recipe_name = "compute_" + self.edited_ds_name
        apply_recipe_creator = DSSRecipeCreator(
            "CustomCode_visual-edit-apply-edits", apply_recipe_name, self.project
        )
        if recipe_already_exists(apply_recipe_name, self.project):
            logging.debug("Found recipe to create edited dataset")
            apply_recipe = self.project.get_recipe(apply_recipe_name)
        else:
            logging.debug("No recipe to create edited dataset, creating it...")
            apply_recipe = apply_recipe_creator.create()
            apply_settings = apply_recipe.get_settings()
            apply_settings.add_input("original", self.original_ds_name)
            apply_settings.add_input("edits", self.edits_ds_name)
            apply_settings.add_output("edited", self.edited_ds_name)
            apply_settings.custom_fields["webapp_url"] = self.webapp_url
            apply_settings.save()
            logging.debug("Done.")

    def __init__(
        self,
        original_ds_name: str,
        primary_keys: List[str],
        editable_column_names: List[str] | None = None,
        notes_column_name: str | None = None,
        validation_column_name: str | None = None,
        linked_records: List[LinkedRecord] | None = None,
        editschema_manual: List[EditSchema] | None = None,
        project_key: str | None = None,
        editschema=None,
        authorized_users: List[str] | None = None,
    ):
        """
        Initializes Datasets (original and editlog) and properties used for data editing.

        Args:
            original_ds_name (str): The name of the original dataset.
            primary_keys (list): A list of column names that uniquely identify a row in the dataset.
            editable_column_names (list): A list of column names that can be edited. If None, all columns are editable.
            notes_column_name (str): The name of a column for end-user to write notes about each row.
            validation_column_name (str): The name of a column for end-user to mark rows as validated.
            project_key (str): The key of the project where the dataset is located. If None, the current project is used.
            authorized_users (list): A list of user identifiers who are authorized to make edits. If None, all users are authorized.
            linked_records (list): (Optional) A list of LinkedRecord objects that represent linked datasets or dataframes.
            editschema_manual (list): (Optional) A list of EditSchema objects that define the primary keys and editable columns.
            editschema (list): (Optional) A list of EditSchema objects that define the primary keys and editable columns.

        Notes:
            - If they don't already exist, the editlog, edits and edited Datasets are created on the same Dataiku Connection as the original Dataset. The Recipes in between (replay and apply edits) are also created.
            - Edits made via CRUD methods will instantly add rows to the editlog, but the edits and the edited Datasets won't be kept in "sync": they are only updated when the Recipes are run.
        """
        self.original_ds_name = original_ds_name
        if project_key is None:
            self.project_key = getenv("DKU_CURRENT_PROJECT_KEY")
        else:
            self.project_key = project_key
        self.__init_webapp_url__()
        client = api_client()
        self.project = client.get_project(self.project_key)
        self.original_ds = Dataset(self.original_ds_name, self.project_key)
        self.schema_columns = self.original_ds.get_config().get("schema").get("columns")

        self.editlog_ds_name = self.original_ds_name + "_editlog"
        self.edits_ds_name = self.original_ds_name + "_edits"
        self.edited_ds_name = self.original_ds_name + "_edited"

        self.__connection_name__ = (
            self.original_ds.get_config().get("params").get("connection")
        )
        if self.__connection_name__ is None:
            self.__connection_name__ = "filesystem_managed"

        self.primary_keys = primary_keys
        if editable_column_names:
            self.editable_column_names = editable_column_names
        if notes_column_name:
            self.notes_column_name = notes_column_name
        if validation_column_name:
            self.validation_column_name = validation_column_name

        # For each linked record, add linked dataset/dataframe as attribute
        self.linked_records = linked_records if linked_records is not None else []
        if self.linked_records:
            self.linked_records_df = DataFrame(
                data=[lr.info.__dict__ for lr in self.linked_records]
            ).set_index("name")
            for linked_record in self.linked_records:
                linked_ds_name = linked_record.ds_name
                linked_ds = Dataset(linked_ds_name, self.project_key)
                # Get the number of records in the linked dataset
                count_records = None
                try:
                    metrics = self.project.get_dataset(linked_ds_name).compute_metrics(
                        metric_ids=["records:COUNT_RECORDS"]
                    )["result"]["computed"]
                    for m in metrics:
                        if m["metric"]["metricType"] == "COUNT_RECORDS":
                            count_records = int(m["value"])
                except Exception:
                    pass

                # If the linked dataset is on an SQL connection and if it has more than 1000 records, load it as a DatasetSQL object
                if is_sql_dataset(linked_ds):
                    if count_records is not None and count_records <= 1000:
                        logging.debug(
                            f"""Loading linked dataset "{linked_ds_name}" in memory since it has less than 1000 records"""
                        )
                        linked_record.df = linked_ds.get_dataframe()
                    else:
                        logging.debug(
                            f"""Loading linked dataset "{linked_ds_name}" as a DatasetSQL object since it has more than 1000 records or an unknown number of records"""
                        )
                        linked_record.ds = DatasetSQL(linked_ds_name, self.project_key)
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
                    linked_record.df = linked_ds.get_dataframe(
                        sampling="head", limit=1000
                    )

        self.editschema_manual = editschema_manual

        if editschema:
            self.primary_keys = get_primary_keys(editschema)
            self.editable_column_names = get_editable_column_names(editschema)
            self.editschema_manual = editschema
        if self.editschema_manual:
            self.editschema_manual_df = DataFrame(
                data=[s.__dict__ for s in self.editschema_manual]
            ).set_index("name")
        else:
            self.editschema_manual_df = DataFrame(
                data={}
            )  # this will be an empty dataframe

        self.authorized_users = authorized_users

        self.display_column_names = get_display_column_names(
            self.schema_columns, self.primary_keys, self.editable_column_names
        )

        # make sure that original dataset and editlog have up-to-date custom fields
        self.__save_custom_fields__(self.original_ds_name)
        self.__setup_editlog__()
        self.__save_custom_fields__(self.editlog_ds_name)
        self.__setup_editlog_downstream__()

        self.editlog_appender = EditLogAppenderFactory().create(self.editlog_ds)

    def get_original_df(self):
        """
        Returns the original dataframe without any edits.

        Returns:
            pandas.DataFrame: The original data.
        """
        return get_original_df(self.original_ds)

    def get_editlog_df(self) -> DataFrame:
        """
        Returns the contents of the editlog.

        Returns:
            pandas.DataFrame: A DataFrame containing the editlog.
        """
        return get_dataframe(self.editlog_ds)

    def empty_editlog(self):
        """
        Writes an empty dataframe to the editlog dataset.
        """
        self.editlog_ds.spec_item["appendMode"] = False
        write_empty_editlog(self.editlog_ds)

    def get_edited_df_indexed(self) -> DataFrame:
        """
        Returns the edited dataframe, indexed by the primary keys.

        Returns:
            pandas.DataFrame: A DataFrame with all rows and columns from the original data, edits applied, and primary keys as index.
        """
        return self.get_edited_df().set_index(self.primary_keys)

    def get_edited_df(self) -> DataFrame:
        """
        Returns the edited dataframe.

        Returns:
            pandas.DataFrame: A DataFrame with all rows and columns from the original data, and edits applied.
        """
        return apply_edits_from_df(self.original_ds, self.get_edited_cells_df())

    def get_edited_cells_df_indexed(self) -> DataFrame:
        """
        Returns a pandas DataFrame with the edited cells, indexed by the primary keys.

        Returns:
            pandas.DataFrame
                A DataFrame containing only the edited rows and editable columns, indexed by the primary keys.
        """
        return self.get_edited_cells_df().set_index(self.primary_keys)

    def get_edited_cells_df(self) -> DataFrame:
        """
        Returns a pandas DataFrame with the edited cells.

        Returns:
            pandas.DataFrame:
                A DataFrame containing only the edited rows and editable columns.
        """
        return replay_edits(
            self.editlog_ds,
            self.primary_keys,
            self.editable_column_names,
            self.validation_column_name,
            self.notes_column_name,
        )

    def get_row(self, primary_keys):
        """
        Retrieve a single row from the dataset that was created, updated or deleted.

        Args:
            primary_keys (dict): A dictionary containing values for all primary keys defined in the initial Visual Edit setup. The set of values must be unique. Example:
                {
                    "key1": "cat",
                    "key2": "2022-12-21",
                }

        Returns:
            pandas.DataFrame:
                A single-row dataframe containing the values of editable columns, indexed by the primary keys. Example:
                ```
                key1        key2        editable_column1    editable_column2
                "cat"       2022-12-21  "hello"             42
                ```

        Notes:
            - The current implementation loads all edited rows in memory, then filters the rows that match the provided primary key values.
            - This method does not read rows that were not edited, and it does not read columns which are not editable.
                - If some rows of the dataset were created, then by definition all columns are editable (including primary keys).
                - If no row was created, editable columns are those defined in the initial Visual Edit setup.
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        return self.get_edited_cells_df_indexed().loc[key]

    def __append_to_editlog__(
        self, key, column, value, action="update"
    ) -> EditSuccess | EditFailure | EditUnauthorized:
        """
        Append an edit action to the editlog.

        Actions can be "validate", "comment", "update", "create", or "delete".
        - When the action is "validate" or "update" or "create", the column is one of the editable columns.
        - When the action is "comment", the column is the notes column.
        - When the action is "delete", the column and value are ignored.

        Args:
            key (tuple): A tuple containing primary key(s) value(s) that identify the row on which the action is performed.
            column (str): The name of a column to create/validate/update. This would be None when the action is "delete".
            value (str): The value to set for the cell identified by key and column.
            action (str): The type of action to log.

        Returns:
            EditSuccess | EditFailure | EditUnauthorized: An object indicating the success or failure to insert an editlog.
        """

        # if the type of column_name is a boolean, make sure we read it correctly
        for col in self.schema_columns:
            if col["name"] == column:
                if isinstance(value, str) and col.get("type") == "boolean":
                    if value == "":
                        value = None
                    else:
                        value = str(loads(value.lower()))
                break

        # turn value into a string, unless it's None
        if value is not None:
            value_string = str(value)
        else:
            value_string = value

        user_identifier = try_get_user_identifier()
        if self.authorized_users and (
            user_identifier is None or user_identifier not in self.authorized_users
        ):
            logging.debug(
                f"""Logging {action} action unauthorized ('{user_identifier}'): column {column} set to value {value} where {self.primary_keys} is {key}."""
            )
            return EditUnauthorized()
        else:
            if (
                column in self.editable_column_names
                or column == self.notes_column_name
                or action == "delete"
            ):
                # make sure that edits to the notes column are stored with the "comment" action
                if column == self.notes_column_name:
                    action = "comment"
                # add to the editlog
                try:
                    self.editlog_appender.append(
                        EditLog(
                            str(key),
                            column,
                            value_string,
                            datetime.now(timezone("UTC")).isoformat(),
                            "unknown" if user_identifier is None else user_identifier,
                            action,
                        )
                    )
                    logging.debug(
                        f"""Logging {action} action success: column {column} set to value {value} where {self.primary_keys} is {key}."""
                    )
                    return EditSuccess()
                except Exception:
                    logging.exception("Failed to append edit log.")
                    return EditFailure(
                        "Internal server error, failed to append edit log."
                    )
            else:
                logging.info(
                    f"""Logging {action} action failed: column {column} set to value {value} where {self.primary_keys} is {key}."""
                )
                return EditFailure(f"""{column} isn't an editable column.""")

    def create_row(self, primary_keys: dict, column_values: dict) -> str:
        """
        Creates a new row.

        Args:
            primary_keys (dict): A dictionary containing values for all primary keys. The set of values must be unique.
                Example: {"id": "My new unique id"}
            column_values (dict): A dictionary containing values for all other columns.
                Example: {"col1": "hey", "col2": 42, "col3": True}

        Returns:
            str: A message indicating that the row was created.

        Notes:
            - No data validation: this method does not check that the values are allowed for the specified columns.
            - Attribution of the 'create' action in the editlog: the user identifier is only logged when this method is called in the context of a webapp served by Dataiku (which allows retrieving the identifier from the HTTP request headers sent by the user's web browser).
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        for col in column_values.keys():
            self.__append_to_editlog__(
                key=key, column=col, value=column_values.get(col), action="create"
            )
        return "Row successfully created"

    def comment_row(
        self, primary_keys: dict, notes: str
    ) -> EditSuccess | EditFailure | EditUnauthorized:
        """
        Comments on a row.

        Args:
            primary_keys (dict): A dictionary containing primary key(s) value(s) that identify the row to comment on.
            notes (str): The comment to write in the notes column.

        Notes:
            Attribution of the 'comment' action in the editlog: the user identifier is only logged when this method is called in the context of a webapp served by Dataiku (which allows retrieving the identifier from the HTTP request headers sent by the user's web browser).
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        return self.__append_to_editlog__(
            key, self.notes_column_name, notes, action="comment"
        )

    def validate_row(
        self, row_dict: dict
    ) -> List[EditSuccess | EditFailure | EditUnauthorized]:
        """
        Validates a row, by logging values for all editable columns under a "validation" action.

        Args:
            row_dict (dict): A dictionary containing all column values for a given row to validate (including its primary key(s)).

        Returns:
            list: A list of objects indicating the success or failure of insertions of all valid column values into the editlog.

        Notes:
            Attribution of the 'validate' action in the editlog: the user identifier is only logged when this method is called in the context of a webapp served by Dataiku (which allows retrieving the identifier from the HTTP request headers sent by the user's web browser).
        """
        key = get_key_values_from_dict(row_dict, self.primary_keys)
        statuses = []
        for col in self.editable_column_names:
            statuses.append(
                self.__append_to_editlog__(key, col, row_dict[col], action="validate")
            )
        return statuses

    def update_row(
        self, primary_keys: dict, column: str, value: str
    ) -> EditSuccess | EditFailure | EditUnauthorized:
        """
        Updates a row.

        Args:
            primary_keys (dict): A dictionary containing primary key(s) value(s) that identify the row to update.
            column (str): The name of the column to update.
            value (str): The value to set for the cell identified by key and column.

        Returns:
            list: A list of objects indicating the success or failure to insert an editlog.

        Note:
            - No data validation: this method does not check that the value is allowed for the specified column.
            - Attribution of the 'update' action in the editlog: the user identifier is only logged when this method is called in the context of a webapp served by Dataiku (which allows retrieving the identifier from the HTTP request headers sent by the user's web browser).
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        return self.__append_to_editlog__(key, column, value, action="update")

    def delete_row(
        self, primary_keys: dict
    ) -> EditSuccess | EditFailure | EditUnauthorized:
        """
        Deletes a row identified by the given primary key(s).

        Args:
            primary_keys (dict): A dictionary containing the primary key(s) value(s) that identify the row to delete.

        Returns:
            str: A message indicating that the row was deleted.

        Notes:
            Attribution of the 'delete' action in the editlog: the user identifier is only logged when this method is called in the context of a webapp served by Dataiku (which allows retrieving the identifier from the HTTP request headers sent by the user's web browser).
        """
        key = get_key_values_from_dict(primary_keys, self.primary_keys)
        return self.__append_to_editlog__(key, None, None, action="delete")
