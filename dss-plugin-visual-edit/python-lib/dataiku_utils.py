from json import dumps
from dataiku import Dataset, api_client
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
    # CSV reader will cast all the cells in the type specified in the schema.
    # However, in the stream, the first row contains the name of the colums which should not be casted obviously.
    # We therefore skip the first row and reconstruct it according to the schema.
    csv_reader = DataikuStreamedHttpUTF8CSVReader(schema_columns, csv_stream)
    rows_iter = csv_reader.iter_rows()
    # skip first row
    next(rows_iter)

    rows = [[c.get("name") for c in schema_columns]]
    for row in rows_iter:
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


def is_sql_dataset(ds: Dataset) -> bool:
    # locationInfoType may not exist, for example for editable dataset.
    return ds.get_location_info().get("locationInfoType", "") == "SQL"

def is_bigquery_dataset(ds: Dataset) -> bool:
    location_info = ds.get_location_info()
    databaseType = location_info.get("info", "").get("databaseType", "")
    return databaseType.lower() == "bigquery"