from typing import List, Optional
import dataiku
from dataiku.sql import Column, toSQL, List as ListBuilder, Expression


def quote_identifier(string: str) -> str:
    sep = '"'
    return sep + string.replace(sep, sep + sep) + sep


def get_quoted_table_full_name(
    catalog: Optional[str], schema: Optional[str], table: str
) -> str:
    if not catalog:
        if not schema:
            return quote_identifier(table)
        else:
            return quote_identifier(schema) + "." + quote_identifier(table)
    else:
        if not schema:
            raise ValueError("schema cannot be empty when catalog is present")
        return (
            quote_identifier(catalog)
            + "."
            + quote_identifier(schema)
            + "."
            + quote_identifier(table)
        )


def get_table_name_from_dataset(dataset: dataiku.Dataset):
    loc = dataset.get_location_info()
    if loc.get("locationInfoType") != "SQL":
        raise ValueError("Cannot only execute query on an SQL dataset")
    table_name = loc.get("info").get("table")
    catalog_name = loc.get("info").get("catalog")
    schema_name = loc.get("info").get("schema")
    return get_quoted_table_full_name(
        catalog=catalog_name, schema=schema_name, table=table_name
    )

def get_table_name_from_bq_dataset(dataset: dataiku.Dataset):
    loc = dataset.get_location_info()
    databaseType = loc.get("info", "").get("databaseType", "")
    if databaseType.lower() != "bigquery":
        raise ValueError("Can only execute query on a BigQuery dataset")
    table_name = loc.get("info").get("table")
    schema_name = loc.get("info").get("schema")
    return schema_name + "." + table_name

class InsertQueryBuilder:
    def __init__(self, dataset: dataiku.Dataset):
        self.dataset = dataset
        self.table_name = get_table_name_from_dataset(dataset=dataset)
        self.columns: List[str] = []
        self.values: List[List[Expression]] = []
        self.TO_PARAM = "?"

    def add_column(self, column: str):
        self.columns.append(column)
        return self

    def add_columns(self, columns: List[str]):
        for column in columns:
            self.add_column(column)
        return self

    def add_value(self, value: List[Expression]):
        if len(value) != len(self.columns):
            raise ValueError("Cannot add values to insert query")
        self.values.append([val for val in value])
        return self

    def _query_start(self) -> str:
        return "INSERT INTO " + self.table_name

    def get_wrapped_cols(self) -> str:
        args = [Column(col) for col in self.columns]
        if len(args) > 0:
            builder = ListBuilder(*args)
            result = toSQL(builder, dataset=self.dataset)
            return result
        return ""

    def get_wrapped_value(self, value: List[Expression]):
        if len(value) > 0:
            builder = ListBuilder(*value)
            result = toSQL(builder, dataset=self.dataset)
            return result
        return None

    def get_wrapped_values(self) -> str:
        string_results = []
        for value in self.values:
            res = self.get_wrapped_value(value)
            if res:
                string_results.append(res)
        return ",".join(string_results)

    def parameterized_value(self) -> str:
        return " VALUES " + self.get_wrapped_values() + ";"

    def build(self) -> str:
        if not self.columns:
            raise ValueError("No columns found for the insert query builder")
        return (
            self._query_start()
            + " "
            + self.get_wrapped_cols()
            + self.parameterized_value()
        )

class BigQueryInsertQueryBuilder:
    def __init__(self, dataset: dataiku.Dataset):
        self.dataset = dataset
        self.table_name = get_table_name_from_bq_dataset(dataset=self.dataset)
        self.columns: List[str] = []
        self.values: List[List[Expression]] = []

    def add_column(self, column: str):
        self.columns.append(column)
        return self

    def add_columns(self, columns: List[str]):
        for column in columns:
            self.add_column(column)
        return self

    def add_value(self, value: List[Expression]):
        if len(value) != len(self.columns):
            raise ValueError("Number of values does not match number of columns.")
        self.values.append(value)
        return self

    def _query_start(self) -> str:
        # Wrap the fully qualified table name in backticks
        return f"INSERT INTO `{self.table_name}`"

    def get_wrapped_cols(self) -> str:
        """
        Gets each column into a properly backticked identifier list for BigQuery.
        E.g. ( `col1`, `col2`, `col3` )
        """
        col_expressions = [Column(f"{col}") for col in self.columns]
        if col_expressions:
            builder = ListBuilder(*col_expressions)
            return toSQL(builder, dataset=self.dataset)
        return ""

    def get_wrapped_value(self, value: List[Expression]) -> str:
        if value:
            builder = ListBuilder(*value)
            return toSQL(builder, dataset=self.dataset)
        return ""

    def get_wrapped_values(self) -> str:
        """
        Builds a comma-separated list of value tuples:
        (val1, val2, ...), (val1, val2, ...)
        """
        rows_sql = []
        for row in self.values:
            rows_sql.append(self.get_wrapped_value(row))
        return ",".join(rows_sql)

    def build(self) -> str:
        if not self.columns:
            raise ValueError("No columns defined for INSERT query.")
        query = (
            self._query_start()                # INSERT INTO `project.dataset.table`
            + " " + self.get_wrapped_cols()    # (`col1`,`col2`,...)
            + " VALUES " + self.get_wrapped_values()  # VALUES (val1,val2,...),(val1,val2,...)
            + ";"
        )
        return query