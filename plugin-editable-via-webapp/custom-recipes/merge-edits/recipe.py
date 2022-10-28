#%% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import update_ds_with_edits


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

editlog_pivoted_df = pivoted_ds.get_dataframe() # this dataframe was written by the pivot-editlog recipe which inferred the schema upon writing, so we stay with the default infer_with_pandas=True


#%% Compute output data
###

edited_df = update_ds_with_edits(original_ds, editlog_pivoted_df)


#%% Write output data
###

# Write schema explicitly, instead of inferring it when writing the dataframe:
# This schema should always be the same as that of the original dataset
edited_ds.write_schema(original_ds.read_schema(), dropAndCreate=True)
edited_ds.write_dataframe(edited_df, infer_schema=False)
