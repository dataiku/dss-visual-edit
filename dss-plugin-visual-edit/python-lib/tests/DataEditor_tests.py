# %%
import sys

sys.path.append("../../python-lib")

from __future__ import annotations
from os import getenv, environ
import dataiku
from DataEditor import DataEditor

environ["DKU_CURRENT_PROJECT_KEY"] = "EX_ENTITY_RESOLUTION"
environ["ORIGINAL_DATASET"] = "match_suggestions_prepared"

original_ds_name: str | None = environ.get("ORIGINAL_DATASET")

# %%
de = DataEditor(
    original_ds_name=original_ds_name,
    primary_keys=["ID"],
    editable_column_names=["Matched Entity"],
    notes_column_required=True,
    notes_column_display_name="Notes",
    validation_column_required=True,
    validation_column_display_name="Validated",
)
de.get_edited_df().to_dict("records")

# %%
from tabulator_utils import get_columns_tabulator

columns = get_columns_tabulator(
    de, show_header_filter=True, freeze_editable_columns=False
)
columns

# %%
