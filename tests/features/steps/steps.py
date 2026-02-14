import logging
from typing import Dict

import behave
from dssgherkin.steps.helpers import get_webapp
from dssgherkin.typings.generic_context_type import AugmentedBehaveContext
from requests import Response, get, post
from tenacity import retry, stop_after_attempt, wait_fixed

from features.steps.url_builder import (
    create_api_url,
    get_cookie_as_dict,
)

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def retry_get(url, cookies: Dict[str, str]) -> Response:
    try:
        response = get(url, cookies=cookies)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.warning("Error during get request.", exc_info=e)
        raise


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def retry_post(url, json, cookies: Dict[str, str]) -> Response:
    try:
        response = post(url, json=json, cookies=cookies)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.warning("Error during post request.", exc_info=e)
        raise


@behave.when("I edit rows as such")
def edit_rows(ctx: AugmentedBehaveContext):
    webapp = get_webapp(ctx, None, None)
    assert webapp
    assert ctx.table

    for row in ctx.table.rows:
        primary_keys = row["primary_keys"].split(",")
        values = row["primary_keys_values"].split(",")
        assert len(primary_keys) == len(values)
        edited_column = row["edited_column"]
        edited_value = row["edited_value"]

        primary_keys_body = {}
        index = 0
        for pk in primary_keys:
            primary_keys_body = primary_keys_body | {pk: values[index]}
            index += 1

        body = {
            "primaryKeys": primary_keys_body,
            "column": edited_column,
            "value": edited_value,
        }

        url = create_api_url(ctx, "update")
        response = retry_post(url, json=body, cookies=get_cookie_as_dict(ctx))

        response.raise_for_status()


@behave.then('the label for key "{key}" in dataset "{ds_name}" is "{label}"')
def assert_label(ctx: AugmentedBehaveContext, key: str, ds_name: str, label: str):
    webapp = get_webapp(ctx, None, None)
    assert webapp

    url = create_api_url(ctx, f"label/{ds_name}?key={key}")

    response = retry_get(url, get_cookie_as_dict(ctx))

    response.raise_for_status()

    assert response.text == label


@behave.then('the lookup result for term "{term}" in dataset "{ds_name}"')
def assert_lookup(ctx: AugmentedBehaveContext, term: str, ds_name: str):
    webapp = get_webapp(ctx, None, None)
    assert webapp

    url = create_api_url(ctx, f"lookup/{ds_name}?term={term}")

    response = retry_get(url, get_cookie_as_dict(ctx))

    response.raise_for_status()
    result = response.json()

    if ctx.table and len(ctx.table.rows):
        assert len(result) == len(ctx.table.rows)

        value_type = type(result[0]["value"])

        converted_rows = []
        for row in ctx.table.rows:
            dict_row = row.as_dict()
            if value_type is int:
                dict_row["value"] = int(row["value"])
            elif value_type is float:
                dict_row["value"] = float(row["value"])

            converted_rows.append(dict_row)

        assert result == converted_rows
    else:
        assert result == []


@behave.then("editing rows as such is unauthorized")
def unauthorized_edit_rows(ctx: AugmentedBehaveContext):
    webapp = get_webapp(ctx, None, None)
    assert webapp
    assert ctx.table

    for row in ctx.table.rows:
        primary_keys = row["primary_keys"].split(",")
        values = row["primary_keys_values"].split(",")
        assert len(primary_keys) == len(values)
        edited_column = row["edited_column"]
        edited_value = row["edited_value"]

        primary_keys_body = {}
        index = 0
        for pk in primary_keys:
            primary_keys_body = primary_keys_body | {pk: values[index]}
            index += 1

        body = {
            "primaryKeys": primary_keys_body,
            "column": edited_column,
            "value": edited_value,
        }

        url = create_api_url(ctx, "update")
        response = retry_post(url, json=body, cookies=get_cookie_as_dict(ctx))

        response.raise_for_status()

        result = response.json()
        assert "msg" in result and result["msg"] == "Unauthorized\n"
