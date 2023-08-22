from os import getenv
from dataiku import Dataset
from commons import *

original_ds_name = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
editlog_ds = Dataset(original_ds_name + "_editlog")
primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
editlog_pivoted_df = pivot_editlog(editlog_ds, primary_keys, editable_column_names)
edited_df = merge_edits_from_log_pivoted_df(original_ds, editlog_pivoted_df)
print(edited_df)
