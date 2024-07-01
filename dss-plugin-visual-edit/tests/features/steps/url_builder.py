from __future__ import annotations

import os

from dataikuapi.dss.webapp import DSSWebApp

webapp_run_ids = os.getenv("DKU_WEBAPP_RUN_IDS")
assert webapp_run_ids, "Expected DKU_WEBAPP_RUN_IDS to be set."
webapp_id_to_run_id = {}
for tuple in list(webapp_run_ids.split(",")):
    arr = tuple.split(":")
    webapp_id_to_run_id = webapp_id_to_run_id | {arr[0]: arr[1]}

webapp_cookie = os.getenv("DKU_WEBAPP_COOKIE")


def get_cookie() -> str:
    if webapp_cookie:
        return webapp_cookie
    raise Exception("Cookie must be specified in env var DKU_WEBAPP_COOKIE.")


def create_webapp_backend_url(webapp: DSSWebApp):
    match = webapp_id_to_run_id.get(webapp.webapp_id, "")
    if not match:
        raise Exception(f"Missing configuration for web app id {webapp.webapp_id}.")
    return f"/web-apps-backends/{webapp.project_key}/{match}/"
