# -*- coding: utf-8 -*-

from os import environ, getenv
from json import load
from pandas import DataFrame

from sys import path
path.append('../../python-lib')
from commons import EditableEventSourced

import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder
# from st_aggrid.shared import GridUpdateMode # TODO: is this required?

# this is for debugging purposes - see https://awesome-streamlit.readthedocs.io/en/latest/vscode.html
# import ptvsd
# ptvsd.enable_attach(address=('localhost', 5678))
# ptvsd.wait_for_attach()

environ["EDIT_DATASET_RECORDS_SETTINGS"] = "example-settings/settings-transactions.json"
settings = load(open(getenv("EDIT_DATASET_RECORDS_SETTINGS"))) # defined in VS Code launch config
project_key = settings["project_key"]
input_dataset_name = settings["input_dataset"]
schema = settings["schema"]

@st.cache()
def get_ees(input_dataset_name, project_key, schema):
    return EditableEventSourced(input_dataset_name, project_key, schema)

ees = get_ees(input_dataset_name, project_key, schema)

"""
### Edit

Select a cell, type a new value, and press Enter to save.
"""

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
        enable_enterprise_modules=True,
        gridOptions=options.build(),
        theme="light",
        update_mode=GridUpdateMode.SELECTION_CHANGED, # TODO: change this
        allow_unsafe_jscode=True,
    )
    return grid

grid = aggrid_interactive_table(df=ees.get_editable_df())
