# TODO: import EES

ees = EditableEventSourced(original_ds_name)

def serve_layout():
    # This function is called upon loading/refreshing the page in the browser
    return html.Div(children=[
        lca.DataTable(id="datatable", component_id=COMPONENT_ID),
        lca.TextInput(id="company_name"), # TODO: change for an actual component
        lca.Button(id="save") # TODO: change for an actual component
    ])

app.layout = serve_layout

@app.callback(
    Output("info", "children"),
    Input("save", "n_clicks"),
    State("company_name", "value"),
    prevent_initial_call=True)
def save_form(value):
    client._perform_raw(
        "POST", f"/public-webapps/{COMPONENT_ID}/update-row", # TODO: check URL of public webapp
        params={
            "key": "123",
            "column": "company_name",
            "value": value
        })
    return "Saved"
