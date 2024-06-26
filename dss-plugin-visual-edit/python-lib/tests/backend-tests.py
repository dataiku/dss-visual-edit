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
ds = project.get_dataset(original_ds_name)
settings = ds.get_settings()
definition = ds.get_definition()
last_metrics = ds.get_last_metric_values()
