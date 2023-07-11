# Plugin: Data Editing | Dataiku

## Interfaces for human-in-the-loop analytics and AI

Dataiku Visual Webapp and Python CRUD API to write manually-entered data back to the Flow.

<iframe src="https://www.loom.com/embed/7b79e45e755544f8baf1ff3ed1bf60ee" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

[Book a demo!](https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1cgQ-IQ2k2eJMm6mUrZxabQgtPSSwaZ9TgNcHcnaUDvrqfweAkf-B7xzZbTSNyYeSRc2smgLbp){: .btn}

## Use cases

* **Entity Resolution** (aka record linkage): review and correct fuzzy matches between 2 or more datasets representing the same entities (e.g. customers, suppliers, products) but with differing IDs and names. [Demo project →](sample-project-company-resolution)
* **AI Validation and Improvement**: continuously provide feedback on AI outputs in production, and ingest back into the AI's training data. [Demo project →](sample-project-ai-feedback-app)
* **Forecast Override**: machine-made forecasts (e.g. sales) need to be adjusted by a human, to take into account contextual information that wasn't available to the machine, or to correct low-confidence predictions.
* **Business rules exception handling**: fill in missing values or override values in the output of business rules.
* **Data correctioning**.

## Features

* **Visual Webapp (no-code setup)** with a feature-rich data table:
  * **Rich editing experience**:
    * **Automatic input validation**: Formatting and editing adapts to the detected data types:
      * numerical cells don’t allow characters
      * boolean cells are edited via a checkbox
      * date cells are edited via a date picker
      * linked records restrict selection to entries in a linked dataset.
    * **Airtable-like editing of linked records** (aka foreign keys) via dropdown, with the ability to **search and display lookup columns** in real time, from a linked dataset of any size.
  * **Powerful data browsing**:
    * **Filtering, sorting and grouping** in real time.
    * Re-ordering, re-sizing and hiding columns, so you can focus on content that's import to you.
    * Pagination of large datasets.
  * **Automatic detection of changes** in the source dataset.
* **Continuous update mechanisms**: seamless integration of new source data into the webapp and of new edits into production data pipelines.
* **Dataset of edited rows**: this can serve as input to a recipe that writes back to a source system, or for the implementation of a feedback loop (e.g. stacking with an AI training dataset).
* **Governance**: built-in audit trail of all edits made by end-users.
* **[API for row-level CRUD on intermediate datasets]((get-started-crud-python-api))** for coders building custom webapps. It is the same API that provides the Visual Webapp's data persistence layer.

## How tos

* [Install](install-plugin) (Dataiku v9 and above)
* [No-code] [Get started: Visual Webapp](get-started): Setup, overview of plugin components and key concepts
* [Low-code] [Get started: CRUD Python API](get-started-crud-python-api): Overview of methods to read/write individual or multiple rows of data
* [Use edits in the Flow](using-edits): Where to find edits & How to leverage for analytics & AI
* [Go further](going-further): Reset edits on a design node, Deploy to production (automation node), Implement feedback loops, FAQ
