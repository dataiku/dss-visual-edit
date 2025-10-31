#%%
from DatasetSQL import DatasetSQL
from os import environ
import logging

DATASET_NAME = "companies_ext"
PROJECT_KEY = "COMPANY_RECONCILIATION"

logging.basicConfig(level=logging.DEBUG)

environ["DKU_CURRENT_PROJECT_KEY"] = PROJECT_KEY
ds = DatasetSQL(DATASET_NAME, PROJECT_KEY)

#%%
ds.get_cell_value_executor("EntityId", "1264207944", "EntityName")

# %%
ds.get_cell_value_executor("EntityId", "1007902331", "EntityName")

# %%
ds.get_cell_value_sql_query("EntityId", "1033495924", "EntityName")

# %%
ds.get_cell_value_sql_query("EntityId", "2000259050", "EntityName")
# %%
