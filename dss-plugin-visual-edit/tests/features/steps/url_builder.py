from __future__ import annotations

import os

from dataikuapi.dss.webapp import DSSWebApp
from dssgherkin.typings.generic_context_type import AugmentedBehaveContext

webapp_run_ids = os.getenv("DKU_WEBAPP_RUN_IDS")
assert webapp_run_ids, "Expected DKU_WEBAPP_RUN_IDS to be set."
webapp_id_to_run_id = {}
for tuple in list(webapp_run_ids.split(",")):
    arr = tuple.split(":")
    webapp_id_to_run_id = webapp_id_to_run_id | {arr[0]: arr[1]}

webapp_cookie = os.getenv("DKU_WEBAPP_COOKIE")
cookies = ""


def get_cookie(ctx: AugmentedBehaveContext) -> str:
    assert ctx.dss_cookies
    global cookies
    if not cookies:
        for c in ctx.dss_cookies:
            name = c.get("name", "")
            value = c.get("value", "")
            if name and value:
                cookies += f"{name}={value};"

    return cookies


def create_webapp_backend_url(webapp: DSSWebApp):
    match = webapp_id_to_run_id.get(webapp.webapp_id, "")
    if not match:
        raise Exception(f"Missing configuration for web app id {webapp.webapp_id}.")
    return f"/web-apps-backends/{webapp.project_key}/{match}/"
