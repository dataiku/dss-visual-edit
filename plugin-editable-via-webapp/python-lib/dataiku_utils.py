from dataikuapi.utils import DataikuStreamedHttpUTF8CSVReader

def get_rows(client, ds_name, project_key, schema_columns, params):
    csv_stream = client._perform_raw(
        "GET", f"/projects/{project_key}/datasets/{ds_name}/data/",
        params=params)
    csv_reader = DataikuStreamedHttpUTF8CSVReader(
        schema_columns, csv_stream)
    rows = []
    for row in csv_reader.iter_rows():
        rows.append(row)
    return rows