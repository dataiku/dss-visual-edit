# Getting started | Plugin: Visual Edit | Dataiku

## Use case description

There are two main types of use cases for the plugin's Visual Webapp:

* Making corrections on "source" data (meaning data that's not machine-generated)
* Reviewing machine-generated data

In this guide, we focus on the former. The latter is slightly more complex and will be covered in a separate guide.

Here, we want business users (aka end-users) to edit data based on their domain expertise, and we want to use the edited data for better downstream analytics and reporting. Instead of doing this in Excel, we want end-users to access a web interface. Therefore we need a front-end for them to see and enter data, and we need to "connect" the data entered via the web front-end with the analytics pipeline. This guide is structured as follows:

* Preliminary steps
* Create a Visual Edit webapp
* Start the webapp
* Test the webapp
* Use edits in the Flow

## Preliminary steps

* [Install the plugin](install-plugin), if not already available.
* Create a new project and add a dataset (via an existing Connection, or file upload). The screen captures shown in this guide were taken on a new project where we uploaded the [orders CSV file](https://downloads.dataiku.com/public/website-additional-assets/data/orders.csv) found in the [Basics 101 course](https://academy.dataiku.com/path/core-designer/basics-101) of the Dataiku Academy. You could also apply the following to an existing project and dataset, which may appear as an input dataset or as the result of an existing recipe.
* Review the dataset schema. The plugin's Visual Webapp uses it to display, sort, filter data and enable editing in the most appropriate way. When a column meaning was defined explicitly, the webapp will use it; otherwise it will consider the storage type instead.
  * Use a “Boolean” meaning to show boolean values as ticks and crosses and to enable editing with checkboxes; filtering will be text-based;
  * Use a numerical meaning to restrict editing to numbers only, to enable sorting by numerical order, and filtering with min-max values;
  * Use a “Date” meaning to enable sorting by chronological order, editing and filtering with date pickers
  * Use a “Text” meaning for both free-text input and for dropdowns (this will be specified in the Visual Webapp's settings), text-based filtering, and sorting by alphabetical order.


## Create a Visual Edit webapp

* Go to Webapps, create New Visual Webapp, pick Visual Edit (this component is provided by the plugin).
  * ![](new_visual_webapp.png)
  * ![](new_visual_webapp_2.png)
* Settings:
  * _Data_:
    * Select a dataset, list primary keys and editable columns (note that a column can't be both). ![](visual_edit_webapp_params_orders.png)
    * Double check the selection of primary keys and editable columns: ground-truth values of editable columns should be fixed for a given (set of) primary key(s) value(s).
  * _Linked Records_: for columns where the editor should be a dropdown widget — see dedicated page [here](linked-records).
  * _Layout_: here you can choose to freeze editable columns to the right-hand side (which is useful when there are many columns), and to group rows by one or more columns.
  * Advanced settings can be provided via the ["editschema" in JSON](editschema).

## Start the webapp

Here is an example of what a Visual Edit webapp would look like:

![](webapp_orders.png)

3 datasets are created upon starting the webapp (if they don't already exist): ![](new_datasets.png)
Their names start with the original dataset's name. Let's review them by their suffix:

1. **_editlog_** is the raw record of all edit events captured by the webapp. It also serves as an audit trail, for governance purposes. The schema of this dataset is fixed, whatever the original dataset. Here is an example: ![](editlog.png)
2. **_editlog\_pivoted_** is the output of the _pivot-editlog_ recipe (provided by the plugin) and the user-friendly view of edits. In the previous example: ![](editlog_pivoted.png)
  * Its schema is a subset of the original dataset's: it doesn't have columns that are display-only, but it has the same key columns and the same editable columns, plus a _last\_edit\_date_ column.
  * Its rows are a subset of the original dataset's: it doesn't contain rows where no edits were made.
  * You can think of it as...
    * A "diff" between edited and original data.
    * A dataset of overrides to apply to the original dataset.
    * The result of "replaying" edit events stored in the log: we only see the last edited values.
3. **_edited_** is the output of the _merge-edits_ recipe (provided by the plugin) that feeds from the original dataset and the _editlog\_pivoted_.
  * It corresponds to the edited data that you are seeing via the webapp.
  * However, it is not in sync with the webapp: it's up to you to decide when to build it in the Flow.
  * It contains the same number of rows as in the original dataset. For any given cell identified by its column and primary key values, if a non-empty value is found in _editlog\_pivoted_, this value is used instead of the original one.
  * Note that, as a result of the above, it is impossible to empty a non-empty cell with the plugin’s Visual Webapp and recipes. This is because empty values in _editlog\_pivoted_ are ignored.

The datasets are created on the same connection as the original dataset. If not already the case, we recommend using a SQL connection for fast and reliable edits. For edits to be recorded by the webapp, this has to be a write connection. If that's not the case, you can change the connection of these datasets as soon as they've been added to the Flow.

Settings such as primary keys and editable columns are copied into the _Visual Edit_ fields of the original and the _editlog_ datasets ([custom fields provided by the plugin](https://doc.dataiku.com/dss/latest/plugins/reference/custom-fields.html) — see the bottom right corner of the screenshot above). This is how the recipes have access to settings defined in the webapp.

## Test the webapp on your own

You may want to test the webapp with a few edits, then check the _editlog_ dataset to see the recorded changes. See all end-user features of the webapp's data table [here](data-table-features).

### How to reset edits

Only use this on a design node, if needed for your tests.

Create and run a _reset edits_ scenario with an "Initialize editlog" Step. This type of scenario step is provided by the plugin and can be found toward the end of the list of available steps.

![](scenario_initialize_editlog.png)

### Behind the scenes

When opening the webapp in your browser, the same code as in the recipes is executed, from the original dataset and the editlog, in order to present an edited view of the data.

Edits made via the webapp instantly add rows to the _editlog_. The _editlog\_pivoted_ and _edited_ datasets are updated only when you run the corresponding recipes.

## Use edits in the Flow

You may want to leverage the _editlog\_pivoted_ dataset to write corrections back to the IT system that holds source data.

In most use cases, however, you would first use the _edited_ dataset as input to recipes, for analytics and reporting purposes. Here are a few tips when doing that:

* Edits would not be instantly reflected in your reporting, as the _edited_ dataset is not updated in real-time. You decide when you want this to happen.
* We recommend creating a **_commit edits_** scenario that builds all that is downstream of the _editlog_ and updates the reporting based on edited data. Its execution can be scheduled, or it can be triggered manually. If you have a _reset edits_ scenario, add a step at the end to also run the _commit edits_ scenario.
* If you want to allow end-users to trigger this scenario on their own, you can embed the Visual Edit webapp in a Dashboard to which you will add a Scenario tile (more on this in the next section).
* Reporting is materialized by a dashboard built from the edited dataset or other datasets downstream. This dashboard would be accessed by business users via the web, or it would be scheduled to be converted to a pdf and sent by email via a dedicated scenario. We recommend creating an **_update source_** scenario to take into account any changes or additional data from source systems, re-build the dataset used by the webapp, and re-run the _commit edits_ scenario.

## Test the webapp with a business user

Prerequisite: End-users of the webapp must be Dataiku users on a Reader license or above.

The best way to make the webapp accessible to business users is by publishing it to a Dashboard. For this, from the webapp view, click on the Actions button of the menu at the top, on the right-hand side).

![](publish_dashboard.png)

You may have already created a Dashboard in your project for reporting purposes; in this case, add the webapp to a new slide of the dashboard.

You can then add other "tiles" to your Dashboard, such as a Text tile with instructions on how to use the webapp, or a Scenario tile, and adjust the layout.

![](dashboard_edit.png)

The Scenario tile is displayed as a button to run a chosen scenario (typically the _commit edits_ scenario discussed above).

## Next

* If you need to customize the way the webapp displays data and create your own Visual Edit front-end, check out the guide to our [CRUD Python API](get-started-crud-python-api) and the examples it contains to learn how to use the plugin's data persistence layer for your webapp's backend.
* Because we're building a project with an interface where users can enter data and this gets processed, we'll need to have two instances of the project leveraging the plugin: one for development, one for production; each will have its own set of edits. Once all your tests are successful, the next step is to [deploy your project](deploy) on an automation node, or as a duplicate project on your design node.
* If you're interested in the use case of reviewing machine-generated data, check out the [dedicated guide](reviewing).
* You can also check out the [FAQ](faq) to learn more about the plugin.
