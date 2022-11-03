# This file is the code for the plugin Python step empty-editlog

import os, json
from dataiku.customstep import get_step_config
from dataiku import Dataset
from pandas import DataFrame

editlog_ds_name = get_step_config().get("editlog_ds_name")
editlog_ds = Dataset(editlog_ds_name)
editlog_df = editlog_ds.get_dataframe()
empty_df = DataFrame(columns=editlog_df.columns)
editlog_ds.write_dataframe(empty_df, infer_schema=False)
