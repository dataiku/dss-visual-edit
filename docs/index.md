# Plugin: Data Editing | Dataiku

**Interfaces for “human in the loop” analytics & AI**

<iframe src="https://www.loom.com/embed/7b79e45e755544f8baf1ff3ed1bf60ee" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

[Book a demo](https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1cgQ-IQ2k2eJMm6mUrZxabQgtPSSwaZ9TgNcHcnaUDvrqfweAkf-B7xzZbTSNyYeSRc2smgLbp){: .btn}

## Use cases

* **Entity Resolution** (aka record linkage): review and correct fuzzy matches between 2 or more datasets representing the same entities (e.g. customers, suppliers, products) but with differing IDs and names. [Demo project →](sample-project-company-resolution)
* **AI Validation and Improvement**: continuously provide feedback on AI outputs in production, and ingest back into the AI's training data. [Demo project →](sample-project-ai-feedback-app)
* **Forecast Override**: machine-made forecasts (e.g. sales) need to be adjusted by a human, to take into account contextual information that wasn't available to the machine, or to correct low-confidence predictions.
* **Business rules exception handling**: fill in missing values or override values in the output of business rules.
* **Data correctioning**.

## Features

* **Visual Webapp (no-code setup)** with a feature-rich data table:
  * **Rich editing experience**:
    * **Airtable-like editing of linked records** (aka foreign keys) via dropdown, with the ability to **search and display lookup columns** from a linked dataset of any size.
    * Boolean cells are edited via a checkbox.
    * Datetime cells are edited via a date picker.
  * **Automatic input validation**: Formatting and editing adapts to the detected data types (e.g. numerical cells don’t allow characters; linked records restrict selection to entries in a linked dataset).
  * Filtering, sorting and grouping of data.
  * Pagination of large datasets.
  * **Automatic detection of changes** in the source dataset.
* **Continuous update mechanisms**: seamless integration of new source data into the webapp and of new edits into production data pipelines.
* **Governance**: built-in audit trail of all edits made by end-users.
* **CRUD Python API** for coders building custom webapps. It is the same API that provides the Visual Webapp's data persistence layer.

## How tos

* [Install](install-plugin) (Dataiku v9 and above)
* [No-code] [Get started: Visual Webapp](get-started): Setup, overview of plugin components and key concepts
* [Low-code] [Get started: CRUD Python API](get-started-crud-python-api): Overview of methods to read/write individual or multiple rows of data
* [Use edits in the Flow](using-edits): Where to find edits & How to leverage for analytics & AI
* [Go further](going-further): Reset edits on a design node, Deploy to production (automation node), Implement feedback loops, FAQ
