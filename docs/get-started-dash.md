# Getting started: Dash component | Plugin: Writeback | Dataiku

```python
import dataiku
dataiku.use_plugin_libs("writeback")
WritebackDataTable = dataiku.import_from_plugin("writeback", "WritebackDataTable")

wb_dt = WritebackDataTable.WritebackDataTable(original_ds_name="my_dataset")
```