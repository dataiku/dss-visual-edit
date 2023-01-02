# Sample project: Join Companies

This project demonstrates a case of feedback loop, where the data to review/edit in the webapp depends on previous edits. This data is in dataset `matches_uncertain` and edits can be found in `matches_uncertain_editlog_pivoted`. The Python recipe which produces `matches_uncertain` feeds from `matches` and from `matches_uncertain_editlog_pivoted` — see its code in the standard recipe code editor or in a notebook, in particular the section named "Apply edits to matches with distance > 0 or undefined".

[Download project bundle](dss-bundle-JOIN_COMPANIES_SIMPLE-webapp-based.zip). Note: the project uses the Managed Snowflake data connection provided on Dataiku Online — you may have to remap to one of your own data connections.

How to use this sample project:

* Build dataset `companies_joined_prepared_edited` (recursive build)
* Go to Webapps and start "Edit Matches Uncertain"
* Go to Dashboards and to "Company Matches"
  * Make some edits
  * Click on the Update button, which will trigger the Update scenario
* Use the Init scenario to reset all edits

## Making of

### Initial flow

* We started with a Fuzzy Join between `companies_ref` and `companies_ext` based on `id`, and specified that we wanted to output matching details.
* We needed additional colums to store reviewing information, such as the approval of a match (boolean) and comments (string). These were created as empty columns in a Prepare recipe. We also extracted the distance information found in the `meta` column of the Fuzzy Join output (where matching details are stored).
* We added a Group recipe to deal with cases where several matches were found in `companies_ext` for the same company in `companies_ref`, and only keep the closest match.
* We created a `corrections` folder that could hold data uploaded as CSV files. For testing purposes, we uploaded a tiny file containing:

```csv
id_companies_ref,id_companies_ext,reviewed
208628,XB40,True
114233,MEIZ,True
```

* We used the plugin's Merge recipe with `matches` and `corrected_data` as inputs, and created `matches_edited`. This required to set the “primary_keys” custom field of `matches`, so that the Merge recipe knows how to join its inputs.
* We added a `to_be_reviewed` column computed by a Prepare recipe, and used it to Split `matches_edited` into two datasets, for certain and uncertain matches.
* Finally, a 3-way join between the `companies_ref`, `companies_ext` and `matches_certain`, produces the output we were looking for: a dataset of companies that has both the `notes` and `fte_count` columns.

### Reviewing and updating

Reviewing could be made in a spreadsheet program. It involves:

* Downloading `matches_uncertain`
* Making changes and saving them to a new CSV file
* Uploading this file to `corrections`
* Rebuilding `matches_uncertain`.

### Usage of the plugin's Visual Webapp component

* Set up the webapp:
  * Create new Visual Webapp and edit its settings:
    * The dataset to edit is `matches_uncertain`.
    * `id_companies_ext` is an editable column and is set to be a "linked record" (linking to the `id` column of `companies_ext`). It contains values set from the Fuzzy Join but also missing values (when no match was found).
    * There are 2 more editable columns: `approved` and `comments` (that we created as placeholders for reviewing information). Initially, all values are empty.
* Start webapp. This creates the editlog and editlog_pivoted datasets.
* Adapt the flow: use `matches_uncertain_editlog_pivoted` as replacement of `corrected_data`.
* Use webapp.
* Implement update mechanism:
  * Preliminary remarks:
    * The webapp uses the same code as the Merge edits recipe that we have in our flow, except that it uses `matches_uncertain` instead of `matches`. Also, it uses a "live" version of the editlog pivoted, instead of the dataset found in the flow and computed from the editlog.
    * Marking a match as approved doesn't automatically move it from `matches_uncertain` to `matches_certain`. We need to rebuild these datasets. For this, we need to make sure that the editlog_pivoted dataset has been rebuilt.
  * Steps:
    * Create an Update scenario with a force-rebuild of `matches_uncertain_editlog_pivoted` and a rebuild of `matches_uncertain`.
    * Create a dashboard which embeds the webapp and has a button to run that scenario.
