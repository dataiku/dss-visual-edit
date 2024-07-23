# Low-code webapp customizations with Dash

## Basic usage

This example is based on the tshirt orders dataset from the [Basics 101 course](https://academy.dataiku.com/basics-101) of the Dataiku Academy. We use the plugin's [`dash_tabulator` component](https://github.com/dataiku/dss-visual-edit/blob/master/dash_tabulator/README.md) for the webapp's data table.

Import classes from dash and from the plugin's library:

```python
from dash import html, Input, Output
import dataiku
dataiku.use_plugin_libs("visual-edit")
DataEditor = dataiku.import_from_plugin("visual-edit", "DataEditor")
tabulator_utils = dataiku.import_from_plugin("visual-edit", "tabulator_utils")
dash_tabulator = dataiku.import_from_plugin("visual-edit", "dash_tabulator")
```

Instantiate `DataEditor`, which will later be used to define the data to load into the table:

```python
ORIGINAL_DATASET = "orders"
PRIMARY_KEYS = ["order_id"]
EDITABLE_COLUMN_NAMES = ["tshirt_price", "tshirt_quantity"]

de = DataEditor.DataEditor(
    original_ds_name=ORIGINAL_DATASET,
    primary_keys=PRIMARY_KEYS,
    editable_column_names=EDITABLE_COLUMN_NAMES
)
```

Define the columns to use in the data table. This is an object that tells `dash_tabulator` how to render each column, based on its type.

```python
columns = tabulator_utils.get_columns_tabulator(de)
```

Define the webapp's layout and components:

```python
def serve_layout():
    return html.Div([
        dash_tabulator.DashTabulator(
            id="quickstart-datatable",
            datasetName=ORIGINAL_DATASET,
            data=de.get_edited_df().to_dict("records"),
            columns=columns
        ),
        html.Div(id="quickstart-output")
    ])

app.layout = serve_layout
```

Define a callback on cell edited:

```python
@app.callback(
    Output("quickstart-output", "children"),
    Input("quickstart-datatable", "cellEdited"),
    prevent_initial_call=True,
)
def log_edit(cell):
    """
    Record edit in editlog, once a cell has been edited

    cell is a dict with the following properties: row, field, value
    """
    return de.update_row(cell["row"], cell["field"], cell["value"])
```

## Leveraging advanced Tabulator features

`dash_tabulator` is based on [Tabulator](https://tabulator.info/). You can leverage Tabulator's advanced features by defining columns with custom properties.

Here we define a calculated column using the Tabulator `mutator` feature and a Javascript function that implements the calculation to perform (here: adding 2 to the values of the `tshirt_quantity` column). We also demonstrate usage of Tabulator's `headerFilter` and `sorter` features.

In the previous webapp example, replace the definition of `columns` with the following:

```python
from dash_extensions import javascript

columns = [
    {"field": "order_id", "headerFilter": True},
    {"field": "pages_visited", "sorter": "number"},
    {"field": "customer_id", "headerFilter": True},
    {"field": "tshirt_category", "headerFilter": True},
    {"field": "tshirt_price", "sorter": "number", "editor": "number"},
    {
        "field": "tshirt_quantity",
        "sorter": "number",
        "editor": "number",
        "mutateLink": "calculated",
    },
    {"field": "comments", "editor": "input"},
    {
        "field": "calculated",
        "title": "calculated",
        "mutator": javascript.assign(
            """
function(value, data){
return parseInt(data.tshirt_quantity) + 2;
}
"""
        ),
    },
]
```

## Deeper customizations

See the [dash_tabulator documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dash_tabulator/README.md) and the [Plugin Developer Documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dss-plugin-visual-edit/README.md) for more ways to customize the webapp.
