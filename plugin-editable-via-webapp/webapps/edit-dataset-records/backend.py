# -*- coding: utf-8 -*-

# Dash webapp to edit dataset records

#%%
# when using interactive execution:
# import sys
# sys.path.append('../../python-lib')
# original_ds_name = ...
# project_key = ...

#%%
from os import getenv
from json5 import load, loads
if (getenv("DKU_CUSTOM_WEBAPP_CONFIG")):
    print("Webapp is being run in Dataiku")
    run_context = "dataiku"

    from dataiku.customwebapp import get_webapp_config
    original_ds_name = get_webapp_config().get("original_dataset")
    editschema = loads(get_webapp_config().get("editschema"))
else:
    print("Webapp is being run outside of Dataiku")
    run_context = "local"
    original_ds_name = getenv("ORIGINAL_DATASET")
    editschema = load(open(getenv("EDITSCHEMA_PATH")))

    from flask import Flask
    from dash import Dash
    f_app = Flask(__name__)
    app = Dash(__name__, server=f_app)
    application = app.server

#%%
# Define the webapp layout and components
from EditableEventSourcedAIO import EditableEventSourcedAIO
def serve_layout():
    return EditableEventSourcedAIO(original_ds_name, editschema)
app.layout = serve_layout

#%%
if __name__=="__main__":
    if run_context=="local":
        print("Running in debug mode")
        app.run_server(debug=True)
print("Webapp OK")
