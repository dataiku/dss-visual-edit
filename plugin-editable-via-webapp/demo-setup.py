import dataiku
import requests

VERSION = "v1.1.1"

dataiku.clear_remote_dss()
dataiku.set_remote_dss("https://dss-39ddd2ed-10872c17-int2.gis-dataiker-2.getitstarted.dataiku.com/", "8lihQTWoK5W6DtodNUOzFNbmo0YBXIrD") # TODO: define environment variables and get them via os.environ - for this I need to create an API key on the Demo instance on Dataiku Online, via the saas+maintenance account
client = dataiku.api_client()

# Delete projects and import again

project = client.get_project('CATEGORIZE_TRANSACTIONS')
project.delete()

# MAKE SURE LAST CHANGES WERE COMMITTED
project_transactions_zipfile = requests.get("https://github.com/louisdorard/dataiku-categorize-transactions/archive/refs/heads/master.zip")
with open("CATEGORIZE_TRANSACTIONS.zip", "rb") as f:
    client.prepare_project_import(f).execute({"targetProjectKey": "CATEGORIZE_TRANSACTIONS"})



# Uninstall plugin and install again (including code env)

plugin = client.get_plugin('editable-via-webapp')
future = plugin.delete(force=True)
future.wait_for_result()

lca_zipfile = requests.get("https://github.com/dataiku/lca/archive/refs/tags/" + VERSION + ".zip")

# TODO: unzip and get plugin only, to zip it again

import zipfile
with zipfile.ZipFile("lca-1.1.1.zip", 'r') as zip_ref:
    zip_ref.extractall("./")

plugin_file = "dssPlugin_editable-via-webapp__2022_05_17.zip"
with open(plugin_file, "r") as f:
    client.install_plugin_from_archive(f) # upload fails with UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb1 in position 12: invalid start byte

plugin = client.get_plugin("myplugin") # TODO: change plugin id
future = plugin.create_code_env(python_interpreter="PYTHON36")
result = future.wait_for_result()

settings = plugin.get_settings()
settings.set_code_env(result["TODO:"])
settings.save()