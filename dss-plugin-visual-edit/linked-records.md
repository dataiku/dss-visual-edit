# Developer guide — Linked Records implementation

## Quick recap

We're implementing dropdown editing that supports:

- search over hundreds of thousands of options (server-side filtering and paging)
- rich formatting of dropdown items (label displayed in bold, additional lookup values shown beneath the label).

This document targets maintainers who need to understand and modify how Linked Record columns are implemented in the Visual Edit plugin. It assumes the user-facing behaviour is already documented in `docs/linked-records.md`.

### Contents

- High-level flow
- Key modules and functions
- Data shapes and contracts
- Server-side filtering and paging
- Display label formatting and lookup columns
- Extension points and common changes

## High-level flow

### Configuration

Linked-record mappings are declared in the webapp configuration (`webapp/config/models/EditSchema.LinkedRecord` entries loaded by the webapp). Each mapping identifies the source column, the linked dataset, the key column, optional label and lookup columns.

### Frontend interaction

When a cell with a Linked Record is edited, the frontend requests options from the backend via an API call (either the full list for small datasets or a filtered slice when a search term is provided).

### Backend resolution

The backend calls helpers in `python-lib/linked_df_utils.py` to fetch, filter and format rows from the linked dataset and return JSON to the frontend.

## Key modules and functions

### Where to look in the codebase

- `python-lib/linked_df_utils.py` — core logic for fetching and formatting options
- `webapps/visual-edit/backend.py` — web routes that glue the web UI to the utils
- `python-lib/DataEditor.py` — higher-level editing flow where values are validated against linked records when edits are applied
- `python-lib/TabulatorColumnAdapter.py` — Tabulator column formatting and the `get_linked_record_configuration` function that configures dropdowns, remote lookup calls and item formatting.

### `python-lib/linked_df_utils.py`

Core helpers:

- `get_linked_dataframe_filtered(linked_record, project_key, filter_term, n_results)`

 Fetches a filtered `pandas.DataFrame` from the linked dataset. Handles both DSS-managed dataset objects and dataset references. Accepts `filter_term` (string) and `n_results` (int) to limit results; delegates to `dataiku_utils.get_dataframe_filtered` when available for server-side filtering.

- `get_linked_options(linked_record, term, key)`

 Top-level helper that returns a list of formatted option dictionaries for the frontend. Applies prefix filtering and caps the number of returned options.

- `get_linked_label(linked_record, key)`

 Given a key value, returns the label used for display (or the key if no label column is configured).

- `get_formatted_items_from_linked_df(linked_df, key_col, label_col, lookup_cols=None)`

 Converts a `DataFrame` into the frontend option format: each item contains `value`, `label` and optional `lookup` data.

### `webapps/visual-edit/backend.py`

Entry points and HTTP routes. Routes that serve linked-record options and resolve labels call into the utils module; search for handlers that call `get_linked_options` and `get_linked_label`.

### `python-lib/DataEditor.py`

- Where linked-record mappings are materialised: DataEditor is responsible for loading the LinkedRecord configuration into an internal structure (e.g. de.linked_records_df) that other components consult.
- Loading linked datasets: DataEditor decides when to load small linked datasets into DataFrames versus holding references to larger datasets as DatasetSQL objects, and holds references used by UI adapters (Tabulator) to look up ds_name/ds_key/ds_label/ds_lookup_columns.
- Integration points: adapters (TabulatorColumnAdapter) read de.linked_records_df to build editors/formatters.

### `python-lib/TabulatorColumnAdapter.py`

Frontend formatter/editor glue for Tabulator. The function `get_linked_record_configuration` builds the Tabulator formatter and editor settings for linked-record columns by specifying:

- Labels retrieval from backend endpoint: the data table's cell formatter for Linked Record columns is to call `/linked-label/linked_ds_name/` with `key` query parameter (current value of the cell) to fetch the corresponding display label.
- Options retrieval from backend endpoint: the data table's cell editor is to call `/linked-options/linked_ds_name/` with `search_term` and `key` query parameters to fetch options as the user types.
- Rich formatting of the dropdown's items when lookup columns are present, leveraging `dash_tabulator`'s `listItemRichFormatter` feature.

