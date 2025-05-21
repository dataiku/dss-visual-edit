# %% Imports and environment setup
import sys

sys.path.append("../../python-lib")

from __future__ import annotations
from os import getenv, environ
import dataiku
import commons

environ["DKU_CURRENT_PROJECT_KEY"] = "EX_ENTITY_RESOLUTION"
environ["ORIGINAL_DATASET"] = "match_suggestions_prepared"

original_ds_name: str | None = environ.get("ORIGINAL_DATASET")
original_ds = dataiku.Dataset(original_ds_name)

# %% Replay edits
editlog_ds = dataiku.Dataset(original_ds_name + "_editlog")
primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
validation_column_required = editlog_ds.get_config()["customFields"][
    "validation_column_required"
]
notes_column_required = editlog_ds.get_config()["customFields"]["notes_column_required"]
replayed_edits_df = commons.replay_edits(
    editlog_ds,
    primary_keys,
    editable_column_names,
    validation_column_required,
    notes_column_required,
)

# %% Apply replayed edits from DataFrame
replayed_edited_df = commons.apply_edits_from_df(original_ds, replayed_edits_df)

# %% Get original DataFrame
original_df, primary_keys, display_columns, editable_columns = commons.get_original_df(
    original_ds
)

# %% Apply edits from dataset
edits_ds = dataiku.Dataset(original_ds_name + "_edits")
edits_df = commons.get_dataframe(edits_ds)
edited_df = commons.apply_edits_from_df(original_ds, edits_df)

# %%
