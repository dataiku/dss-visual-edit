# Switching to the `visual-edit` plugin

## Background

**Visual Edit** (plugin id `visual-edit`) is the public release of the previously private plugin **Data Editing** (plugin id `editable-via-webapp`). The core functionalities have remained the same but some key components have been renamed:

* The plugin's Recipes are now called "Replay Edits" and "Apply Edits". They are represented with the same icons as previously in the Flow.
* **The "editlog pivoted" dataset is now simply called the "edits" dataset. This is the most visible change in the Flow.**
* The type of Visual Webapp provided by the plugin is now called "Visual Edit", and is technically identified as `visual-edit`.

We recommend reading this guide entirely before starting the switch.

## Steps for a single project

* Preliminary: make sure that `visual-edit` is installed on your Dataiku instances (design and automation).
* Create a bundle of your Dataiku project (to serve as backup if needed).
* Clone this [Python notebook](https://github.com/dataiku/dss-visual-edit/blob/master/docs/switch-plugins.ipynb) into your Dataiku project:
    * In the Notebooks section of your project, click on "+ New Notebook" and "Import from Git".
    * Fill "Remote URL" with `git@github.com:dataiku/dss-visual-edit.git` and click on "List Notebooks".
    * Select "switch-plugins" from the list and click on "Import 1 Notebook".
* Review the notebook's warnings and run block by block. This will:
    * Delete any `editable-via-webapp` recipes.
    * Rename any "editlog pivoted" datasets.
    * Change the type of Visual Webapp to `visual-edit` and restart: this automatically creates new recipes using the new `visual-edit` plugin.
* If the project includes Scenarios with steps to build the "editlog pivoted" dataset, adapt to the new name.
* If the project includes Code Webapps that leverage the `EditableEventSourced` class of the `editable-via-webapp` plugin's Python library
    * Change the code to use the `DataEditor` class of the `visual-edit` plugin's Python library (this means renaming the class _and_ the plugin id used to import the class).
    * Restart the webapps.

## Switching all projects

You can find a list of projects that use `editable-via-webapp` at `/plugins/editable-via-webapp/usages/` in the Dataiku web interface. This can also be accessed programmatically using the Python client:

```python
usages = client.get_plugin("editable-via-webapp").list_usages()
for usage in usages.usages:
    if usage.element_kind == "webapps":
        project_key = usage.project_key
        print(project_key)
```

You could combine this and the Python notebook to switch all projects at once, but prior to this we recommend to...

* Notify project owners.
* Inform them of the procedure: share this guide with them, along with the Python notebook, and highlight its warnings.
* Make sure that a backup is created for each project.
* Get project owners' approval.

Once all of these projects have switched to the new `visual-edit` plugin, you can uninstall the `editable-via-webapp` plugin from your Dataiku design instances. This will prevent any new projects from using the old plugin.

Once all of these projects have been deployed to your Dataiku automation instances, you can list usages of the `editable-via-webapp` plugin on these instances; if none, you can uninstall.
