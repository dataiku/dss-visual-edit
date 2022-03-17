from dash import Dash, dash_table, html
from dash.dependencies import Input, Output, State
import pandas as pd

"""
Some inspiration:
* https://community.plotly.com/t/dash-table-datatable-determining-which-rows-have-changed/16618/3
* https://community.plotly.com/t/row-update-in-dash-table-datatable/15564/5
* https://towardsdatascience.com/creating-interactive-data-tables-in-plotly-dash-6d371de0942b

Useful doc:
* https://dash.plotly.com/datatable/editable
* Previous version of data_table_experiments allowed to use a `row_update` property: https://github.com/plotly/dash-recipes/blob/master/dash-datatable-editable-update-self.py
"""

df = pd.read_csv("iris.csv").head(10)
app = Dash()
app.layout = html.Div([
    html.H4('Edit DATASET_NAME'),
    html.Div([
        html.Div("Select a cell, type a new value, and press Enter to save."),
        html.Br(),
        html.Div(
            children=dash_table.DataTable(
                id='editable-table',
                columns=([{"name": i, "id": i} for i in df.columns]),
                data=df.to_dict('records'),
                editable=True
            ),
        ),
        html.Pre(id='output')
    ])
])

@app.callback(Output('output', 'children'),
              [State('editable-table', 'active_cell'),
              Input('editable-table', 'data')], prevent_initial_call=True)
def update_db(cell_coordinates, table_data):
    cell_coordinates["row"] = cell_coordinates["row"]-1
    str_return = "This cell was updated: " + str(cell_coordinates) + "\n"
    db_response = "New value: " + str(table_data[cell_coordinates["row"]][cell_coordinates["column_id"]])
    return str_return, db_response

if __name__ == '__main__':
    app.run_server(debug=True)