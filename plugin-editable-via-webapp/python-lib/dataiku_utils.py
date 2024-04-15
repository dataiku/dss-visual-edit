from json import dumps
from dataiku import api_client
from dataikuapi.utils import DataikuStreamedHttpUTF8CSVReader
from pandas import DataFrame

client = api_client()


def recipe_already_exists(recipe_name, project):
    """Determine if a recipe already exists in a project

    Args:
        recipe_name (str): name of the recipe
        project (project): Dataiku project (e.g. client.get_project("MY_PROJECT"))

    Returns:
        bool: True if the recipe exists, False otherwise
    """
    try:
        project.get_recipe(recipe_name).get_status()
        return True
    except Exception:
        return False


def get_rows(dataset_name, project_key, params):
    """Get the rows of a dataset

    Args:
        dataset_name (str): name of the Dataiku dataset
        project_key (str): project key
        params (_type_): _description_

    Returns:
        _type_: _description_
    """
    project = client.get_project(project_key)
    schema_columns = project.get_dataset(dataset_name).get_schema()["columns"]
    csv_stream = client._perform_raw(
        "GET", f"/projects/{project_key}/datasets/{dataset_name}/data/", params=params
    )
    csv_reader = DataikuStreamedHttpUTF8CSVReader(schema_columns, csv_stream)
    rows = []
    for row in csv_reader.iter_rows():
        rows.append(row)
    return rows


def get_dataframe_filtered(ds_name, project_key, filter_column, filter_term, n_results):
    """
    Get the first rows of a dataset filtered by a column and a term

    Params:
    - ds_name: name of the dataset
    - project_key: project key
    - filter_column: name of the column to filter on
    - filter_term: term to filter on
    - n_results: number of results to return

    Returns: DataFrame with default index
    """

    params = {
        "format": "tsv-excel-header",
        "filter": f"""startsWith(toLowercase(strval("{filter_column}")), "{filter_term}")""",
        "sampling": dumps(
            {"samplingMethod": "HEAD_SEQUENTIAL", "maxRecords": n_results}
        ),
    }
    rows = get_rows(ds_name, project_key, params)
    return DataFrame(columns=rows[0], data=rows[1:]) if len(rows) > 0 else DataFrame()


def get_connection_info(ds):
    connection_name = ds.get_config().get("params").get("connection")
    if connection_name:
        connection_type = client.get_connection(connection_name).get_info().get_type()
    else:
        connection_type = ""
    return connection_name, connection_type
