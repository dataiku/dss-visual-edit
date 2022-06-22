# when using interactive execution:

#%%
# import sys
# import os
# sys.path.append('../../python-lib')
# editlog_names = ["stakeholders_tbc_filtered_editlog"]
# pivoted_names = ["stakeholders_tbc_filtered_editlog_pivoted"]
# project_key = "STAKEHOLDER_OWNERSHIP"
# os.environ["DKU_CURRENT_PROJECT_KEY"] = project_key

#%%
import dataiku
from commons import pivot_editlog

#%%
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role
editlog_names = get_input_names_for_role('editlog')
pivoted_names = get_output_names_for_role('editlog_pivoted')

#%%
editlog_datasets = [dataiku.Dataset(name) for name in editlog_names]
editlog_ds = editlog_datasets[0]

#%%
pivoted_datasets = [dataiku.Dataset(name) for name in pivoted_names]
pivoted_ds = pivoted_datasets[0]

#%%
primary_keys = editlog_ds.get_config()["customFields"]["primary_keys"]
editable_column_names = editlog_ds.get_config()["customFields"]["editable_column_names"]

#%%
pivoted_df = pivot_editlog(editlog_ds, primary_keys, editable_column_names)

#%%
pivoted_ds.write_dataframe(pivoted_df, infer_schema=True, dropAndCreate=True)
