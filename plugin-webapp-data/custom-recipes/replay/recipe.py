#%% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import pivot_editlog, get_overrides_ds_schema


#%% Get recipe parameters
###

editlog_names = get_input_names_for_role('editlog')
overrides_names = get_output_names_for_role('overrides')

editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]

overrides_datasets = [dataiku.Dataset(name) for name in overrides_names]
overrides_ds = overrides_datasets[0]


#%% Compute output data
###

primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
overrides_df = pivot_editlog(editlog_ds, primary_keys, editable_column_names)


#%% Write output data
###

overrides_ds.write_dataframe(overrides_df, infer_schema=True, dropAndCreate=True) # the schema could be different from that of the original dataset
