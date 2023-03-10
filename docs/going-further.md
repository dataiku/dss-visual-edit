# Going further

## Adding the webapp to a Dashboard

The best way to make this webapp accessible to end-users is by publishing it to a Dashboard (from the webapp view, click on the Actions button of the menu at the top, on the right-hand side).

![](publish_dashboard.png)

You can then add other "tiles" to your Dashboard, such as a Text tile with instructions on how to use the webapp, or a Scenario tile, and adjust the layout.

![](dashboard_edit.png)

The Scenario tile is displayed as a button to run a chosen scenario. This is a great way to let the end-user run computations that take edits into account. An example is provided in our [sample project: join companies](sample-project-join-companies).

## Resetting edits on a design node

Create and run a scenario with an "Initialize editlog" Step. This type of scenario step is provided by the plugin and can be found toward the end of the list of available steps.

![](scenario_initialize_editlog.png)

You can also add a step to run a scenario dedicated to building datasets downstream of the editlog.

## Deploying to production (automation node)

1. Make sure that the version of the plugin installed on the Automation node is the same as on the Design node.
2. Create a new bundle (do not include the contents of the editlog in the bundle, as it would replace edits made in production with those made on the design node).
3. If this isn't a first deployment of your project but an update, go straight to step 4. Otherwise, initialize the editlog used on the Automation node:
   * ⚠️ Preliminary remarks and motivation:
     * Unlike most datasets managed by Dataiku, editlogs are source datasets (with no recipe upstream).
     * For a given data editing webapp, you would want to have two different editlog datasets: one on the Design node, one on the Automation node. This way, edits made on the Design node won't have any impact in production.
     * These two editlog datasets would have the same name, but they should be on different data connections.
     * Upon deploying the project bundle for the first time on the Automation node, the editlog dataset will exist and it will have a schema, but it may appear as having an invalid configuration. This would be the case when using a SQL connection, as the table used for the editlog in Automation won't be automatically created by the bundle deployment process.
   * Please create and run a scenario with an "Initialize editlog" step, to ensure that the editlog is properly initialized. ![](scenario_step.png)
   * You can then open the dataset and make sure that you see an empty editlog that looks like this: ![](empty_editlog.png)
   * You can then delete the scenario, to make sure that it won't be used accidentally in the future (which would cause losing all edits).
4. Build the dataset used by the webapp as the "original dataset" to edit.
5. (Stop and) Start the webapp.

Demo videos:
* [Deploy to production](https://www.loom.com/share/e47c5d09871741c48062e3547108bb39)
* [Update in production](https://www.loom.com/share/8b806a65e50a4406b9ec3d4a31495205)

## Feedback loops

In some use cases the data to review/edit in the webapp depends on previous edits. Check out our [sample project](sample-project-join-companies) that demonstrates this and shares best practices.

## FAQ

### What happens if my source dataset changes?

The webapp automatically detects changes in the original dataset, by periodically checking the last build date of the dataset. As a consequence, it only works if this isn't a "source" dataset but the output of a recipe.

![](refresh_data.png)

### What happens if I change primary keys or editable columns in the webapp settings?

* Primary key:
  * Add:
    * If this primary key had already been in use in the past (and you're adding it back), there may be rows in the editlog that contain a value for this key, and these rows will be taken into account.
    * Otherwise, previous edits won't be taken into account by the webapp / the recipes.
  * Remove:
    * If the remaining keys allow to uniquely identify a row in the dataset, then there is no impact.
    * Otherwise, many rows could be impacted by a single row of the editlog (instead of a single row).
* Editable column:
  * Add: no impact.
  * Remove: previous edits on this column won't be taken into account by the webapp / the recipes, and they won't appear in _editlog\_pivoted_ (but they will still be in the editlog).

## Troubleshooting

If the webapp backend started successfully but the webapp itself isn't functioning as expected, clear the browser's cached images and files.
