from __future__ import annotations
from os import getenv
from dataiku import Dataset
from commons import replay_edits_from_df

original_ds_name: str | None = getenv("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)

# editlog_ds = Dataset("" if original_ds_name is None else original_ds_name + "_editlog")
# primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
# editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
# edits_df = replay_edits(editlog_ds, primary_keys, editable_column_names)

from pandas import read_csv

primary_keys = ["ID"]
editable_column_names = ["Matched Entity"]
editlog_df = read_csv("new_editlog.csv", sep=";")

import sys

sys.path.append("../../python-lib")

from commons import replay_edits_from_df

edits_df = replay_edits_from_df(editlog_df, primary_keys, editable_column_names)
edited_df = apply_edits_from_df(original_ds, edits_df)
print(edited_df)
