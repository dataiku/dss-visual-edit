from flask import Blueprint, jsonify, make_response, request
from EditableEventSourced import EditableEventSourced

crud_blueprint = Blueprint("crud_blueprint", __name__)

# CRUD endpoints
###


@crud_blueprint.route("/<ds_name>/create", methods=["POST"])
def create_endpoint():
    """
    Create a new row.

    Params:
    - primaryKeys: dict containing values for all primary keys defined in the initial data editing setup; the set of values must be unique.
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
    # TODO: check set of primary key values is unique?
    ees = EditableEventSourced(ds_name)
    ees.create_row(primary_keys_values, column_values)
    response = jsonify({"msg": "New row created"})
    return response


@crud_blueprint.route("/<ds_name>/read", methods=["POST"])
def read_endpoint():
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
    - If no row was created, editable columns are those defined in the initial data editing setup.
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
    ees = EditableEventSourced(ds_name)
    response = ees.get_row(primary_keys_values).to_json()
    return response


@crud_blueprint.route("/<ds_name>/read-all-edits", methods=["GET"])
def read_all_edits_endpoint():
    """
    Read all rows edited or created via webapp or API

    Returns: CSV-formatted dataset with rows that were created or edited, and values of primary key and editable columns. See remarks of the `read` endpoint.
    """
    ees = EditableEventSourced(ds_name)
    response = make_response(ees.get_edited_cells_df_indexed().to_csv())
    response.headers["Content-Disposition"] = (
        "attachment; filename=" + original_ds_name + "_edits.csv"
    )
    response.headers["Content-Type"] = "text/csv"
    response.headers["Cache-Control"] = "no-store"
    return response


@crud_blueprint.route("/update", methods=["GET", "POST"])
def update_endpoint():
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
        primary_keys_values = request.get_json().get("primaryKeys")
        column = request.get_json().get("column")
        value = request.get_json().get("value")
    else:
        primary_keys_values = request.args.get("primaryKeys", "")
        column = request.args.get("column", "")
        value = request.args.get("value", "")
    ees = EditableEventSourced(ds_name)
    info = ees.update_row(primary_keys_values, column, value)
    response = jsonify({"msg": info})
    return response


@crud_blueprint.route("/<ds_name>/delete", methods=["GET", "POST"])
def delete_endpoint():
    """
    Delete a row

    Params:
    - primaryKeys: value(s) of the primary key(s) identifying the row to delete (see read endpoint)

    Returns a message confirming row deletion.
    """
    if request.method == "POST":
        primary_keys = request.get_json().get("primaryKeys")
    else:
        primary_keys = request.args.get("primaryKeys", "")
    ees = EditableEventSourced(ds_name)
    info = ees.delete_row(primary_keys)
    response = jsonify({"msg": f"Row deleted"})
    return response
