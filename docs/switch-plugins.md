# Switching to the `visual-edit` plugin

**Visual Edit** (plugin id `visual-edit`) is the public release of the previously private plugin **Data Editing** (plugin id `editable-via-webapp`). If you want your projects based on `editable-via-webapp` to switch to using `visual-edit`, follow the steps below:

1. [Install the `visual-edit` plugin](install-plugin) (keep `editable-via-webapp` for now)
2. Change the `project_key` variable in the code below
3. Create a bundle of your Dataiku project (to serve as backup if needed)
4. Run the code below as a script, or block by block in a notebook environment, either from Dataiku DSS or from your local Python environment (provided it has the `dataiku` package installed)
5. Repeat for all projects where you used `editable-via-webapp`. You can find a list of such projects at `/plugins/editable-via-webapp/usages/` in the Dataiku DSS web interface
6. Once you've done this for all projects, you can uninstall the `editable-via-webapp` plugin.

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
# Stop visual webapps, change their types, and restart them: this re-creates the recipes we deleted but with the types from the new plugin
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
