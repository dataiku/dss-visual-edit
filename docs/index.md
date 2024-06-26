# Plugin: Visual Edit | Dataiku

## Build apps to validate and edit data within pipelines

![](demo_unmatched_entities.gif)

[Book a demo!](https://calendar.google.com/calendar/u/0/appointments/schedules/AcZssZ1cgQ-IQ2k2eJMm6mUrZxabQgtPSSwaZ9TgNcHcnaUDvrqfweAkf-B7xzZbTSNyYeSRc2smgLbp){: .btn}

Use Cases: enable domain experts to...

* Validate the output of rules or AI used for
  * Mass corrections/enrichment of source data: **entity resolution, deduplication, categorization**, etc.
  * Operational processes: **log decisions on alerts, validate suggestions of amounts to pay or orders to place**, etc.
* Make tactical corrections on source data, to ensure correctness of an analytics project.

Features:

* Powerful data table with rich editing experience and a special validation column.
* Easy webapp setup (no-code and low-code options) and integration of edits in your pipeline.
* Ability to leverage human feedback for continuous AI improvement.
* Audit trail of all edits.

## Plugin information

* Author: Dataiku (Louis Dorard, Julien Hobeika, Fabien Daoulas)
* [Source code](https://github.com/dataiku/dss-visual-edit/)
* [Reporting issues](https://github.com/dataiku/dss-visual-edit/issues)

## Quick links

* For Data Experts:
  * [Installation](install-plugin)
  * User guides:
    * [Use Case #1: Correcting Source Data](get-started)
    * [Use Case #2: Reviewing Machine-Generated Data](reviewing)
    * [Deploying in Production](deploy)
  * Advanced features:
    * [Linked Records](linked-records)
    * [Editschema](editschema)
  * For Developers:
    * [Introduction to Visual Edit's CRUD Python API](https://github.com/dataiku/dss-visual-edit/blob/master/docs/CRUD_example_usage.ipynb)
    * [Low-code webapp customizations with Dash](dash-examples)
    * [Reference API documentation]([backend/](https://dataiku.github.io/dss-visual-edit/backend/#DataEditor))
    * Full-code webapp customizations: see [dash_tabulator documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dash_tabulator/README.md) and [Plugin Developer Documentation](https://github.com/dataiku/dss-visual-edit/blob/master/dss-plugin-visual-edit/README.md)
  * [FAQ](faq)
* For Business Users:
  * [How to use the data table](data-table-features)
