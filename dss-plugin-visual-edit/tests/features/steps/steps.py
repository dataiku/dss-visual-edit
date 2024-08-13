import behave
from dssgherkin.typings.generic_context_type import AugmentedBehaveContext
from requests import post

from features.steps.url_builder import (
    create_api_url,
    get_cookie_as_dict,
)
from dssgherkin.steps.helpers import get_webapp


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
        response = post(url, json=body, cookies=get_cookie_as_dict(ctx))

        response.raise_for_status()


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
        response = post(url, json=body, cookies=get_cookie_as_dict(ctx))

        response.raise_for_status()

        result = response.json()
        assert "msg" in result and result["msg"] == "Unauthorized\n"
