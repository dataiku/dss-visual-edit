# README

What the backend creates:

1. a copy of the input dataset, named INPUT_editable
2. a dataset that stores the list of changes made by the webapp user, named INPUT_changes
3. a recipe that links INPUT and INPUT_changes to INPUT_editable and allows to replay changes


## Settings

Common fields:

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

## TODO:

* Update recipe when unique key is changed via webapp settings
* Unique key can be changed via recipe settings? What happens if so?
* Show info on what is going to be created (change log dataset with name INPUT_DATASET_NAME_changes, editable dataset with name INPUT_DATASET_NAME_editable, recipe)
* Configure connection for change log dataset?
