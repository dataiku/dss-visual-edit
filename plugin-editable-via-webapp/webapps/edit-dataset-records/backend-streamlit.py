import streamlit as st
from EditableEventSourced import EditableEventSourced

ORIGINAL_DATASET = "matches_to_be_reviewed"
PRIMARY_KEYS = ["ID"]
EDITABLE_COLUMN_NAMES = ["Matched Entity", "Reviewed", "Comments"]

ees = EditableEventSourced(
    original_ds_name=ORIGINAL_DATASET,
    primary_keys=PRIMARY_KEYS,
    editable_column_names=EDITABLE_COLUMN_NAMES,
)
df = ees.get_edited_df()
edited_df = st.data_editor(df, key="data_editor")
st.write("Here's the session state:")
st.write(st.session_state["data_editor"])  # 👈 Access the edited data
