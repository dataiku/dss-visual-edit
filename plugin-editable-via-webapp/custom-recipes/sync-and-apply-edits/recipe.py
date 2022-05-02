import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
from dataiku.customrecipe import *

input_names = get_input_names_for_role('input')
input_datasets = [dataiku.Dataset(name) for name in input_names]

changes_names = get_input_names_for_role('editlog')
changes_datasets = [dataiku.Dataset(name) for name in changes_names]

editable_names = get_output_names_for_role('editable')
editable_datasets = [dataiku.Dataset(name) for name in editable_names]

input_dataset = input_datasets[0]
input_df = input_dataset.get_dataframe()

changes_dataset = changes_datasets[0]
changes_df = input_dataset.get_dataframe()

editable_df = input_df
# TODO: apply changes

editable_dataset = editable_datasets[0]
editable_dataset.write_with_schema(editable_df)