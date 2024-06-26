# FAQ

## Can the webapp be used by several users at the same time?

Several users can view and edit data at the same time, but they won't see each other's edits in real-time; if 2 or more users try to edit the same cell at the same time, all their edits will be logged but only the last edit will make its way to the _edits_ dataset.

## What happens if I change primary keys or editable columns in the webapp settings?

* Primary key:
  * Add:
    * If this primary key had already been in use in the past (and you're adding it back), there may be rows in the editlog that contain a value for this key, and these rows will be taken into account.
    * Otherwise, previous edits won't be taken into account by the webapp / the recipes.
  * Remove:
    * If the remaining keys allow to uniquely identify a row in the dataset, then there is no impact.
    * Otherwise, many rows could be impacted by a single row of the editlog (instead of a single row).
* Editable column:
  * Add: no impact.
  * Remove: previous edits on this column won't be taken into account by the webapp / the recipes, and they won't appear in _edits_ (but they will still be in the editlog).

