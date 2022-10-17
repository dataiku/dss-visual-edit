#%% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import merge_edits


#%% Get recipe parameters
###

original_names = get_input_names_for_role('original')
original_datasets = [dataiku.Dataset(name) for name in original_names]
original_ds = original_datasets[0]

pivoted_names = get_input_names_for_role('editlog_pivoted')
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

edited_names = get_output_names_for_role('edited')
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]


#%% Read input data
###

original_df = original_ds.get_dataframe(infer_with_pandas=False)
editlog_pivoted_df = pivoted_ds.get_dataframe(infer_with_pandas=False)


#%% Compute output data
###

primary_keys = original_ds.get_config()["customFields"]["primary_keys"]
edited_df = merge_edits(original_df, editlog_pivoted_df, primary_keys)


#%% Write output data
###

# Write schema explicitly, instead of inferring it when writing the dataframe:
# This schema should always be the same as that of the original dataset
edited_ds.write_schema(original_ds.read_schema(), dropAndCreate=True)
edited_ds.write_dataframe(edited_df, infer_schema=False)
