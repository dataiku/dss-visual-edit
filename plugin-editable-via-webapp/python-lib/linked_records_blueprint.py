import logging
from flask import Blueprint, jsonify, request
from dataiku_utils import get_dataframe_filtered
from EditableEventSourced import EditableEventSourced

linked_records_blueprint = Blueprint("linked_records_blueprint", __name__)

# Label and lookup endpoints used by Tabulator when formatting or editing linked records
###


@linked_records_blueprint.route(
    "/label/<linked_ds_name>/<ds_name>/", methods=["GET", "POST"]
)
def label_endpoint(linked_ds_name, ds_name):
    """
    Return the label of a row in a linked dataset

    Params:
    - key: value of the primary key identifying the row to read

    Returns: the value of the column defined as label in the linked dataset
    """

    if request.method == "POST":
        key = request.get_json().get("key")
    else:
        key = request.args.get("key", "")
    label = ""

    # Return data only when it's a linked dataset
    ees = EditableEventSourced(ds_name)
    if ees.linked_records:
        for lr in ees.linked_records:
            if linked_ds_name == lr["ds_name"]:
                linked_ds_key = lr["ds_key"]
                linked_ds_label = lr["ds_label"]
                # Return label only if a label column is defined (and different from the key column)
                if key != "" and linked_ds_label and linked_ds_label != linked_ds_key:
                    if lr.get("ds"):
                        label = lr["ds"].get_cell_value_sql_query(
                            linked_ds_key, key, linked_ds_label
                        )
                    else:
                        linked_df = lr["df"].set_index(linked_ds_key)
                        label = linked_df.loc[key, linked_ds_label]
                else:
                    label = key
    return label


@linked_records_blueprint.route("/lookup/<linked_ds_name>", methods=["GET", "POST"])
def lookup_endpoint(linked_ds_name):
    """
    Get label and lookup values in a linked dataset, matching a search term.

    This endpoint is used by Tabulator when editing a linked record. The values it returns are read by the `itemFormatter` function of the Tabulator table, which displays a dropdown list of linked records whose labels match the search term.
    """
    if request.method == "POST":
        term = request.get_json().get("term")
    else:
        term = request.args.get("term", "")
    logging.info(
        f"""Received a request for dataset "{linked_ds_name}", term "{term}" ({len(term)} characters)"""
    )
    response = jsonify({})

    # Return data only when linked_ds_name corresponds to a linked dataset
    n_results = 10
    ees = EditableEventSourced(ds_name)
    if ees.linked_records:
        for lr in ees.linked_records:
            if linked_ds_name == lr["ds_name"]:
                linked_ds_key = lr["ds_key"]
                linked_ds_label = lr["ds_label"]
                linked_ds_lookup_columns = lr["ds_lookup_columns"]
                if lr.get("ds"):
                    # Use the Dataiku API to filter the dataset
                    linked_df_filtered = get_dataframe_filtered(
                        linked_ds_name,
                        project_key,
                        linked_ds_label,
                        term.strip().lower(),
                        n_results,
                    )
                else:
                    linked_df = lr["df"].set_index(linked_ds_key)
                    if term == "":
                        n_results = (
                            100  # show more options if no search term is provided
                        )
                        linked_df_filtered = linked_df.head(n_results).reset_index()
                    else:
                        # Filter linked_df for rows whose label contains the search term
                        linked_df_filtered = (
                            linked_df[
                                linked_df[linked_ds_label]
                                .str.lower()
                                .str.contains(term.strip().lower())
                            ]
                            .head(n_results)
                            .reset_index()
                        )
                    logging.debug(f"Found {linked_df_filtered.size} entries")
                    response = linked_df_filtered.to_json(orient="index")

            logging.debug(f"Found {linked_df_filtered.size} entries")
            editor_values_param = get_values_from_df(
                linked_df_filtered,
                linked_ds_key,
                linked_ds_label,
                linked_ds_lookup_columns,
            )
            response = jsonify(editor_values_param)

    return response
