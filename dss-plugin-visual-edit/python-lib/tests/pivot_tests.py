from __future__ import annotations
from os import getenv
from dataiku import Dataset
from commons import pivot_editlog, merge_edits_from_log_pivoted_df

original_ds_name: str | None = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
editlog_ds = Dataset("" if original_ds_name is None else original_ds_name + "_editlog")
primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
edits_df = pivot_editlog(editlog_ds, primary_keys, editable_column_names)
edited_df = merge_edits_from_log_pivoted_df(original_ds, edits_df)
print(edited_df)
