# Plugin: Data Editing | Dataiku

No-code webapps for “human in the loop” analytics & AI.

<iframe src="https://www.loom.com/embed/7b79e45e755544f8baf1ff3ed1bf60ee" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

[Book a demo](https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1cgQ-IQ2k2eJMm6mUrZxabQgtPSSwaZ9TgNcHcnaUDvrqfweAkf-B7xzZbTSNyYeSRc2smgLbp){: .btn}

Check out our library of [demo videos](https://loom.com/share/folder/b5e96d5672da4a58883b3b05a35445fa): webapp setup, integrating edits into the Flow, feedback loops, usage in Design vs Automation.

## Use cases

* **Entity reconciliation**: 2 or more datasets represent the same entities and need to be merged. However, common properties of a given entity may have different values from one dataset to the other (e.g. entity name). See our ["company reconciliation" sample project](sample-project-company-reconciliation) where we manually review and correct automated matches between company entities. This can be adapted to the case where entities are customers, suppliers, or even products, whose names differ from one data source to the other.
* **Forecast override**: machine-made sales forecasts need to be adjusted by a human, to take into account contextual information that wasn't available to the machine, or to correct low-confidence predictions.
* **AI feedback loop**: human feedback on AI-powered predictions is ingested back into the AI's training data.
* **Business rules exception handling**: manually filling in missing values in the output of classification rules.
* **Data correctioning**.

## Features

* **Visual Webapp (no-code setup)** with a feature-rich data table:
  * **Rich editing experience**:
    * Boolean cells are edited via a checkbox.
    * Datetime cells are edited via a date picker.
    * **Linked records (aka foreign keys)** are edited via a dropdown, with the ability to **search and display lookup columns** from the linked dataset.
  * **Automatic input validation**: Formatting and editing adapts to the detected data types (e.g. numerical cells don’t allow characters; linked records restrict selection to entries in a linked dataset).
  * Filtering, sorting and grouping of data.
  * Pagination of large datasets.
  * **Automatic detection of changes** in the source dataset.
* **Continuous update mechanisms**: seamless integration of new source data into the webapp and of new edits into production data pipelines.
* **Governance**: built-in audit trail of all edits made by end-users.
* **CRUD Python API** for coders building custom webapps. It is the same API that provides the Visual Webapp's data persistence layer.

## Contents

* [Installation](install-plugin): Dataiku v9 and above
* [Getting started: Visual Webapp](get-started): Overview of plugin components and key concepts
* [Getting started: CRUD Python API](get-started-crud-python-api): Overview of methods to read/write individual or multiple rows of data
* [Going further](going-further): Deployment, FAQ
* [Sample project: Company Reconciliation](sample-project-company-reconciliation)
* [Sample project: AI Feedback App](sample-project-ai-feedback-app)
