# Plugin: Data Editing | Dataiku

No-code webapps for “human in the loop” analytics & AI.

<iframe src="https://www.loom.com/embed/7b79e45e755544f8baf1ff3ed1bf60ee" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

[Book a demo](https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1cgQ-IQ2k2eJMm6mUrZxabQgtPSSwaZ9TgNcHcnaUDvrqfweAkf-B7xzZbTSNyYeSRc2smgLbp){: .btn}

Check out our library of [demo videos](https://loom.com/share/folder/b5e96d5672da4a58883b3b05a35445fa): webapp setup, integrating edits into the Flow, feedback loops, usage in Design vs Automation.

## Use cases

* **Entity reconciliation**: 2 or more datasets represent the same entities and need to be merged. However, common properties of a given entity may have different values from one dataset to the other. See our ["company reconciliation" sample project](sample-project-company-reconciliation) where we manually review and correct matches between company entities whose names differ.
* **Forecast override**: machine-made sales forecasts need to be adjusted by a human, to take into account contextual information that wasn't available to the machine, or to correct low-confidence predictions.
* **AI feedback loop**: human feedback on AI-powered predictions is ingested back into the AI's training data.
* **Business rules exception handling**: manually filling in missing values in the output of classification rules.
* **Data correctioning**.

## Features

* Feature-rich data table with editable columns:
  * Filter, sort and group data
  * Formatters and editors for different data types (boolean, numerical, textual, date)
  * Support for linked records (aka foreign keys) and lookup columns.
* Continuous update mechanisms: seamless integration of new source data into the webapp and of new edits into production data pipelines.
* Governance: audit trail of all edits made by end-users.

## Contents

* [Installation](install-plugin): Dataiku v9 and above
* [Getting started](get-started): Overview of plugin components and key concepts
* [Going further](going-further): Deployment, FAQ
* [Sample project: Company Reconciliation](sample-project-company-reconciliation)
* [Sample project: AI Feedback App](sample-project-ai-feedback-app)
