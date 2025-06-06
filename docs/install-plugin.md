# Installation

## How to install the plugin via Git

### Dataiku Cloud

- Enable maintenance access
- Share this URL with Dataiku Support and ask them to install the plugin for you

### Dataiku self-managed

#### Requirements

- Compatible version of Dataiku, Python, and compatible SQL data connection. See [Compatibility](compatibility.md).
- Ability to install plugins on your Dataiku instance.
- Ability to create a code environment.

#### Instructions

- From the Plugins page of your Dataiku instance, click on the "Add Plugin" button in the top right corner and choose "Fetch from Git repository":
  - Repository URL: `git@github.com:dataiku/dss-visual-edit.git`
  - Development mode: leave unticked
  - Checkout: choose `master` under "Branch", to install the latest version of the plugin; alternatively, choose a version number under "Tag"
  - Path in repository: `dss-plugin-visual-edit`
- Create the code environment for this plugin. Select the version of Python you want to use and the types of containers you plan to use as backend for Visual Edit webapps or for running recipes provided by the plugin (the easiest is to choose All).
- The plugin is installed! ![](plugin_installed.png) We'll see how to use each of its components in the next guide.

## How to update the plugin via Git

From the Plugins page of your Dataiku instance, go to the "Installed" tab, find "Visual Edit" in the list and click on the "Update from repository" link. ![](update_plugin_git.png)

Release notes for all versions are available at [https://github.com/dataiku/dss-visual-edit/releases](https://github.com/dataiku/dss-visual-edit/releases).

## How to install the plugin via ZIP file

- Find the latest release at <https://github.com/dataiku/dss-visual-edit/releases>. Under **Assets**, click **Source code (zip)** to download `dss-visual-edit-X.Y.Z.zip` (where `X.Y.Z` is the version number of the release).
- Open the zip file and find the folder `dss-plugin-visual-edit`.
- Create a zip archive of this folder and name it `dss-plugin-visual-edit.zip`
From the **Plugins page** of your Dataiku instance, click the **Add Plugin** button at the top right corner and choose **Upload**.
- **Choose the `dss-plugin-visual-edit.zip` archive you just created.**
- ⚠️ Do not use `dss-visual-edit-X.Y.Z.zip`.
