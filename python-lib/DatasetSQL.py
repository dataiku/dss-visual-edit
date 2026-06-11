import logging

from dataiku import Dataset, SQLExecutor2, api_client, get_custom_variables
from dataiku.sql import Column, SelectQuery, toSQL

client = api_client()


class DatasetSQL:
    def __init__(self, name, project_key):
        """Initialize a DatasetSQL object

        Args:
            name (str): Name of the dataset (e.g. "companies_ext")
            project_key (str): Project key (e.g. "COMPANY_RECONCILIATION")
        """
        self.name = name
        self.project_key = project_key
        self.dataset = Dataset(name, project_key)
        self.connection_name = self.dataset.get_config()["params"]["connection"]
        self.executor = SQLExecutor2(connection=self.connection_name)
        self.table_name = self.dataset.get_config()["params"]["table"].replace("${projectKey}", project_key)
        node = get_custom_variables(project_key).get("NODE")
        if node:
            self.table_name = self.table_name.replace("${NODE}", node)

    def __get_safe_query__(self, key_column_name, key_value, column_name):
        select_query = SelectQuery()
        select_query.select_from(self.dataset)
        select_query.select([Column(column_name)])
        select_query.where(Column(key_column_name).eq(key_value))
        select_query.limit(1)

        try:
            return toSQL(select_query, self.dataset)
        except Exception:
            logging.exception("Error when generating query.")
            raise

    def get_cell_value_executor(self, key_column_name, key_value, column_name):
        """
        Get the value of a cell identified by a key value and a column name, using a SQLExecutor2 object

        Params:
        - key_column_name: name of the column containing the key
        - key_value: value of the key
        - column_name: name of the column containing the value to return

        Returns: cell value
        """
        if key_value != "":
            df = self.executor.query_to_df(self.__get_safe_query__(key_column_name, key_value, column_name))
            if df.size:
                return df[column_name].values[0]
            else:
                return "[Not found]"
        else:
            return ""

    def get_cell_value_sql_query(self, key_column_name, key_value, column_name):
        """
        Get the value of a cell identified by a key value and a column name, using the sql_query method of the Dataiku client
        """
        if key_value != "" and key_value != "null":
            streamed_query = client.sql_query(
                query=self.__get_safe_query__(key_column_name, key_value, column_name),
                connection=self.connection_name,
                project_key=self.project_key,
            )
            rows = []
            for row in streamed_query.iter_rows():
                rows.append(row)
            if len(rows) > 0:
                return rows[0][0]
            else:
                return "[Not found]"
        else:
            return ""
