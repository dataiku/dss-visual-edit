# Getting started: CRUD Python API | Plugin: Visual Edit | Dataiku

<iframe src="https://www.loom.com/embed/3d899ce5f7544850abe91d088b969331" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

As an alternative to using the Visual Edit Webapp, you can build a custom webapp that uses the CRUD (Create, Read, Update, Delete) methods provided by the `DataEditor` Python class.

Let's take a quick tour of how to use this. We strongly recommend following the [Visual Webapp guide](get-started) first, to get an initial understanding of the plugin's features and concepts.

## Requirement: code environment

When running the code below in a notebook or a webapp in Dataiku, a code environment must be specified. A code environment was created upon installation of the plugin, but it can't be selected from the list of available code environments as it can only be used by the plugin's visual components (Visual Webapp and Recipes). You'll need to create a new code environment and to make sure it contains the same packages as the plugin's.

## Instantiate the `DataEditor` class

```python
import dataiku
dataiku.use_plugin_libs("visual-edit")
DataEditor = dataiku.import_from_plugin("visual-edit", "DataEditor")
```

```python
de = DataEditor.DataEditor(
    original_ds_name="my_dataset",
    primary_keys=["id"],
    editable_column_names=["existing_editable_col", "new_editable_col"]
)
```

`editable_column_names` can contain names of columns found in the original dataset, and names of new columns that don't exist yet.

## Perform CRUD operations

Here we provide an overview of available methods.

More information on the parameters can be found in the [docstrings](backend/).

### Read data

At row level:

* `get_row(primary_keys)` — read a row that was created, updated or deleted; params: dictionary containing primary key(s) value(s) of the row to read.

At dataset level:

* `get_original_df()` — original data (all rows) without edits
* `get_edited_df()` — original data (all rows) with edited values
* `get_edited_cells_df()` — only rows and columns that were edited
* `get_editlog_df()`

These methods return Pandas dataframes.

### Write data

At row level:

* `create_row(primary_keys, column_values)` - create a new row; params: dictionary containing primary key(s) value(s) of the row to create, dictionary containing values for all other columns.
* `update_row(primary_keys, column, value)` - update any row; params: primary key(s) value(s) of the row to update, name of column to update, new value.
* `delete_row(primary_keys)` - deleted any row, params: primary key(s) value(s) of the row to delete.

Note on the attribution of edits in the editlog: when these methods are called in the context of an active HTTP request (e.g. in a Flask or Dash app), the identifier of the user logged into Dataiku (e.g. their email address) is retrieved from the request headers sent by their web browser. Otherwise, the identifier is set to "unknown".

At dataset level:

* `empty_editlog()`: delete all rows of the editlog (use with caution)

## Example usage in Dash

### Simple example

This example is based on the tshirt orders dataset from the [Basics 101 course](https://academy.dataiku.com/basics-101).

Import `DataEditor` as shown previously, then use it in the Dash app code:

```python
from dash import html, Input, Output

# Define the data and columns to use in the data table component
###

ORIGINAL_DATASET = "orders"
PRIMARY_KEYS = ["order_id"]
EDITABLE_COLUMN_NAMES = ["tshirt_price", "tshirt_quantity"]

de = DataEditor.DataEditor(
    original_ds_name=ORIGINAL_DATASET,
    primary_keys=PRIMARY_KEYS,
    editable_column_names=EDITABLE_COLUMN_NAMES,
)

tabulator_utils = dataiku.import_from_plugin("visual-edit", "tabulator_utils")
tabulator_utils = dataiku.import_from_plugin("visual-edit", "tabulator_utils")
columns = tabulator_utils.get_columns_tabulator(ees)

# Define Dash layout and callbacks
###

dash_tabulator = dataiku.import_from_plugin("visual-edit", "dash_tabulator")
dash_tabulator = dataiku.import_from_plugin("visual-edit", "dash_tabulator")

def serve_layout():
    return html.Div([
        dash_tabulator.DashTabulator(
            id="quickstart-datatable",
            datasetName=ORIGINAL_DATASET,
            data=ees.get_edited_df().to_dict("records"),
            columns=columns
        ),
        html.Div(id="quickstart-output")
    ])

app.layout = serve_layout

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
    return ees.update_row(cell["row"], cell["field"], cell["value"])
```

### Example with advanced Tabulator features

In this example we define a calculated column using the Tabulator `mutator` feature and a JavaScript function that implements the calculation to perform (here: adding 2 to the values of the `tshirt_quantity` column).

We also demonstrate usage of Tabulator's `headerFilter` and `sorter` features.

In the above code example, replace the definition of `columns` with the following:

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

## Behind the scenes

The implementation of these methods is based on the [Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing): instead of directly storing the current state of the edited data, we use an append-only store to record the full series of actions on that data. This store is a dataset that we call the "editlog".

When the `DataEditor` class is instantiated on a given dataset, it creates an "editlog" dataset and 2 recipes that create an "editlog pivoted" and an "edited" dataset (if they don't already exist). Those datasets are created on the same connection as the original dataset.

Edits made via CRUD methods instantly add rows to the editlog. The editlog pivoted and the edited datasets are only updated when the recipes that build them are run.
