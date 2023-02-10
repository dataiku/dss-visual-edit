#%% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import merge_edits_from_overrides_df


#%% Get recipe parameters
###

original_names = get_input_names_for_role('original')
original_datasets = [dataiku.Dataset(name) for name in original_names]
original_ds = original_datasets[0]

overrides_names = get_input_names_for_role('overrides')
overrides_datasets = [dataiku.Dataset(name) for name in overrides_names]
overrides_ds = overrides_datasets[0]

edited_names = get_output_names_for_role('edited')
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]


#%% Read input data
###

overrides_df = overrides_ds.get_dataframe() # this dataframe was written by the replay recipe which inferred the schema upon writing, so we stay with the default infer_with_pandas=True


#%% Compute output data
###

edited_df = merge_edits_from_overrides_df(original_ds, overrides_df)


#%% Write output data
###

# Write schema explicitly, instead of inferring it when writing the dataframe:
# This schema should always be the same as that of the original dataset
edited_ds.write_schema(original_ds.read_schema(), dropAndCreate=True)
edited_ds.write_dataframe(edited_df, infer_schema=False)
