# %% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import replay_edits


# %% Get recipe parameters
###

editlog_names = get_input_names_for_role("editlog")
edits_names = get_output_names_for_role("edits")

editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]

edits_datasets = [dataiku.Dataset(name) for name in edits_names]
edits_ds = edits_datasets[0]


# %% Compute output data
###

primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
edits_df = replay_edits(editlog_ds, primary_keys, editable_column_names)


# %% Write output data
###

edits_ds.write_dataframe(
    edits_df, infer_schema=True, dropAndCreate=True
)  # the schema is inferred upon writing and might be different from that of the original dataset: this will be reconciled by the apply-edits recipe/method
