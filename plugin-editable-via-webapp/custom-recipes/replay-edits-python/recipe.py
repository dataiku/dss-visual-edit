import dataiku
from dataiku.customrecipe import *
from json import loads

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

import commons


# TODO: this recipe should be created by the webapp
webapp_json = commons.get_webapp_json(get_recipe_config()['webapp_ID'])
# input_dataset_name = webapp_json["config"]["input_dataset"] # alternative way to get input dataset
schema = loads(webapp_json["config"]["schema"])
primary_key, _ = commons.get_primary_key(schema)

input_names = get_input_names_for_role('input')
input_datasets = [dataiku.Dataset(name) for name in input_names]
input_ds = input_datasets[0]

pivoted_names = get_input_names_for_role('editlog_pivoted')
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

edited_names = get_output_names_for_role('edited')
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]

# Read input data
input_df = input_ds.get_dataframe()
editlog_pivoted_df = pivoted_ds.get_dataframe()

# Write output schema
edited_ds.write_schema(input_ds.read_schema()) # otherwise column type for columns of missing values might change

# Write output data
edited_df = commons.merge_edits(input_df, editlog_pivoted_df, primary_key)
edited_ds.write_dataframe(edited_df)
