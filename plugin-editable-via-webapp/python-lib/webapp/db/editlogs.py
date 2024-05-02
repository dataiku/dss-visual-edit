from __future__ import annotations
from dataclasses import dataclass
from dataiku import Dataset, SQLExecutor2
from abc import ABC, abstractmethod
from pandas import DataFrame
from dataiku_utils import is_sql_dataset
from webapp.db.querybuilder import InsertQueryBuilder


COLUMNS = ["key", "column_name", "value", "date", "user", "action"]


@dataclass(frozen=True)
class EditLog:
    key: str
    column_name: str
    value: str | None
    date: str
    user: str
    action: str


class EditLogAppender(ABC):
    @abstractmethod
    def append(self, log: EditLog) -> None:
        pass


class GenericEditLogAppender(EditLogAppender):
    def __init__(self, dataset: Dataset) -> None:
        self.dataset = dataset

    def append(self, log: EditLog) -> None:
        self.dataset.spec_item["appendMode"] = True
        edit_data = {
            "key": [log.key],
            "column_name": [log.column_name],
            "value": [log.value],
            "date": [log.date],
            "user": [log.user],
            "action": [log.action],
        }
        self.dataset.write_dataframe(DataFrame(data=edit_data))


class SQLEditLogAppender(EditLogAppender):
    def __init__(self, dataset: Dataset) -> None:
        self.dataset = dataset
        self.executor = SQLExecutor2(dataset=self.dataset)

    def append(self, log: EditLog):
        insert_query = (
            InsertQueryBuilder(self.dataset)
            .add_columns(COLUMNS)
            .add_value(
                [log.key, log.column_name, log.value, log.date, log.user, log.action]
            )
            .build()
        )
        self.executor.query_to_df(insert_query, post_queries=["COMMIT"])


class EditLogAppenderFactory:
    def create(self, dataset: Dataset) -> EditLogAppender:
        if is_sql_dataset(dataset):
            return SQLEditLogAppender(dataset)
        else:
            return GenericEditLogAppender(dataset)
