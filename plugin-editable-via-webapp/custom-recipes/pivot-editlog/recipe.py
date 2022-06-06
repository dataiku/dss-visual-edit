import dataiku
from dataiku.customrecipe import *
from json import loads
from pandas import DataFrame

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import get_editlog_df, pivot_editlog

editlog_names = get_input_names_for_role('editlog')
editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]
editlog_df = get_editlog_df(editlog_ds)

pivoted_names = get_output_names_for_role('editlog_pivoted')
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]
editable_column_names = DataFrame(pivoted_ds.read_schema())["name"].to_list()[1:-1] # first and last columns are "key" and "date"

pivoted_df = pivot_editlog(editlog_df, editable_column_names)
pivoted_ds.write_dataframe(pivoted_df)
