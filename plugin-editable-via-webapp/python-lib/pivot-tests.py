from os import getenv
from dataiku import Dataset
original_ds_name = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
pivoted_ds = Dataset(original_ds_name + "_editlog_pivoted")
editlog_pivoted_df = pivoted_ds.get_dataframe()

from commons import *
edited_df = merge_edits_from_log_pivoted_df(original_ds, editlog_pivoted_df)
print(edited_df)