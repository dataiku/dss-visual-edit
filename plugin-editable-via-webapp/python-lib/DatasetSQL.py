from dataiku import Dataset, SQLExecutor2, api_client, get_custom_variables

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
        self.connection_name = self.dataset.get_config()['params']['connection']
        self.executor = SQLExecutor2(connection=self.connection_name)
        self.table_name = self.dataset.get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", get_custom_variables().get("NODE"))

    def get_cell_value(self, key_column_name, key_value, column_name):
        """
        Get the value of a cell identified by a key value and a column name

        Params:
        - key_column_name: name of the column containing the key
        - key_value: value of the key
        - column_name: name of the column containing the value to return

        Returns: cell value
        """
        if key_value!="":
            select_query = f"""
                SELECT "{column_name}"
                FROM "{self.table_name}"
                WHERE "{key_column_name}"='{key_value}'"""
            streamed_query = client.sql_query(select_query, connection=self.connection_name, type='sql')
            df = self.executor.query_to_df(select_query)
            if df.size:
                return df[column_name].values[0]
            else:
                return "[Not found]"
        else:
            return ""
