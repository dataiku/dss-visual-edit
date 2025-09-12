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


def get_linked_dataframe_filtered(linked_record, project_key, filter_term, n_results):
    """
    Get the first rows of a linked dataset filtered by a column and a term

    Params:
    - linked_record
    - project_key
    - filter_term: term to filter on
    - n_results: number of results to return

    Returns: DataFrame with default index
    """

    linked_ds_label = linked_record.ds_label
    if linked_record.ds:
        # The linked dataset is SQL-based; we use the Dataiku API to filter it (but we could also use a SQL query)
        linked_ds_name = linked_record.ds_name
        linked_df_filtered = get_dataframe_filtered(
            ds_name=linked_ds_name,
            project_key=project_key,
            filter_column=linked_ds_label,
            filter_term=filter_term,
            n_results=n_results,
        )
    else:
        # The linked dataframe is already available in memory (and capped to 1000 rows); it can be filtered by Pandas
        # This dataframe is indexed by the linked dataset's key column: we reset the index to stay consistent with the rest of this method
        if linked_record.df is None:
            return "Something went wrong. Try restarting the backend.", 500
        linked_df = linked_record.df.reset_index()
        if filter_term == "":
            linked_df_filtered = linked_df.head(n_results)
        else:
            # Filter linked_df for rows whose label starts with the search term
            linked_df_filtered = linked_df[
                linked_df[linked_ds_label].str.lower().str.startswith(filter_term)
            ].head(n_results)
    return linked_df_filtered


def get_linked_label(linked_record, key):
    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label
    # Return label only if a label column is defined (and different from the key column)
    if key != "" and linked_ds_label and linked_ds_label != linked_ds_key:
        if linked_record.ds:
            try:
                label = linked_record.ds.get_cell_value_sql_query(
                    linked_ds_key, key, linked_ds_label
                )
            except Exception:
                return "Something went wrong fetching label of linked value.", 500
        else:
            linked_df = linked_record.df
            if linked_df is None:
                return "Something went wrong. Try restarting the backend.", 500
            try:
                label = linked_df.loc[key, linked_ds_label]
            except Exception:
                return label
    else:
        label = key
    return label


def is_sql_dataset(ds: Dataset) -> bool:
    # locationInfoType may not exist, for example for editable dataset.
    return ds.get_location_info().get("locationInfoType", "") == "SQL"


def is_bigquery_dataset(ds: Dataset) -> bool:
    location_info = ds.get_location_info()
    databaseType = location_info.get("info", "").get("databaseType", "")
    return databaseType.lower() == "bigquery"
