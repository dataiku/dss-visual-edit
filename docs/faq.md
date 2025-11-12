# FAQ

## Can I use Visual Edit if my data is on connection X?

Visual Edit can load your original data regardless of the underlying connection. When using it for the first time, the `editlog`, `edits`, and `edited` datasets will be created on the same connection.

We strongly recommend using a [compatible SQL connection](compatibility) for the `editlog`, as motivated in the [deployment guide](deploy). The `edits` and `edited` datasets can be on a different connection.

If [linked records](linked-records) are needed, and if the linked dataset has more than 10,000 rows or if lookup columns are needed, then the linked dataset must also be on an SQL connection.

## Can the webapp be used by several end-users simultaneously?

From a technical standpoint, **yes**: multiple end-users can view and edit data simultaneously. **However, they won't see each other's edits in real-time**. More specifically, if two or more end-users try to edit the same cell at the same time:

* All edits will be recorded in the editlog.
* Only the last edit will be taken into account.
* End-users won't know that they're all editing the same cell simultaneously.
* The only way to figure out that this happened, and who "won", is to look at the editlog.

We recommend assessing the likelihood of simultaneous editing by considering the number of end-users, how often each is expected to use the webapp per day, and for how long.

To address the above user experience issues, we recommend **assigning ownership of each row to a specific end-user**. This can be done by creating an extra column in the dataset to review/edit whose values are user names. This column can then be used in two ways:

* In the webapp: have end-users filter for their name in that column.
* In the flow: split the dataset according to that column, create one Visual Edit webapp per resulting dataset, and specify the corresponding user in the webapp's "authorized users" setting.

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
