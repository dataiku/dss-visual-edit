#%%
import sys
sys.path.append('../../python-lib')

from __future__ import annotations
from os import getenv, environ
from dataiku import Dataset
from commons import replay_edits, apply_edits_from_df

environ["DKU_CURRENT_PROJECT_KEY"] = "EX_ENTITY_RESOLUTION"
environ["ORIGINAL_DATASET"] = "match_suggestions_prepared"

original_ds_name: str | None = environ.get("ORIGINAL_DATASET")
original_ds = Dataset(original_ds_name)
editlog_ds = Dataset(original_ds_name + "_editlog")
primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
validation_column_required = editlog_ds.get_config()["customFields"]["validation_column_required"]
notes_column_required = editlog_ds.get_config()["customFields"]["notes_column_required"]

#%% Replay edits
edits_df = replay_edits(editlog_ds, primary_keys, editable_column_names, validation_column_required, notes_column_required)

#%% Apply edits to original dataset
edited_df = apply_edits_from_df(original_ds, edits_df)

# %%
