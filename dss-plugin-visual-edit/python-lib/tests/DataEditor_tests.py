# %%
from os import getenv, environ

environ["ORIGINAL_DATASET"] = "datamodel_customers"
environ["DKU_CURRENT_PROJECT_KEY"] = "CRM_PELLETS"

# %%
from dataiku import Dataset
from pandas import DataFrame

original_ds_name = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
original_schema = original_ds.read_schema()
original_schema_df = DataFrame(original_schema).set_index("name")

# %%
from DataEditor import DataEditor

de = DataEditor(
    original_ds_name=original_ds_name,
    primary_keys=["name"],
    editable_column_names=["address", "machine_type", "household", "dob", "label"],
)

# %%
user = "API"
# from commons import get_user_details
# user = get_user_details() # use this when in the context of a request sent by a client/browser via http

# %%
ees.get_edited_df()

# %%
ees.create_row(
    primary_keys={"name": "New name"}, column_values={"address": "New address"}
)

# %%
ees.update_row(primary_keys={"name": "toto"}, column="label", value="hey2")
# %%
ees.get_edited_cells_df()


# %%
ees.delete_row(primary_keys={"name": "New name"})
# %%
