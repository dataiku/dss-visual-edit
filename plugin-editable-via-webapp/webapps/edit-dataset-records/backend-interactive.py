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

# Run Dash cells? (see backend.py starting at Dash layout definition)