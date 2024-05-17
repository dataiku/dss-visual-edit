# Installation | Plugin: Visual Edit | Dataiku

## Requirements

* Dataiku 9 or more recent
* Ability to install plugins on your Dataiku instance and to create an associated code env based on Python 3.9
* For Dataiku Cloud:
  * Make sure the "code env" feature is activated; if it's not, use the contents of the requirements file to create your first environment
  * Enable maintenance access so that someone can install the plugin for you

## How to install the plugin

* From the Plugins page of your Dataiku instance, click on the "Add Plugin" button in the top right corner and choose "Fetch from Git repository":
  * Repository URL: `git@github.com:dataiku/dss-visual-edit.git`
  * Development mode: leave unticked
  * Checkout: `master`
  * Path in repository: `dss-plugin-visual-edit`
* Create the code environment for this plugin. Select the types of containers you plan to use as backend for data editing webapps or for running recipes provided by the plugin (the easiest is to choose All).
* The plugin is installed! ![](plugin_installed.png) We'll see how to use each of its components in the next section.

## How to update the plugin

From the Plugins page of your Dataiku instance, go to the "Installed" tab, find "Visual Edit" in the list and click on the "Update from repository" link. ![](update_plugin_git.png)

## Next

Check out the guide to [Get started](get-started) for an introduction to the plugin's components and how to use them.