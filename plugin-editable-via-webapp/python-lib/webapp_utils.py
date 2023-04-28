from pandas import DataFrame
from json import loads
from os import getenv
import dataiku
import requests


def call_rest_api(path):
    PORT = dataiku.base.remoterun.get_env_var("DKU_BASE_PORT")
    if (PORT == None):
        PORT = "11200"
    BASE_API_URL = "http://127.0.0.1:" + PORT + \
        "/public/api/projects/" + getenv("DKU_CURRENT_PROJECT_KEY")
    return loads(
        requests.get(
            url=BASE_API_URL + path,
            headers=dataiku.core.intercom.get_auth_headers(),
            verify=False
        ).text)


def get_webapp_json(webapp_ID):
    return call_rest_api("/webapps/" + webapp_ID)


def find_webapp_id(original_ds_name):
    webapps_df = DataFrame(call_rest_api("/webapps/"))
    webapps_edit_df = webapps_df[webapps_df["type"] ==
                                 "webapp_editable-via-webapp_edit-dataset-records"]
    webapps_edit_df["original_ds_name"] = webapps_edit_df.apply(
        lambda row: get_webapp_json(row["id"]).get(
            "config").get("original_dataset"),
        axis=1)
    return webapps_edit_df[webapps_edit_df["original_ds_name"] == original_ds_name].iloc[0]["id"]
