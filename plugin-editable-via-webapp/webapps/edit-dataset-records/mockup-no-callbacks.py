
ees = EditableEventSourced(DATASET_NAME)
datatable = lca.DataTable(ees)
key = datatable.selected_row.key
company_name = lca.TextInput(label="Company Name", value=datatable.selected_row.company_name)
lca.Button("Save", ees.update_row({"key": key, "company_name": company_name.value})) # TODO: need to update datatable rendering accordingly... the update_row function could use pubsub for that?
