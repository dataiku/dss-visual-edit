# Installation

Visual Edit's open-source code is hosted in a [GitHub repository](https://github.com/dataiku/dss-visual-edit/tree/master/dss-plugin-visual-edit). As a result, the plugin can be installed via Git or as a ZIP file (installation via Git is recommended as it allows to easily [update the plugin](update-plugin.md) when new versions are released).

In this guide, we provide details on the steps found in the [Dataiku Documentation: Installing plugins](https://doc.dataiku.com/dss/latest/plugins/installing.html). We also discuss requirements and tips to determine if Visual Edit is a good fit for you, before installation.

## Requirements

- Compatible version of Dataiku, Python, and compatible SQL data connection. See [Compatibility](compatibility.md).
- Ability to install plugins on your Dataiku instance.
- Ability to create a code environment.

## Is it a fit?

Use this quick checklist to determine if Visual Edit meets your needs before installation.

- **Audit trail / rebuilds**
  - Good fit: datasets that are regularly rebuilt or require an audit trail. Here's why:
    - Visual Edit stores edits in a separate _editlog_ dataset
    - Plugin recipes turn this into an _edited_ dataset.
    - As a result, edits survive rebuilds and are auditable.
  - Not a fit: if you require direct in-place editing with no extra artifacts, Visual Edit adds unnecessary complexity to your Flow.

- **Adding or removing rows**
  - The no-code Visual Webapp does not support adding/removing rows.
  - The Visual Edit API has experimental support for row addition/deletion; plan for UI work if you need this.

- **Alternatives**
  - For simple in-place editing or lightweight labeling, evaluate Dataiku core features like [Push to Editable](https://doc.dataiku.com/dss/latest/other_recipes/push-to-editable.html) or [Labeling](https://doc.dataiku.com/dss/latest/machine-learning/labeling.html) as alternatives.
  - For additional customizability, consider low-code webapp frameworks such as Streamlit or Dash and DB drivers/ORM such as SQLAlchemy for direct database edits.

If unsure, try the plugin in a test project first to validate the webapp and integration with your existing Flow.

## Option 1: Git

### Pre-requisite: GitHub remote repository setup

To connect from Dataiku to this repository, you must add your Dataiku user’s public SSH key to the list of accepted SSH keys in your GitHub account.

- Follow the steps provided in the [Dataiku Documentation: Working with Git > Working with remotes > Setup](https://doc.dataiku.com/dss/latest/collaboration/git.html#setup).
- See a more detailed [illustration with Dataiku Cloud](dataiku-cloud-github-setup.md).

### Repository settings

From the Plugins page of your Dataiku instance, once you have clicked on the "Add Plugin" button in the top right corner and chosen "Fetch from Git repository", use the following settings:

- Repository URL: `git@github.com:dataiku/dss-visual-edit.git`
- Development mode: leave unticked
- Checkout: choose `master` under "Branch", to install the latest version of the plugin; alternatively, choose a version number under "Tag"
- Path in repository: `dss-plugin-visual-edit`

## Option 2: ZIP file

Prepare the plugin ZIP file to upload to your Dataiku instance:

- Find the latest release of the plugin at <https://github.com/dataiku/dss-visual-edit/releases>. Under **Assets**, click **Source code (zip)** to download `dss-visual-edit-X.Y.Z.zip` (where `X.Y.Z` is the version number of the release).
- Open the zip file and find the folder `dss-plugin-visual-edit`.
- Create a zip archive of this folder and name it `dss-plugin-visual-edit.zip`

From the Plugins page of your Dataiku instance, once you have clicked on the "Add Plugin" button in the top right corner and chosen "Upload", make sure to choose the `dss-plugin-visual-edit.zip` archive you just created (do NOT use `dss-visual-edit-X.Y.Z.zip`).

## Creating the code environment

When prompted during the installation procedure, select Python 3.9 and the types of containers you plan to use as backend for Visual Edit webapps or for running recipes provided by the plugin (the easiest is to choose All).

The plugin is installed! ![](plugin_installed.png) You can now follow the guides from the [plugin documentation](index.md).
