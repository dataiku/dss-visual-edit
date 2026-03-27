from __future__ import annotations

import logging
from typing import List

from dataiku.core.schema_handling import CASTERS
from flask import Blueprint, Response, jsonify, request
from pandas.api.types import is_float_dtype, is_integer_dtype

from DataEditor import DataEditor
from dataiku_utils import (
    get_linked_dataframe_filtered,
    get_linked_label,
)
from tabulator_utils import get_formatted_items_from_linked_df
from webapp.api.utils import use_data_editor
from webapp.config.loader import webapp_config
from webapp.config.models import LinkedRecord

logger = logging.getLogger(__name__)

linked_dataset_blueprint = Blueprint("linkeddataset", __name__, url_prefix="/linkeddataset")


def _get_matching_linked_record_conf(data_editor: DataEditor, dataset_name: str) -> LinkedRecord | None:
    candidate_linked_records: List[LinkedRecord] = [
        lr for lr in data_editor.linked_records if lr.ds_name == dataset_name
    ]
    if not candidate_linked_records:
        logger.error("Unknown linked record for dataset %s.", dataset_name)
        return None

    if len(candidate_linked_records) > 1:
        logger.error(
            "Found several linked records configurations for dataset %s whereas only one was expected.", dataset_name
        )
        return None

    return candidate_linked_records[0]


@linked_dataset_blueprint.route("/label/<linked_ds_name>", methods=["GET", "POST"])
@use_data_editor
def get_label_from_row_key(data_editor: DataEditor, linked_ds_name: str) -> Response:
    """
    Return the label of a row in a linked dataset

    Params:
    - key: value of the primary key identifying the row to read

    Returns: the value of the column defined as label in the linked dataset
    """

    if request.method == "POST":
        key = request.get_json().get("key")
    elif request.method == "GET":
        key = request.args.get("key", "")
    else:
        logger.error("Bad method %s was used to get label from row key.", request.method)
        return Response("Bad method.", 405)

    linked_record: LinkedRecord | None = _get_matching_linked_record_conf(data_editor, linked_ds_name)
    if linked_record is None:
        return Response("Unexpected error.", 500)

    # Cast provided key value into appropriate type (necessary for integers for example)
    linked_key_type: str = data_editor.schema_columns_df.loc[linked_record.name, "type"]  # type: ignore
    linked_key_dtype = CASTERS.get(linked_key_type)
    try:
        if linked_key_dtype and is_integer_dtype(linked_key_dtype):
            key = int(key)
        if linked_key_dtype and is_float_dtype(linked_key_dtype):
            key = float(key)
    except Exception as ex:
        logger.error("Invalid key type.", exc_info=ex)
        return Response("Invalid key type.", 400)

    return get_linked_label(linked_record, key)


@linked_dataset_blueprint.route("/lookup/<linked_ds_name>", methods=["GET", "POST"])
@use_data_editor
def search(data_editor: DataEditor, linked_ds_name: str) -> Response:
    """
    Get label and lookup values in a linked dataset. Can be used to perform a search in a linked dataset.

    If a search term is provided, return a list of options that match this term. Otherwise, return a single option corresponding to the provided key.

    Params:
    - term: the search term to filter linked records

    Returns: a list of matching options
    """

    if request.method == "POST":
        term = request.get_json().get("term")
    elif request.method == "GET":
        term = request.args.get("term", "")
    else:
        logger.error("Bad method %s was used to search a linked dataset.", request.method)
        return Response("Bad method.", 405)

    term = term.strip().lower()
    logger.debug(
        f"""Received a request to get options from linked dataset "{linked_ds_name}" matching search term "{term}" ({len(term)} characters)"""
    )

    # Find the linked record whose linked dataset is requested
    linked_record: LinkedRecord | None = _get_matching_linked_record_conf(data_editor, linked_ds_name)
    if linked_record is None:
        return Response("Unexpected error.", 500)

    linked_ds_key = linked_record.ds_key
    linked_ds_label = linked_record.ds_label
    linked_ds_lookup_columns = linked_record.ds_lookup_columns

    # when a search term is provided, show a limited number of options matching this term
    # otherwise, show many options to choose from
    n_options = 10 if term != "" else 1000

    linked_df_filtered = get_linked_dataframe_filtered(
        linked_record=linked_record,
        project_key=webapp_config.project_key,
        filter_term=term,
        n_results=n_options,
    )

    editor_values_param = get_formatted_items_from_linked_df(
        linked_df=linked_df_filtered,
        key_col=linked_ds_key,
        label_col=linked_ds_label,
        lookup_cols=linked_ds_lookup_columns,
    )
    return jsonify(editor_values_param)
