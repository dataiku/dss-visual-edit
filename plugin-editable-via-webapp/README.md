# README

What the backend creates:

1. a copy of the input dataset, named INPUT_editable
2. a dataset that stores the list of changes made by the webapp user, named INPUT_changes
3. a recipe that links INPUT and INPUT_changes to INPUT_editable and allows to replay changes

## Settings: schema

To be read by the webapp, in JSON format. Similar in spirit to the settings of a visual webapp as they are stored in a Dataiku project (see JSON file in a Dataiku's project's "web_apps" directory).

Here, the settings are mostly about the schema. Common fields:

* name: name of the field, as it appears in the editable table
* type: type of the field (identical to a type in a dataset schema)
* editable: boolean that defines whether field should be editable or not (currently not enforced in the webapp)
* editable_type: None or "key" (for primary key) or "linked_record" or "lookup_column"

Fields for a linked record:

* linked_ds_name: name of the dataset that is linked to the field
* linked_ds_key: primary key for the linked dataset

Fields for a lookup column:

* linked_record_col: name of the editable's column that defines the corresponding linked record
* linked_ds_column_name: name of the lookup column in the linked dataset

## Data table component: Dash Tabulator

Based on [dash_tabulator](https://github.com/preftech/dash-tabulator) (Python) which is a Dash component based on [react-tabulator](https://github.com/ngduc/react-tabulator) (JavaScript) which is based on [Tabulator](http://tabulator.info).

Latest version of dash_tabulator is 0.4.2 which uses react-tabulator 0.14.2 which uses Tabulator 4.8, but latest version of Tabulator is 5.2.

See how to build from source at:
https://github.com/preftech/dash-tabulator/blob/207ae1ff6f683471cb0a02247ddff32860400210/RELEASE.md

## TODO:

* Show info on what is going to be created (change log dataset with name INPUT_DATASET_NAME_changes, editable dataset with name INPUT_DATASET_NAME_editable, recipe)
