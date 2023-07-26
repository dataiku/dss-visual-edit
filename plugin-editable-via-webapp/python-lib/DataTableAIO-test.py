# Dash webapp with a DataTableAIO component that displays data coming from a Dataiku dataset named "my_dataset"
#
from flask import Flask
import dash
from os import getenv
from DataTableAIO import DataTableAIO

original_ds_name = getenv("ORIGINAL_DATASET")

server = Flask(__name__)
app = dash.Dash(__name__, server=server)
app.enable_dev_tools(debug=True, dev_tools_ui=True)
app.layout = dash.html.Div([DataTableAIO(aio_id="dt", ds_name=original_ds_name)])

if __name__ == "__main__":
    app.run_server(debug=True)
