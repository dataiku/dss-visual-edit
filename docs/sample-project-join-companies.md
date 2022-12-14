# Sample project: Join Companies

How to use this sample project:

* Build dataset `companies_joined_prepared_edited` (recursive build)
* Go to Webapps and start "Edit Matches Uncertain"
* Go to Dashboards and to "Company Matches"
  * Make some edits
  * Click on the Update button, which will trigger the Update scenario
    * This runs the Python recipe that produces
* Use the Init scenario to reset all edits

This project demonstrates a case of feedback loop, where the data to review/edit in the webapp depends on previous edits. This data is in dataset `matches_uncertain` and edits can be found in `matches_uncertain_editlog_pivoted`. The Python recipe which produces `matches_uncertain` is ran as part of the Update scenario; it feeds from `matches` and from `matches_uncertain_editlog_pivoted` — see its code in the standard code editor or in a notebook, in particular the section named "Apply edits to matches with distance > 0 or undefined".
