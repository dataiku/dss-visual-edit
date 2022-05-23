import dataiku
from dataiku.customrecipe import *
from json import loads

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

import commons


webapp_ID = get_recipe_config()['webapp_ID']
webapp_json = commons.get_webapp_json(get_recipe_config()['webapp_ID'])
schema = loads(webapp_json["config"]["schema"])
editable_column_names = commons.get_editable_column_names(schema)


editlog_names = get_input_names_for_role('editlog')
editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]

pivoted_names = get_output_names_for_role('editlog_pivoted')
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

# Read input data
editlog_df = commons.get_editlog_df(editlog_ds)

# Write output data
pivoted_df = commons.pivot_editlog(editlog_df)
pivoted_ds.write_with_schema(pivoted_df)
