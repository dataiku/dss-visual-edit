# Data table features

## Rich editing experience

* **Automatic input validation**: Formatting and editing adapt to the detected data types:
  * Numerical cells don’t allow characters
  * Boolean cells are edited via a checkbox
  * Date cells are edited via a date picker
  * Linked records restrict selection to entries in a linked dataset.
* **Airtable-like editing of linked records** (aka foreign keys) via dropdown, with the ability to **search and display lookup columns** in real time, from a linked dataset of any size.

## Powerful data browsing

* **Filtering, sorting and grouping** in real time.
* Re-ordering, re-sizing and hiding columns, so you can focus on content that's important to you.
* Pagination of large datasets.
* **Automatic detection of changes** in the source dataset.

## How to use these features

* Right-clicking on the column name will show a menu with an option to hide the column, and an option to group rows by value.
* Filtering:
  * The default filter is a textual one.
  * In the case of a display-only boolean column, the filter is a tri-state checkbox (or a simple toggle if you specified the column type to be "boolean_tick" via the advanced settings ([editschema](editschema)).
  * Editable boolean columns have a textual filter that you can use by typing "true" or "false".
* All of this can be reset by clicking on the "Reset View" button in the bottom-left corner.
* Linked records are edited via dropdowns which include the ability to search through all options: when there are many of them, only options that start with the search term are presented.
* Changes in the original dataset are automatically detected and signaled. The user needs to refresh the webpage in order to see them.