import behave
from dssgherkin.typings.generic_context_type import AugmentedBehaveContext

from features.steps.url_builder import create_webapp_backend_url, get_cookie
from dssgherkin.steps.helpers import get_webapp


@behave.when("I edit rows as such")
def edit_rows(ctx: AugmentedBehaveContext):
    webapp = get_webapp(ctx, None, None)
    assert webapp
    assert ctx.table

    for row in ctx.table.rows:
        primary_keys = row["primary_keys"].split(";")
        values = row["primary_keys_values"].split(";")
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

        url = f"{ctx.dss_client.host}{create_webapp_backend_url(webapp)}update"
        response = ctx.dss_client._session.request(
            "POST",
            url,
            json=body,
            cookies={"Cookie": get_cookie()},
        )

        assert response.ok
