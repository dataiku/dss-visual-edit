def get_linked_records(params, linked_records_count):
    """
    Get linked records from webapp parameters, as a list of dictionaries
    """
    linked_records = []
    if linked_records_count > 0:
        for c in range(1, linked_records_count + 1):
            name = params.get(f"linked_record_name_{c}")
            ds_name = params.get(f"linked_record_ds_name_{c}")
            ds_key = params.get(f"linked_record_key_{c}")
            ds_label = params.get(f"linked_record_label_column_{c}")
            ds_lookup_columns = params.get(f"linked_record_lookup_columns_{c}")
            if not ds_label:
                ds_label = ds_key
            if not ds_lookup_columns:
                ds_lookup_columns = []
            linked_records.append(
                {
                    "name": name,  # name of the original dataset's column which is a linked record
                    "ds_name": ds_name,  # name of the linked dataset
                    "ds_key": ds_key,  # name of the linked dataset's column which acts as primary key
                    "ds_label": ds_label,  # name of the linked dataset's column to be used as label for display purposes, instead of the key
                    "ds_lookup_columns": ds_lookup_columns,  # list of column names in the linked dataset to be looked up and displayed when editing a linked record
                }
            )
    return linked_records
