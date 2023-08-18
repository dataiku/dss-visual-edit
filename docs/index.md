# Plugin: Data Editing | Dataiku

## Build apps that write manually-entered data back to the Flow

<iframe src="https://www.loom.com/embed/7b79e45e755544f8baf1ff3ed1bf60ee" frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

[Book a demo!](https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1cgQ-IQ2k2eJMm6mUrZxabQgtPSSwaZ9TgNcHcnaUDvrqfweAkf-B7xzZbTSNyYeSRc2smgLbp){: .btn}

## Use cases

* Human-in-the-loop analytics and AI:
  * **Entity Resolution** (aka record linkage): review and correct fuzzy matches between 2 or more datasets representing the same entities (e.g. customers, suppliers, products) but with differing IDs and names. [Demo project →](sample-project-company-resolution)
  * **AI Validation and Improvement**: continuously provide feedback on AI outputs in production, and ingest back into the AI's training data. [Demo project →](sample-project-ai-feedback-app)
  * **Forecast Override**: machine-made forecasts (e.g. sales) need to be adjusted by a human, to take into account contextual information that wasn't available to the machine, or to correct low-confidence predictions.
  * **Automation Reviewing**: deal with exceptions by overriding values in the output of business rules, or filling in missing values.
* **Data Quality Campaigns**: fix incorrect records and improve downstream analytics.

## Features

* **No-code data editing webapp** with powerful data browsing (filtering, sorting, grouping in real-time) and rich editing experience (automatic input validation, linked records, lookup columns). [Learn more →](data-table-features)
* **Continuous updates**: seamless integration of new edits into production data pipelines, and of new data into the webapp (changes are detected automatically and previous edits are applied to the new data).
* **Dataset of edited rows**: use as input to a recipe that writes back to a source system, or for the implementation of a feedback loop (e.g. stacking with an AI training dataset).
* **Governance**: built-in audit trail of all edits made by end-users.
* **API to Create, Read, Update, Delete rows (CRUD)**, for coders building custom webapps.

## How-tos

* [Install](install-plugin) (Dataiku v9 and above)
* Get started:
  * [No-code] [Visual Webapp](get-started): Setup, overview of plugin components and key concepts
  * [Low-code] [CRUD Python API](get-started-crud-python-api): Overview of methods to read/write individual or multiple rows of data
* [Use edits in the Flow](using-edits): Where to find edits & How to leverage for analytics & AI
* [Go further](going-further): Reset edits on a design node, Deploy to production (automation node), Implement feedback loops, FAQ
