# Building a complete application to test with end-users

As a first step, make sure to read the [How to Use](https://www.dataiku.com/product/plugins/visual-edit/#how-to-use) guide on the plugin's presentation page.

## Integrating edits in automation Scenarios

We recommend creating the following automation Scenarios:

* **_Commit Edits_**, to build all datasets downstream of the _editlog_ and to update dashboards based on them. Remember that edits made via the webapp are not instantly reflected in the _edits_ and _edited_ datasets (only the _editlog_ is updated in real-time).
  * Its execution can be scheduled, or it can be triggered manually. If you have a _Reset Edits_ scenario, add a step at the end to also run the _Commit Edits_ scenario.
  * If you want to allow end-users to trigger this scenario on their own, you can embed the Visual Edit webapp in a Dashboard to which you will add a Scenario tile (more on this in the next section).
* **_Update Source_**, to take into account any changes or additional data from source systems, re-build the Original Dataset used by the webapp, and re-run the _Commit Edits_ scenario.

## Publishing the webapp to a Dashboard

The best way to make the webapp accessible to business users is by publishing it to a Dashboard. There can be 2 separate Dashboards for Editing and for Reporting purposes, or there can be a single Dashboard with 2 pages.

* Editing Dashboard:
  * From the Webapp view, click on the **ACTIONS** button of the menu in the top-right corner, to publish the webapp to a Dashboard. ![](publish_dashboard.png)
  * From the Dashboard view, add other "tiles" to the page, such as a Text tile with instructions on how to use the webapp, and a Scenario tile displayed as a button to run the _Commit Edits_ Scenario discussed above. You can also adjust the layout. ![](dashboard_edit.png)
* Reporting Dashboard:
  * This would consist in charts built from the _edited_ dataset or other datasets downstream.
  * It could include a Scenario tile to run the _Update Source_ Scenario.
  * It would be accessed by business users via the web, and it could also be scheduled to be converted to a PDF and sent by email via a Scenario.

Important remarks on deployment:

* This Dashboard and its associated link would only be for test purposes.
  * Because you're building a project with an interface where users can enter data which then gets processed, you'll need to have two instances of the project: one for development and one for production; each will have its own set of edits.
  * You can reset edits by creating and running a _Reset Edits_ scenario with an **Initialize editlog** Step. This type of Scenario Step is provided by the plugin and can be found toward the end of the list of available Steps. Only use this on a design node as part of your tests.
  * Once your tests are successful, the next step is to [deploy your project](deploy) on an automation node, or as a duplicate project on your design node.
* End-users must be Dataiku users on a Reader license or above.
