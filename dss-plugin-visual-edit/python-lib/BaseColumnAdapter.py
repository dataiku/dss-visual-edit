import logging
from pandas import DataFrame


class BaseColumnAdapter:
    """
    BaseColumnAdapter: Common logic for generating column definitions for data table components (Tabulator, AgGrid, etc).

    This class provides shared logic for generating column configurations, including type inference and pretty type names. Subclasses should override formatter/editor methods for component-specific behavior.

    A column's configuration must include definitions for:
    - Header menu
    - Header filters
    - Title formatting (e.g., adding an icon or a mention of the column type in addition to its title)
    - Values sorting
    - Values formatting (e.g., dates)
    - Editing widget: only for editable columns; therefore, this is implemented in a separate method.
    """

    @staticmethod
    def get_column_configuration(t_type):
        """
        Returns a dictionary with formatting options for the given column type.
        This is a stub and should be overridden in subclasses for component-specific formatting.
        Args:
            t_type (str): The inferred type of the column (e.g., 'string', 'number', 'boolean').
        Returns:
            dict: Formatting options for the column.
        """
        return {}

    @classmethod
    def get_columns(cls, de, show_header_filter=True, freeze_editable_columns=False):
        """
        Generate a list of column configuration dictionaries for a data table component.
        Loops over all relevant columns and applies type inference and component-specific logic.
        Args:
            de: DataEditor instance or similar object with schema info.
            show_header_filter (bool): Whether to show header filters.
            freeze_editable_columns (bool): Whether to freeze editable columns.
        Returns:
            list: List of column configuration dictionaries.
        """
        linked_record_names = []
        if hasattr(de, "linked_records") and de.linked_records:
            try:
                linked_records_df = de.linked_records_df
                linked_record_names = linked_records_df.index.values.tolist()
            except Exception:
                logging.exception("Failed to get linked record names.")

        t_cols = []
        for col_name in (
            de.primary_keys + de.display_column_names + de.editable_column_names
        ):
            t_col = {
                "field": col_name,
                "title": col_name,
                "headerFilter": show_header_filter,
                "resizable": True,
            }

            t_type = cls.get_column_type(de, col_name)

            # Add title formatter if implemented in subclass
            if hasattr(cls, "get_title_formatter"):
                t_col["titleFormatter"] = cls.get_title_formatter(t_type)

            # Freeze primary keys, and editable columns if specified
            if col_name in de.primary_keys or (
                col_name in de.editable_column_names and freeze_editable_columns
            ):
                t_col["frozen"] = True

            # Add editor options for editable columns
            if col_name in linked_record_names and hasattr(
                cls, "get_linked_record_configuration"
            ):
                # Linked record columns are editable, by definition
                t_col.update(cls.get_linked_record_configuration(de, col_name))
            else:
                t_col.update(cls.get_column_configuration(t_type))
                if col_name in de.editable_column_names:
                    t_col.update(cls.get_column_editor_configuration(t_type))

            t_cols.append(t_col)

        return t_cols

    @staticmethod
    def get_column_type(de, col_name):
        """
        Infer the type of a column based on Dataset schema and manual overrides.
        Args:
            de: DataEditor instance or similar object with schema info.
            col_name (str): Name of the column.
        Returns:
            str: Inferred type (e.g., 'linked_record', 'string', 'boolean', 'number', 'date').
        """
        linked_record_names = []
        if hasattr(de, "linked_records") and de.linked_records:
            try:
                linked_records_df = de.linked_records_df
                linked_record_names = linked_records_df.index.values.tolist()
            except Exception:
                logging.exception("Failed to get linked record names.")
        if col_name in linked_record_names:
            t_type = "linked_record"
        else:
            t_type = "string"  # default type
            if (
                hasattr(de, "editschema_manual_df")
                and not de.editschema_manual_df.empty
                and "type" in de.editschema_manual_df.columns
                and col_name in de.editschema_manual_df.index
            ):
                editschema_manual_type = de.editschema_manual_df.loc[col_name, "type"]
            else:
                editschema_manual_type = None
            if (
                editschema_manual_type
                and editschema_manual_type == editschema_manual_type
            ):
                t_type = editschema_manual_type
            else:
                schema_df = DataFrame(data=de.schema_columns).set_index("name")
                if "meaning" in schema_df.columns.to_list():
                    schema_meaning = schema_df.loc[col_name, "meaning"]
                else:
                    schema_meaning = None
                if schema_meaning and schema_meaning == schema_meaning:
                    if schema_meaning == "Boolean":
                        t_type = "boolean"
                    if (
                        schema_meaning == "DoubleMeaning"
                        or schema_meaning == "LongMeaning"
                        or schema_meaning == "IntMeaning"
                    ):
                        t_type = "number"
                    if schema_meaning == "Date":
                        t_type = "date"
                else:
                    schema_type = schema_df.loc[col_name, "type"]
                    if schema_type == "boolean":
                        t_type = "boolean"
                    if schema_type in [
                        "tinyint",
                        "smallint",
                        "int",
                        "bigint",
                        "float",
                        "double",
                    ]:
                        t_type = "number"
                    if schema_type == "date":
                        t_type = "date"
        return t_type

    @staticmethod
    def get_pretty_type(t_type):
        """
        Return a human-readable string for a given column type.
        Args:
            t_type (str): The column type.
        Returns:
            str: Pretty type name for display.
        """
        pretty_types = {
            "number": "Number",
            "string": "Text",
            "textarea": "Text",
            "boolean": "Checkbox",
            "boolean_tick": "Checkbox",
            "date": "Date",
            "linked_record": "Dropdown",
        }
        return pretty_types.get(t_type, t_type)

    @staticmethod
    def get_column_editor_configuration(t_type):
        """
        Returns a dictionary with editor options for the given column type.
        This is a stub and should be overridden in subclasses for component-specific editors.
        Args:
            t_type (str): The inferred type of the column.
        Returns:
            dict: Editor options for the column.
        """
        return {}

    @staticmethod
    def get_linked_record_configuration(de, col_name):
        """
        Returns a dictionary with editor options for a linked record column.
        This is a stub and should be overridden in subclasses for component-specific editors.
        Args:
            de: DataEditor instance or similar object with schema info.
            col_name (str): Name of the linked record column.
        Returns:
            dict: Editor options for the linked record column.
        """
        return {}
