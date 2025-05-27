# Low-code webapp customizations with Dash

As seen in the [Introduction to Visual Edit's CRUD Python API](https://github.com/dataiku/dss-visual-edit/blob/master/docs/CRUD_example_usage.ipynb), one can use the Visual Edit API to add a data persistence layer to any webapp.

The plugin's Visual Webapp consists of a single data table component. In this guide, we show how to customize the layout of a data editing and validation webapp in Dash, based on such a component. This can be to:

- **Add other components to the layout**. The first section of this guide shows the minimal Dash code to use in order to get the same data table as in the Visual Webapp. This is based on the plugin's [`dash_tabulator` component](https://github.com/dataiku/dss-visual-edit/blob/master/dash_tabulator/README.md). You can then add other components to the Dash layout.
- **Customize the settings of the data table**. `dash_tabulator` is based on the [Tabulator](https://tabulator.info/) JavaScript library. The second section gives an example of how to leverage some of its advanced features by customizing column definitions.
- **Use a different data table component**. The third section shows how to use a different data table component in Dash, such as [AG Grid](https://dash.plotly.com/dash-ag-grid).

Note that these customizations don't need modifying the plugin nor converting to development mode.

## Basic usage of `dash_tabulator`

This example is based on the tshirt orders dataset from the [Basics 101 course](https://academy.dataiku.com/basics-101) of the Dataiku Academy.

Import classes from dash and from the plugin's library:

```python
from dash import html, Input, Output
import dataiku
dataiku.use_plugin_libs("visual-edit")
DataEditor = dataiku.import_from_plugin("visual-edit", "DataEditor")
tabulator_utils = dataiku.import_from_plugin("visual-edit", "tabulator_utils")
dash_tabulator = dataiku.import_from_plugin("visual-edit", "dash_tabulator")
```

Instantiate `DataEditor`, which will be used to get the edited data and load it when rendering the table, and to persist edits:

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

Define a function that creates a data table from a `DataEditor` object, which will be called when rendering the layout:

```python
def create_data_table(id, dataset_name, data_editor):
    data = data_editor.get_edited_df().to_dict("records")
    # Define the columns to use in the data table. This is an object that tells dash_tabulator how to render each column, based on its type.
    columns = tabulator_utils.get_columns_tabulator(data_editor)
    return dash_tabulator.DashTabulator(id, dataset_name, data, columns)
```

Define the webapp's layout and components:

```python
def serve_layout():
    return html.Div([
        create_data_table(
            id="quickstart-datatable",
            dataset_name=ORIGINAL_DATASET,
            data_editor=de
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

## Using AG Grid

As a preliminary step, make sure to run `pip install dash-ag-grid`.

Replace the `create_data_table` function with the following:

```python
import dash_ag_grid as dag

def create_data_table(id, dataset_name, data_editor):
    df = data_editor.get_edited_df()
    return dag.AgGrid(
        id=id,
        rowData=df.to_dict("records"),
        columnDefs=[{"field": i} for i in df.columns],
        defaultColDef={"editable": True, "resizable": True, "sortable": True, "filter": True},
        columnSize="sizeToFit",
        getRowId="params.data.index",
        dashGridOptions={"domLayout": "autoHeight"}
    )
```

## Deeper customizations

See the [dash_tabulator documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dash_tabulator/README.md) and the [Plugin Developer Documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dss-plugin-visual-edit/README.md) for more ways to customize the webapp.
