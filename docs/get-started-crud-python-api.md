# Getting started: CRUD Python API | Plugin: Data Editing | Dataiku

<iframe src="https://www.loom.com/embed/3d899ce5f7544850abe91d088b969331" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

As an alternative to using the Data Editing Visual Webapp, you can build a custom webapp that uses the CRUD (Create, Read, Update, Delete) methods provided by the `EditableEventSourced` Python class.

Let's take a quick tour of how to use this. If you haven't, [install the plugin](install-plugin) first.

## Instantiate the `EditableEventSourced` class

```python
import dataiku
dataiku.use_plugin_libs("editable-via-webapp")
EditableEventSourced = dataiku.import_from_plugin("editable-via-webapp", "EditableEventSourced")

ees = EditableEventSourced.EditableEventSourced(
    original_ds_name="my_dataset",
    primary_keys=["id"],
    editable_column_names=["existing_editable_col", "new_editable_col"]
)
```

`editable_column_names` can contain names of columns found in the original dataset, and names of new columns as well.

## Perform CRUD operations

Here we provide an overview of available methods — more information can be found in the docstrings in the code.

### Read data

At row level:

* `get_row` — read a row that was created, updated or deleted; params: dictionary containing primary key(s) value(s) of the row to read.

At dataset level:

* `get_original_df` — original data (all rows) without edits
* `get_edited_df` — original data (all rows) with edited values
* `get_edited_cells_df` — only rows and columns that were edited
* `get_editlog_df`

These methods return Pandas dataframes.

### Write data

At row level:

* `create_row` - create a new row; params: dictionary containing primary key(s) value(s) of the row to create, dictionary containing values for all other columns.
* `update_row` - update any row; params: primary key(s) value(s) of the row to update, name of column to update, new value.
* `delete_row` - deleted any row, params: primary key(s) value(s) of the row to delete.

Note on the attribution of edits in the editlog: when these methods are called in the context of an active HTTP request (e.g. in a Flask or Dash app), the identifier of the user logged into Dataiku (e.g. their email address) is retrieved from the request headers sent by their web browser. Otherwise, the identifier is set to "unknown".

At dataset level:

* `empty_editlog`: delete all rows of the editlog (use with caution)

## Behind the scenes

The implementation of these methods is based on the [Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing): instead of directly storing the current state of the edited data, we use an append-only store to record the full series of actions on that data. This store is a dataset that we call the "editlog".

When the `EditableEventSourced` class is instantiated on a given dataset, it creates an "editlog" dataset and 2 recipes that create an "editlog pivoted" and an "edited" dataset (if they don't already exist). Those datasets are created on the same connection as the original dataset.

Edits made via CRUD methods instantly add rows to the editlog. The editlog pivoted and the edited datasets are only updated when the recipes that build them are run.

## Next

* [Using edits in the Flow](using-edits): Where to find edits and how to leverage them for analytics
