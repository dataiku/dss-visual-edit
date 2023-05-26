#%%
from DatasetSQL import DatasetSQL
ds = DatasetSQL("companies_ext", "COMPANY_RECONCILIATION")

#%%
ds.get_cell_value("EntityId", "1264207944", "EntityName")