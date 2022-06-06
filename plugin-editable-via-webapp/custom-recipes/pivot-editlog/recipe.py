import dataiku
from dataiku.customrecipe import *
from json import loads
from pandas import DataFrame

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

import commons

editlog_names = get_input_names_for_role('editlog')
editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]
original_ds_name = DataFrame(editlog_ds.get_config()["dkuProperties"]).set_index("name").loc["original_dataset", "value"]
original_ds = dataiku.Dataset(original_ds_name)
schema = loads(original_ds.get_config()["customFields"]["schema"])
editable_column_names = commons.get_editable_column_names(schema)

pivoted_names = get_output_names_for_role('editlog_pivoted')
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

# Read input data
editlog_df = commons.get_editlog_df(editlog_ds)

# Write output data
pivoted_df = commons.pivot_editlog(editlog_df, editable_column_names)
pivoted_ds.write_with_schema(pivoted_df)
