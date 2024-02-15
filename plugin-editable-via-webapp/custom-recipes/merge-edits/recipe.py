# %% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import merge_edits_from_log_pivoted_df


# %% Get recipe parameters
###

original_names = get_input_names_for_role("original")
original_datasets = [dataiku.Dataset(name) for name in original_names]
original_ds = original_datasets[0]
myschema = original_ds.read_schema()

pivoted_names = get_input_names_for_role("editlog_pivoted")
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

edited_names = get_output_names_for_role("edited")
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]


# %% Read input data
###

editlog_pivoted_df = (
    pivoted_ds.get_dataframe()
)  # this dataframe was written by the pivot-editlog recipe which inferred the schema upon writing, so we stay with the default infer_with_pandas=True


# %% Compute output data
###

edited_df = merge_edits_from_log_pivoted_df(original_ds, editlog_pivoted_df)


# %% Write output data
###

edited_ds.write_with_schema(
    edited_df, drop_and_create=True
)  # the dataframe's types were set explicitly, so let's use them to write this dataset's schema
