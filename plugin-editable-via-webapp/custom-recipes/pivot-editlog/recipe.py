#%% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import pivot_editlog, get_editlog_pivoted_ds_schema


#%% Get recipe parameters
###

editlog_names = get_input_names_for_role('editlog')
editlog_pivoted_names = get_output_names_for_role('editlog_pivoted')

editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]

editlog_pivoted_datasets = [dataiku.Dataset(name) for name in editlog_pivoted_names]
editlog_pivoted_ds = editlog_pivoted_datasets[0]


#%% Compute output data
###

original_ds_name = editlog_ds.get_config()["customFields"]["original_ds"]
original_ds = dataiku.Dataset(original_ds_name)
original_schema = original_ds.read_schema()
primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]
editlog_pivoted_df = pivot_editlog(editlog_ds, primary_keys, editable_column_names)


#%% Write output data
###

# Write schema explicitly, instead of inferring it when writing the dataframe
editlog_pivoted_ds_schema, edited_ds_schema = get_editlog_pivoted_ds_schema(original_schema, primary_keys, editable_column_names)
editlog_pivoted_ds.write_schema(editlog_pivoted_ds_schema, dropAndCreate=True)
editlog_pivoted_ds.write_dataframe(editlog_pivoted_df, infer_schema=False)
