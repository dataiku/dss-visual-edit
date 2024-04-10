# Deploying to production (automation node)

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

## Security

As any Dataiku webapp, it can either require authentication, or it can be made accessible to visitors who are not logged into Dataiku. We do not recommend the latter option, as anyone who has access to the webapp will be allowed to see the data that it exposes and to make edits. If, however, you do want to make the webapp accessible to unauthenticated visitors, their edits will be attributed to the user "none" in the editlog.

When authentication is required:

* The webapp can only be used by users with a Reader license or above.
* It allows to read contents of the original dataset, of the associated editlog, and of the label and lookup columns of linked datasets (if any).
* Even though the name "Reader" might suggest that they can only read data, they webapp doesn't make a distinction between license types and Readers are able to make edits.
* You can restrict access to specified (groups of) users via the Project > Security settings: only those with "Read Dashboard" permission will be able to use the webapp (i.e. see and edit data).
* You can restrict access at the webapp level, via the "Authorized users" property of the Visual Webapp settings. It is presented as a list; if it is not empty, only users whose identifiers are included in the list will be able to use the webapp (i.e. see and edit data).

Remember that the webapp only writes data to the editlog, not to the original dataset (which stays unchanged). The editlog pivoted and the edited datasets can only be changed by running the recipes that build them.

## Best practices and remarks

When sharing the production webapp with business users, it's a good idea to tick "auto-start backend" in webapp settings, which will help make sure that the webapp is always available. In an effort to be conscious of your Dataiku instance's resources, we recommend running the webapp in containerized execution when available.

You can share a direct link to the webapp (or a dashboard that embeds it), but it can be easier for end-users to find it again in the future if it's added to a Workspace. Workspaces provide a friendlier way for business users to access all objects shared with them in Dataiku. If your end-users don't already use a Workspace, we recommend creating one for them and having them use Workspaces as their Dataiku home page.

Remark on concurrent usage: several users can view and edit data at the same time, but they won't see each other's edits in real-time; if 2 or more users try to edit the same cell at the same time, the last edit is the one that will be taken into account.
