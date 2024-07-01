from __future__ import annotations

import os

from dataikuapi.dss.webapp import DSSWebApp

webapp_run_id = os.getenv("DKU_WEBAPP_RUN_ID")
webapp_cookie = os.getenv("DKU_WEBAPP_COOKIE")


def get_cookie() -> str:
    if webapp_cookie:
        return webapp_cookie
    raise Exception("Cookie must be specified in env var DKU_WEBAPP_COOKIE.")


def create_webapp_backend_url(webapp: DSSWebApp):
    if webapp_run_id:
        return f"/web-apps-backends/{webapp.project_key}/{webapp_run_id}/"
    raise Exception("Web app run id must be specified in env var DKU_WEBAPP_RUN_ID.")
