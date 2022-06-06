import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role
from json import loads

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

import commons


original_names = get_input_names_for_role('original')
original_datasets = [dataiku.Dataset(name) for name in original_names]
original_ds = original_datasets[0]

pivoted_names = get_input_names_for_role('editlog_pivoted')
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

edited_names = get_output_names_for_role('edited')
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]

# Read input data
original_df = original_ds.get_dataframe()
editlog_pivoted_df = pivoted_ds.get_dataframe()

# Write output schema
edited_ds.write_schema(original_ds.read_schema()) # otherwise column type for columns of missing values might change

schema = loads(original_ds.get_config()["customFields"]["schema"])
primary_key, _ = commons.get_primary_key(schema)

# Write output data
edited_df = commons.merge_edits(original_df, editlog_pivoted_df, primary_key)
edited_ds.write_dataframe(edited_df)
