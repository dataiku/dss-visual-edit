import dataiku
from dataiku.customrecipe import *
from commons import replay_edits

primary_key = get_recipe_config()['primary_key']
editable_column_names = get_recipe_config()['editable_column_names']

input_names = get_input_names_for_role('input')
input_datasets = [dataiku.Dataset(name) for name in input_names]
input_ds = input_datasets[0]

editlog_names = get_input_names_for_role('editlog')
editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]

edited_names = get_output_names_for_role('edited')
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]

# Read input data
input_df = input_ds.get_dataframe()
editlog_df = editlog_ds.get_dataframe()

# Write output schema
edited_ds.write_schema(input_ds.read_schema()) # otherwise column type for columns of missing values might change

# Write output data
edited_df = replay_edits(input_df, editlog_df, primary_key, editable_column_names)
edited_ds.write_dataframe(edited_df)
