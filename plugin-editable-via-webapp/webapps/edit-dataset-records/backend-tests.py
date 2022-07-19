#%%
import dataiku
ds = dataiku.Dataset("stakeholders_tbc_prepared", "STAKEHOLDER_OWNERSHIP")
client = dataiku.api_client()
project = client.get_project("STAKEHOLDER_OWNERSHIP")
ds = project.get_dataset("stakeholders_tbc_prepared")
settings = ds.get_settings()
definition = ds.get_definition()
last_metrics = ds.get_last_metric_values()


#%%
import sys
sys.path.append('../../python-lib')
original_ds_name = "stakeholders_tbc_filtered"
project_key = "STAKEHOLDER_OWNERSHIP"
editschema = [
    {"name": "Stakeholder Id", "editable_type": "key"},
    {"name": "Security Id", "editable_type": "key"},
    {"name": "Report Date", "editable_type": "key"},
    {"name": "Stakeholder Name"},
    {"name": "Security Name"},
    {"name": "1) Position is Free Float? (TRUE/FALSE)", "title": "Free float?", "type": "boolean", "editable": True},
    {"name": "In case 1) = FALSE then 2) Shares in FS Correct? (TRUE/FALSE)", "title": "If not, Shares correct?", "type": "boolean", "editable": True},
    {"name": "In case 2) = FALSE then 3) Fill in shares manually", "title": "If not, Shares value?", "type": "number", "editable": True}
]

#%%
from EditableEventSourced import EditableEventSourced
ees = EditableEventSourced(original_ds_name, editschema, project_key)
user = "test"

# Dash cells: see backend.py starting at Dash layout definition