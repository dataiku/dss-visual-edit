import dash_tabulator
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from dash_extensions.javascript import Namespace
#from textwrap import dedent as d
#import json

app = dash.Dash(__name__)

ns = Namespace("myNamespace", "tabulator")

columns = [
                { "title": "Name", "field": "name"},
                { "title": "Age", "field": "age"},
                { "title": "Favourite Color", "field": "col"},
                { "title": "Date Of Birth", "field": "dob"},
                { "title": "Rating", "field": "rating"},
                { "title": "Passed?", "field": "passed"},
                {"title": "Print", "field": "print"}
              ]
data = [
                {"id":1, "name":"Oli Bob", "age":"12", "col":"red", "dob":"", "print" :"foo"},
                {"id":2, "name":"Mary May", "age":"1", "col":"blue", "dob":"14/05/1982", "print" :"foo"},
                {"id":3, "name":"Christine Lobowski", "age":"42", "col":"green", "dob":"22/05/1982", "print" :"foo"},
                {"id":4, "name":"Brendon Philips", "age":"125", "col":"orange", "dob":"01/08/1980", "print" :"foo"},
                {"id":5, "name":"Margret Marmajuke", "age":"16", "col":"yellow", "dob":"31/01/1999", "print" :"foo"},
                {"id":6, "name":"Fred Savage", "age":"16", "col":"yellow", "rating":"1", "dob":"31/01/1999", "print" :"foo"},
                {"id":7, "name":"Brie Larson", "age":"30", "col":"blue", "rating":"1", "dob":"31/01/1999", "print" :"foo"},
              ]

options = { "groupBy": "col", "selectable":"true", "columnResized" : ns("columnResized")}
downloadButtonType = {"css": "btn btn-primary", "text":"Export", "type":"xlsx"}
clearFilterButtonType = {"css": "btn btn-outline-dark", "text":"Clear Filters"}
initialHeaderFilter = [{"field":"col", "value":"blue"}]

app.layout = html.Div([
    dash_tabulator.DashTabulator(
        id='tabulator',
        columns=columns,
        data=data
        # theme="tabulator",
        # options=options,
        # downloadButtonType=downloadButtonType,
        # clearFilterButtonType=clearFilterButtonType,
    ),
    html.Div(id='output'),
    dcc.Interval(
                id='interval-component-iu',
                interval=1*10, # in milliseconds
                n_intervals=0,
                max_intervals=0
            )

])

@app.callback(Output('output', 'children'),
    [Input('tabulator', 'rowClicked'),
    Input('tabulator', 'multiRowsClicked'),
    Input('tabulator', 'cellEdited'),
    Input('tabulator', 'dataChanged'),
    Input('tabulator', 'dataFiltering'),
    Input('tabulator', 'dataFiltered')])
def display_output(row, multiRowsClicked, cell, dataChanged, filters, dataFiltered):
    print("row: {}".format(str(row)))
    print("cell: {}".format(str(cell)))
    print("data changed: {}".format(str(dataChanged)))
    print("filters: {}".format(str(filters)))
    print("data filtered: {}".format(str(dataFiltered)))
    return 'You have clicked row {} ; cell {} ; multiRowsClicked {}'.format(row, cell, multiRowsClicked)


if __name__ == '__main__':
    app.run_server(debug=True)
