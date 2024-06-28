from __future__ import annotations

import os

from dataikuapi.dss.webapp import DSSWebApp

answers_run_id = os.getenv("DKU_ANSWERS_RUN_ID")
answers_cookie = os.getenv("DKU_ANSWERS_COOKIE")


def get_cookie() -> str:
    if answers_cookie:
        return answers_cookie
    return "tofill"


def create_webapp_backend_url(webapp: DSSWebApp):
    if answers_run_id:
        return f"/web-apps-backends/{webapp.project_key}/{answers_run_id}/"
    return f"/web-apps-backends/{webapp.project_key}/cbrroHcg/"
