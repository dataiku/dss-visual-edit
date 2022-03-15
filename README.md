# README

What the backend creates:

1. a copy of the input dataset, named INPUT_editable
2. a dataset that stores the list of changes made by the webapp user, named INPUT_changes
3. a recipe that links INPUT and INPUT_changes to INPUT_editable and allows to replay changes

## TODO:

* What happens to the change log when a row has been edited and gets edited again?
* Configure connection for change log dataset?
* Update recipe when unique key is changed via webapp settings
* Unique key can be changed via recipe settings? What happens if so?