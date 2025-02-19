# FAQ

## Can I use Visual Edit if my data is on connection X?

Visual Edit can load your original data regardless of the underlying connection. When using it for the first time, the editlog, edits, and edited datasets will be created on the same connection.

We strongly recommend using an SQL connection for the editlog, as explained in the [deployment guide](deploy). The edits and edited datasets can be on a different connection.

If [linked records](linked-records) are needed, and if the linked dataset has more than 10,000 rows or if lookup columns are needed, then the linked dataset must also be on an SQL connection.

## Can the webapp be used by several users simultaneously?

Several users can view and edit data at the same time, but they won't see each other's edits in real time; if two or more users try to edit the same cell at the same time, all their edits will be logged, but only the last edit will make its way to the _edits_ dataset.

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
