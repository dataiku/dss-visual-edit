from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, make_response, request
from pydantic import BaseModel

from DataEditor import DataEditor, EditFailure, EditFreezed, EditSuccess, EditUnauthorized
from webapp.api.utils import use_data_editor
from webapp.config.loader import webapp_config

logger = logging.getLogger(__name__)

editlogs_blueprint = Blueprint("editlogs", __name__, url_prefix="/editlogs")


class UpdateRowParams(BaseModel):
    primaryKeys: dict
    column: str = ""
    value: Any = ""


class DeleteRowParams(BaseModel):
    primaryKeys: dict


def __edit_result_to_message__(
    r: EditSuccess | EditFailure | EditUnauthorized | EditFreezed,
) -> str:
    if isinstance(r, EditSuccess):
        return "Row successfully updated"
    elif isinstance(r, EditFailure):
        return r.message
    elif isinstance(r, EditUnauthorized):
        return "Unauthorized"
    elif isinstance(r, EditFreezed):
        return "Edits are disabled."
    else:
        return "Unexpected update result"


@editlogs_blueprint.route("/create", methods=["POST"])
@use_data_editor
def create_row(data_editor: DataEditor) -> Response:
    """
    Create a new row.

    Params:
    - primaryKeys: dict containing values for all primary keys defined in the initial Visual Edit setup; the set of values must be unique.
    - columnValues: dict containing values for all other columns.

    Example request JSON:
    ```json
    {
        "primaryKeys": {
            "id": "My new unique id"
        },
        "columnValues": {
            "col1": "hey",
            "col2": 42,
            "col3": true
        }
    }
    ```

    Returns a message confirming row creation.

    Note: this method doesn't implement data validation / it doesn't check that the values are allowed for the specified columns.
    """
    primary_keys_values = request.get_json().get("primaryKeys")
    column_values = request.get_json().get("columnValues")
    data_editor.create_row(primary_keys_values, column_values)
    response = jsonify({"msg": "New row created"})
    return response


@editlogs_blueprint.route("/update", methods=["GET", "POST"])
@use_data_editor
def update_row(data_editor: DataEditor) -> Response:
    """
    Update a row

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to update (see read endpoint)
    - column: name of the column to update
    - value: value to set for the cell identified by key and column

    Example responses:
    - if column is an editable column:
    ```json
    { "msg": "Updated column _column_ where _list of primary key names_ is _primaryKeys_. New value: _value_." }
    ````
    - otherwise:
    ```json
    { "msg": "_column_ isn't an editable column" }
    ```

    Note: this method doesn't implement data validation / it doesn't check that the value is allowed for the specified column.
    """
    if request.method == "POST":
        params = UpdateRowParams(**request.get_json())
    elif request.method == "GET":
        params = UpdateRowParams(**request.args)  # type: ignore
    else:
        return Response("Method not allowed", status=405)

    results = data_editor.update_row(params.primaryKeys, params.column, params.value)
    info = ""
    for res in results:
        info += __edit_result_to_message__(res) + "\n"
    response = jsonify({"msg": info})
    return response


@editlogs_blueprint.route("/delete", methods=["DELETE"])
@use_data_editor
def delete_row(data_editor: DataEditor) -> Response:
    """
    Delete a row

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to delete (see read endpoint)

    Returns a message confirming row deletion.
    """
    params = DeleteRowParams(**request.get_json())
    result = data_editor.delete_row(params.primaryKeys)
    response = jsonify({"msg": __edit_result_to_message__(result)})
    return response


@editlogs_blueprint.route("/read", methods=["POST"])
@use_data_editor
def read_row(data_editor: DataEditor) -> Response:
    """
    Read a row that was created or edited via webapp or API

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to read

    Example request JSON:
    ```json
    {
        "primaryKeys": {
            "key1": "cat",
            "key2": "2022-12-21",
        }
    }
    ```

    Returns: JSON representation of the values of editable columns.
    - If some rows of the dataset were created, then by definition all columns are editable (including primary keys) .
    - If no row was created, editable columns are those defined in the initial Visual Edit setup.
    - Example API response:
    ```json
    {
        "columnValues": {
            "col1": "hey",
            "col2": 42,
            "col3": true
        }
    }
    ```
    """
    primary_keys_values = request.get_json().get("primaryKeys")
    response = data_editor.get_row(primary_keys_values).to_json()
    return response


@editlogs_blueprint.route("/read-all-edits", methods=["GET"])
@use_data_editor
def read_all_rows(data_editor: DataEditor) -> Response:
    """
    Read all rows edited or created via webapp or API

    Returns: CSV-formatted dataset with rows that were created or edited, and values of primary key and editable columns. See remarks of the `read` endpoint.
    """
    response = make_response(data_editor.get_edited_cells_df_indexed().to_csv())
    response.headers["Content-Disposition"] = f"attachment; filename={webapp_config.original_ds_name}_edits.csv"
    response.headers["Content-Type"] = "text/csv"
    response.headers["Cache-Control"] = "no-store"
    return response
