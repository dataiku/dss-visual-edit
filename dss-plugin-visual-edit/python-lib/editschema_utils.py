def get_editable_column_names(schema):
    editable_column_names = []
    for col in schema:
        if col.get("editable"):
            editable_column_names.append(col.get("name"))
    return editable_column_names


def get_primary_keys(schema):
    keys = []
    for col in schema:
        if col.get("editable_type") == "key":
            keys.append(col["name"])
    return keys
