# Switching to the `visual-edit` plugin

## Overview

**Visual Edit** (plugin id `visual-edit`) is the public release of the previously private plugin **Data Editing** (plugin id `editable-via-webapp`). The core functionalities have remained the same but some key components have been renamed:

* The plugin's Recipes are now called "Replay Edits" and "Apply Edits". They are represented with the same icons as previously in the Flow.
* **The "editlog pivoted" dataset is now simply called the "edits" dataset. This is the most visible change in the Flow.**
* The type of Visual Webapp provided by the plugin is now called "Visual Edit", and is technically identified as `visual-edit`.

In this document we provide Python code to help switch to the new plugin. It consists, in a given project, in...
* Deleting any `editable-via-webapp` recipes.
* Renaming any "editlog pivoted" datasets.
* Changing the type of Visual Webapp to `visual-edit` and restarting these webapps: this automatically creates new recipes using the new `visual-edit` plugin.

We provide instructions to use this Python code. We also provide additional instructions for webapp coders who used `editable-via-webapp`'s Python library.

## Instructions

* Preliminary step: [Install the `visual-edit` plugin](install-plugin) (keep `editable-via-webapp` for now).
* For each project where you used `editable-via-webapp` (you can find a list of such projects at `/plugins/editable-via-webapp/usages/` in the Dataiku DSS web interface):
    1. Change the `project_key` variable in the Python code.
    2. Create a bundle of your Dataiku project (to serve as backup if needed).
    3. Review the code below and run as a script, or block by block in a notebook environment, either from Dataiku DSS or from your local Python environment (provided it has the `dataiku` package installed).
    4. If the project included Scenarios with a step to build the "editlog pivoted" dataset, adapt to the new name.
* Once you've done this for all projects, you can uninstall the `editable-via-webapp` plugin.

## Python code

```python
# %%
# Initialize dataiku client and project
import dataiku

project_key = "ML_FEEDBACK_LOOP"
dss_client = dataiku.api_client()
project = dss_client.get_project(project_key)

# %%
# Delete plugin recipes
for recipe in project.list_recipes(as_type="objects"):
    # print(recipe)
    recipe_type = recipe.get_settings().type
    if (
        recipe_type == "CustomCode_merge-edits"
        or recipe_type == "CustomCode_pivot-editlog"
    ):
        recipe.delete()

# %%
# Rename all datasets ending with '_editlog_pivoted' to end with '_edits'
for d in project.list_datasets():
    dataset_name = d["name"]
    dataset = project.get_dataset(dataset_name)
    # if the name ends with '_editlog_pivoted', rename it to change the suffix to '_edits'
    if dataset_name.endswith("_editlog_pivoted"):
        new_name = dataset_name.replace("_editlog_pivoted", "_edits")
        # add to list of datasets to build
        dataset.rename(new_name)
        print(f"Renamed {dataset_name} to {new_name}")

# %%
# Stop Visual Webapps, change their types, and restart them: this re-creates the recipes we deleted but with the types from the new plugin
for webapp in project.list_webapps(as_type="objects"):
    webapp_settings = webapp.get_settings()
    if (
        webapp_settings.get_raw()["type"]
        == "webapp_editable-via-webapp_edit-dataset-records"
    ):
        webapp.stop_backend()
        webapp_settings.get_raw()["type"] = "webapp_visual-edit_visual-edit"
        webapp_settings.save()
        print(
            f"Changed type of {webapp_settings.get_raw()['name']} to 'webapp_visual-edit_visual-edit'"
        )
        webapp.start_or_restart_backend()
```

## Instructions for webapp coders

The `EditableEventSourced` class of the plugin's Python library was renamed `DataEditor`. If you were using this class in a code webapp, make sure to rename both the class and the plugin id used to import the class.
