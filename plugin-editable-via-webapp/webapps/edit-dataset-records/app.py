# -*- coding: utf-8 -*-

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
import streamlit as st
from EditableEventSourced import EditableEventSourced
@st.cache()
def get_ees(original_ds_name, editschema, project_key):
    return EditableEventSourced(original_ds_name, editschema, project_key)
ees = get_ees(original_ds_name, editschema, project_key)
user = "streamlit"

"""
### Edit
Select a cell, type a new value, and press Enter to save.
"""

# st.dataframe(ees.get_edited_df_indexed())

#%%
from pandas import DataFrame
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode # TODO: is this required?
def aggrid_interactive_table(df: DataFrame):
    """Creates an st-aggrid interactive table based on a dataframe"""
    options = GridOptionsBuilder.from_dataframe(
        df, enableRowGroup=False, enableValue=True, enablePivot=False
    )
    options.configure_columns(df.columns, editable=True)
    options.configure_side_bar()
    options.configure_selection("single", use_checkbox=True)
    grid = AgGrid(
        df,
        gridOptions=options.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED, # TODO: change this
        allow_unsafe_jscode=True,
    )
    return grid

grid = aggrid_interactive_table(df=ees.get_edited_df_indexed())
