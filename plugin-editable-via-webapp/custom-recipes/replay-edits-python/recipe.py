import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
from dataiku.customrecipe import *

input_names = get_input_names_for_role('input')
input_datasets = [dataiku.Dataset(name) for name in input_names]

editlog_names = get_input_names_for_role('editlog')
editlog_datasets = [dataiku.Dataset(name) for name in changes_names]

editable_names = get_output_names_for_role('editable')
editable_datasets = [dataiku.Dataset(name) for name in editable_names]

input_ds = input_datasets[0]
input_df = input_ds.get_dataframe()

editlog_ds = changes_datasets[0]
editlog_df = editlog_ds.get_dataframe()

editable_df = input_df
# TODO: apply edits - see webapp backend for logic to implement, and move it into a lib

editable_dataset = editable_datasets[0]
editable_dataset.write_with_schema(editable_df)