#### Tabulator-specific vs generalizable logic

- General / portable logic
  - Backend endpoints and helpers: get_linked_options, get_linked_label, get_linked_dataframe_filtered, and associated JSON option shape (value/label/lookup).
  - Server-side filtering, paging and performance considerations (n_results cap, SQL indexing, dataiku_utils.get_dataframe_filtered).
  - Data contracts: LinkedRecord config and the option item format consumed by the frontend.
  - Formatting rules implemented in python (how labels and lookup objects are composed) — these can be reused by any frontend renderer.

- Tabulator-specific
  - Use of assign(...) and Namespace(...) to inline JavaScript functions and reference JS helpers provided by `dash_tabulator` (e.g. listItemRichFormatter).
  - editorParams shape and keys (valuesLookup, itemFormatter, filterRemote, placeholderLoading, etc.) which rely on Tabulator/dash_tabulator runtime behaviour.
  - Synchronous $.ajax usage in the current formatter/editor JS snippets (tied to how the Tabulator config expects values).

- Porting notes (example: AgGrid)
  - Replace Tabulator-specific editorParams with AgGrid cellEditor/cellRenderer equivalents. Map:
    - valuesLookup -> asynchronous value provider for the editor.
    - itemFormatter -> cellRenderer that supports rich HTML for items.
    - filterRemote -> implement server-side filtering via the editor's async query callbacks.
  - Avoid synchronous XHR in renderers; use promises/async callbacks the target grid supports (AgGrid provides async cell editors/renderers).
  - Reuse backend endpoints (linked-options/linked-label) unchanged; adapt the frontend calls and payload naming (e.g. search_term vs filterTerm) to the grid's editor API.
  - Implement client-side glue to convert the backend option item shape into whatever the grid's editor expects (simple array of {value,label} or richer objects).

## Data shapes and contracts

- LinkedRecord config (`LinkedRecord`): an object with at least `column` (source column name), `ds` (linked dataset reference or null), `ds_key` (key column name), `ds_label` (label column name, optional), and `lookup_cols` (array of extra columns to include).

- Frontend option item (JSON):

  - `value`: the key (what gets stored back to the edited dataset)
  - `label`: the string shown in the dropdown
  - `lookup`: optional object with additional columns for display

## Server-side filtering and paging

- For large linked datasets the backend returns only a slice of matching rows. Filtering is a prefix match against the label or key column (see `get_linked_dataframe_filtered`).

- `n_results` caps the returned items (UI defaults to a small number, typically 10). If you change this cap, update both frontend and `get_linked_options`.

- Performance considerations:

  - For SQL-backed datasets, add an index on the column used to filter (label or key) to speed up prefix queries.
  - Avoid loading the full linked dataset when only a small page is required; `dataiku_utils.get_dataframe_filtered` supports server-side filtering when the dataset is a managed SQL dataset.

## Display label formatting and lookup columns

- The code uses `ds_label` if present and different from `ds_key`. If a label is not configured, the key is used as the label.

- `get_formatted_items_from_linked_df` builds a concise `label` string and a `lookup` object containing requested columns. If richer rendering is required (HTML/JS), update both the formatter and the frontend renderer.

## Extension points and common changes

- Change filter behaviour (e.g. substring instead of prefix):

  - Update `get_linked_dataframe_filtered` to change the predicate used for `filter_term`.
  - Update `get_linked_options` to ensure returned items still match the frontend contract.

- Increase result cap or add pagination controls:

  - Increase `n_results` usage in both backend and frontend.
  - Consider adding a `cursor` parameter for deeper pages and returning a `has_more` flag.

- Add caching for performance:

  - For stable Linked Datasets, add a short-lived LRU cache keyed by `(ds_ref, filter_term)`.
  - Cache formatted option lists instead of entire DataFrames to limit memory use.

### Tests and debugging

- Unit tests should mock `dataiku_utils.get_dataframe_filtered` and assert that `get_linked_options` returns the expected JSON for various dataset sizes and filter terms.

- To reproduce issues locally, run the webapp outside DSS (`backend.py` supports local launch) and hit the linked-record endpoints with `curl` while monitoring logs.
