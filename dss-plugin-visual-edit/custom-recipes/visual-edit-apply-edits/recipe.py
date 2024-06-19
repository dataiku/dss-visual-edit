# %% Imports
###

import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role
from pandas import DataFrame

# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')

from commons import apply_edits_from_df, get_dataframe


# %% Get recipe parameters
###

original_names = get_input_names_for_role("original")
original_datasets = [dataiku.Dataset(name) for name in original_names]
original_ds = original_datasets[0]
original_schema = original_ds.read_schema()
original_schema_df = DataFrame(original_schema).set_index("name")

edits_names = get_input_names_for_role("edits")
edits_datasets = [dataiku.Dataset(name) for name in edits_names]
edits_ds = edits_datasets[0]

edited_names = get_output_names_for_role("edited")
edited_datasets = [dataiku.Dataset(name) for name in edited_names]
edited_ds = edited_datasets[0]


# %% Read input data
###

edits_df = get_dataframe(
    edits_ds
)  # this dataframe was written by the replay-edits recipe which inferred the schema upon writing: let's use this schema when reading this dataset


# %% Compute output data
###

edited_df = apply_edits_from_df(original_ds, edits_df)


# %% Write output data
###

edited_ds.write_with_schema(
    edited_df, drop_and_create=True
)  # the dataframe's types were set explicitly, so let's use them to write this dataset's schema
edited_schema = edited_ds.read_schema()
# for each item of edited_schema, make sure its type is the same as the one given by original_schema
for item in edited_schema:
    item["type"] = original_schema_df.loc[item["name"]]["type"]
edited_ds.write_schema(edited_schema)
