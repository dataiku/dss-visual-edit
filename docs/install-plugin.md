# Install the _Editable via Webapp_ plugin

* Load the plugin - 2 options: fetch from Git or upload a ZIP file
  * Fetch from Git
    * Repository URL: `git@github.com:dataiku/lca.git`
    * Checkout: choose [latest release tag](https://github.com/dataiku/lca/releases), e.g. vX.Y.Z
    * Path in repository: `plugin-editable-via-webapp`
  * OR Upload a ZIP file
    * Download `lca` repo from the [latest release](https://github.com/dataiku/lca/releases)
    * Create a ZIP file from the `plugin-editable-via-webapp` directory
    * Upload to your Dataiku instance
      * ![](add_plugin_upload.png)
      * ![](add_plugin_select_zip.png)
* Create the code environment for this plugin
  * ![](add_plugin_creating_code_env.png)
  * ![](add_plugin_creating_code_env_2.png)
  * ![](add_plugin_creating_code_env_done.png)
  * ![](add_plugin_creating_code_env_done_2.png)
  * ![](add_plugin_done.png)
* The plugin is installed! ![](plugin_installed.png)
