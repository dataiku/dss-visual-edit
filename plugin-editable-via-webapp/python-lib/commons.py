from pandas import DataFrame, concat, pivot_table

def get_editlog_schema():
    return [
        {"name": "date", "type": "string", "meaning": "DateSource"}, # not using date type, in case the editlog is CSV TODO: make sure that it's read as a date in the replay recipe
        {"name": "user", "type": "string", "meaning": "Text"},
        {"name": "key", "type": "string"},
        {"name": "column_name", "type": "string", "meaning": "Text"},
        {"name": "value", "type": "string"}
    ]

def get_editlog_columns():
    return ["date", "user", "key", "column_name", "value"]

def get_editlog_df(editlog_ds):
    # Try to get dataframe from editlog dataset, if it's not empty. Otherwise, create empty dataframe.
    try:
        editlog_df = editlog_ds.get_dataframe()
    except:
        editlog_df = DataFrame(columns=get_editlog_columns())
        editlog_ds.write_schema(get_editlog_schema())
        editlog_ds.write_dataframe(editlog_df)
    return editlog_df

def get_table_name(dataset):
    return dataset.get_config()["params"]["table"].replace("${projectKey}", project_key).replace("${NODE}", dataiku.get_custom_variables().get("NODE"))

def pivot_editlog(editlog_df):
    if (not editlog_df.size): # i.e. if empty editlog
        editlog_pivoted_df = editlog_df
    else:
        editlog_df.set_index("key", inplace=True)
        # For each named column, we only keep the last value
        editlog_pivoted_df = pivot_table(
            editlog_df.sort_values("date"), # ordering by edit date
            index="key",
            columns="column_name",
            values="value",
            aggfunc="last").join(
                editlog_df[["date"]].groupby("key").last() # join the last edit date for each key
                )
    return editlog_pivoted_df.reset_index()

def replay_edits(input_df, editlog_df, primary_key, editable_column_names):
    input_df.set_index(primary_key, inplace=True)
    if (not editlog_df.size): # i.e. if empty editlog
        edited_df = input_df
    else:
        editlog_pivoted_df = pivot_editlog(editlog_df).set_index("key")

        # We don't need the date column in the rest
        editlog_pivoted_df = editlog_pivoted_df.drop(columns=["date"])
        
        # Make sure we have all editable columns (even those whose names don't appear in the editlog because they were never edited)
        # For this we just concatenate an empty dataframe with these columns, with the editlog
        all_editable_columns_df = DataFrame(columns=editable_column_names)
        editlog_pivoted_df = concat([all_editable_columns_df, editlog_pivoted_df])

        # Change types of columns to match input_df?
        # for col in editlog_pivoted_df.columns.tolist():
        #     editlog_pivoted_df[col] = editlog_pivoted_df[col].astype(input_df[col].dtype)

        # Join -> this adds _value_last columns
        editlog_df.index.names = [primary_key]
        edited_df = input_df.join(editlog_pivoted_df, rsuffix="_value_last")

        # "Merge" -> this creates _original columns
        for col in editable_column_names:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"])

        # Drop the _original and _value_last columns -> this gets us back to the original schema
        edited_df = edited_df[edited_df.columns[:-2*len(editable_column_names)]]

    return edited_df.reset_index()