from pandas import pivot_table

def replay_edits(input_df, editlog_df, primary_key, editable_column_names):
    input_df.set_index(primary_key, inplace=True)
    if (not editlog_df.size): # i.e. if empty editlog
        edited_df = input_df
    else:
        editlog_df.set_index(primary_key, inplace=True)
        # - Pivot editlog
        editlog_pivoted_df = pivot_table(editlog_df, index=primary_key, columns="column_name", values="value", aggfunc="last")
        # - Join -> this adds _value_last columns
        edited_df = input_df.join(editlog_pivoted_df, rsuffix="_value_last")
        # - Merge -> this creates _original columns
        for col in editable_column_names:
            # copy col to a new column whose name is suffixed by "_original"
            edited_df[col + "_original"] = edited_df[col]
            # merge original and last edited values
            edited_df.loc[:, col] = edited_df[col + "_value_last"].where(edited_df[col + "_value_last"].notnull(), edited_df[col + "_original"])
        # Drop the _original and _value_last columns -> this gets us back to the original schema
        edited_df = edited_df[edited_df.columns[:-2*len(editable_column_names)]]
    return edited_df.reset_index()