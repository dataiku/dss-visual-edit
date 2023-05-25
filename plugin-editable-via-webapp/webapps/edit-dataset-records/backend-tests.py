#%%
from os import getenv, environ
environ["ORIGINAL_DATASET"] = "matches_uncertain"
environ["DKU_CURRENT_PROJECT_KEY"] = "COMPANY_RECONCILIATION"

#%%
from dataiku import Dataset
from pandas import DataFrame
project_key = getenv("DKU_CURRENT_PROJECT_KEY")
original_ds_name = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
original_schema = original_ds.read_schema()
original_schema_df = DataFrame(original_schema).set_index("name")

#%%
import dataiku
client = dataiku.api_client()
project = client.get_project(project_key)

#%%
ds = project.get_dataset("stakeholders_tbc_prepared")
settings = ds.get_settings()
definition = ds.get_definition()
last_metrics = ds.get_last_metric_values()

#%%
from EditableEventSourced import *
ees = EditableEventSourced(
    original_ds_name=original_ds_name,
    primary_keys=["id"],
    editable_column_names=["ext_id", "reviewed", "comments"])

#%%
# when using interactive execution:
import sys
sys.path.append('../../python-lib')

from dataiku_utils import get_rows
from json import dumps
def get_label(ds_name, key_column, key, label_column):
    schema_columns = project.get_dataset(ds_name).get_schema()["columns"]
    params = {
        "format": "tsv-excel-header",
        "filter": f"""strval("{key_column}")=="{key}")""",
        "sampling": dumps({
            "samplingMethod": "HEAD_SEQUENTIAL",
            "maxRecords": 1
        })
    }
    rows = get_rows(client, ds_name, project_key, schema_columns, params)
    return DataFrame(columns=rows[0], data=rows[1:])[label_column].values[0]

#%%
get_label(original_ds_name, "id", "0016M00002Gw2N0", "name")

# Dash cells: see backend.py starting at Dash layout definition
# %%
