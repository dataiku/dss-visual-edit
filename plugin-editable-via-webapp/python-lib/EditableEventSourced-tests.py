#%%
from os import getenv
from dataiku import Dataset
original_ds_name = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
original_schema = original_ds.read_schema()
original_schema_df = DataFrame(original_schema).set_index("name")

#%%
from commons import *
from EditableEventSourced import *
ees = EditableEventSourced(
    original_ds_name=original_ds_name,
    primary_keys=["name"],
    editable_column_names=["address", "machine_type", "household", "dob", "label"])

#%%
user = "API"
# user = get_user_details() # use this when in the context of a request sent by a client/browser via http

#%%
ees.create_row(
    primary_keys={"name": "toto"},
    column_values={"address": "home"},
    user=user)

#%%
ees.update_row(
    primary_keys={"name": "toto"},
    column="label",
    value="hey",
    user=user)
#%%
ees.get_edited_cells_df()