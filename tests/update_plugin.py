import os
from dataikuapi import DSSClient

host = os.getenv("DSS_HOST")
api_key = os.getenv("DSS_API_KEY")
plugin_id = os.getenv("PLUGIN_ID")
client = DSSClient(host, api_key)
plugin = client.get_plugin(plugin_id)
print("Found plugin")
# Find the zip file in the dist directory
dist_dir = "./dist"
zip_files = [f for f in os.listdir(dist_dir) if f.endswith(".zip")]
if not zip_files:
    raise FileNotFoundError("No zip file found in the dist directory")
# Assuming there's only one zip file, or you can add more logic to select the right one
zip_file_path = os.path.join(dist_dir, zip_files[0])
print(f"Found zip file: {zip_file_path}")

# Update the plugin from the zip file
with open(zip_file_path, "rb") as file_obj:
    print("Update PLUGIN")
    plugin.update_from_zip(file_obj)

# Update the code environment
print("Update CODE ENV")
future = plugin.update_code_env()
future.wait_for_result()
print("Plugin has been updated successfully.")
