# This file is the code for the plugin Python step empty-editlog

import os, json
from dataiku.customstep import get_step_config
from dataiku import Dataset
from pandas import DataFrame
from commons import write_empty_editlog

editlog_ds_name = get_step_config().get("editlog_ds_name")
write_empty_editlog(Dataset(editlog_ds_name))
