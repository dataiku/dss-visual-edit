from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from pandas import DataFrame
from pydantic import BaseModel

from DatasetSQL import DatasetSQL


class EditSchema(BaseModel):
    name: str
    type: str


@dataclass(frozen=True)
class LinkedRecordInfo:
    name: str
    ds_name: str
    ds_key: str
    ds_label: str
    ds_lookup_columns: list


class LinkedRecord:
    def __init__(self, info: LinkedRecordInfo) -> None:
        self.info = info
        self.name = info.name
        self.ds_name = info.ds_name
        self.ds_key = info.ds_key
        self.ds_label = info.ds_label
        self.ds_lookup_columns = info.ds_lookup_columns
        self.df: DataFrame | None = None
        self.ds: DatasetSQL | None = None


class Config(BaseModel):
    original_dataset: str = ""  # may be set by an environment variable
    primary_keys: List[str]
    editable_column_names: List[str]
    show_header_filter: bool = True
    freeze_editable_columns: bool
    group_column_names: List[str]
    linked_records_count: int = 0
    authorized_users: List[str] = []
    freeze_edits: bool = False
    # it can in fact be: null, "", [] -> empty or not, and "[]" json in a string.
    editschema: Any = []
