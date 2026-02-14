import pytest
from unittest.mock import MagicMock, patch

from webapp.db.querybuilder import BigQueryInsertQueryBuilder

@pytest.fixture
def mock_dataset():
    dataset = MagicMock(name="MockDataset")
    dataset.get_location_info.return_value = {
        "info": {
            "databaseType": "bigquery",
            "table": "my_table",
            "schema": "my_schema"
        }
    }
    return dataset

@pytest.fixture
def mock_get_table_name_from_bq_dataset():
    with patch("webapp.db.querybuilder.get_table_name_from_bq_dataset", return_value="project.dataset.table") as mock_func:
        yield mock_func


@pytest.fixture
def mock_toSQL():
    with patch("webapp.db.querybuilder.toSQL") as mock_func:
        mock_func.side_effect = lambda builder, dataset: f"{builder}"
        yield mock_func


def test_initialization(mock_dataset, mock_get_table_name_from_bq_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    assert builder.dataset == mock_dataset
    assert builder.table_name == "project.dataset.table"
    assert builder.columns == []
    assert builder.values == []


def test_add_column(mock_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    builder.add_column("col1")
    assert builder.columns == ["col1"]


def test_add_columns(mock_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    builder.add_columns(["col1", "col2", "col3"])
    assert builder.columns == ["col1", "col2", "col3"]


def test_add_value(mock_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    builder.add_columns(["col1", "col2"])
    builder.add_value(["val1", "val2"])
    assert builder.values == [["val1", "val2"]]


def test_add_value_mismatched_columns(mock_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    builder.add_columns(["col1", "col2"])
    with pytest.raises(ValueError, match="Number of values does not match number of columns."):
        builder.add_value(["val1"])


def test_build_query_no_columns(mock_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    with pytest.raises(ValueError, match="No columns defined for INSERT query."):
        builder.build()


def test_query_start(mock_dataset, mock_get_table_name_from_bq_dataset):
    builder = BigQueryInsertQueryBuilder(dataset=mock_dataset)
    result = builder._query_start()
    assert result == "INSERT INTO `project.dataset.table`"
