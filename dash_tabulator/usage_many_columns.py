import dash_tabulator
import dash
from dash.dependencies import Input, Output
from dash import html
from dash import dcc

app = dash.Dash(__name__)

from pandas import DataFrame
from numpy import random
df = DataFrame(random.random_sample(size=(10, 100))).astype(str)
random.random_sample()
data = df.to_dict('records')

df.columns = df.columns.to_series().astype(str)
cols = DataFrame(df.columns, columns=["field"])
columns = cols.to_dict('records')

app.layout = html.Div([
    dash_tabulator.DashTabulator(
        id="tabulator",
        columns=columns,
        data=data
    ),
    dcc.Interval(
                id='interval-component-iu',
                interval=1*10, # in milliseconds
                n_intervals=0,
                max_intervals=0
            )
])

@app.callback([ Output('tabulator', 'columns'),
                Output('tabulator', 'data')],
                [Input('interval-component-iu', 'n_intervals')])
def initialize(val):
    return columns, data

if __name__ == '__main__':
    app.run_server(debug=True)