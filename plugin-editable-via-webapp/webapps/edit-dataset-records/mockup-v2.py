import EditableEventSourced

project_key = getenv("DKU_CURRENT_PROJECT_KEY")
component_id = "xxx" # component_id would be the id of the Data Editing Visual Webapp, such that the webapp can be viewed at http(s)://{DSS_URL}/public-webapps/{project_key}/{component_id}/

ees = EditableEventSourced(name="", primary_keys=["id"], editable_column_names=["col1", "col2"])

def serve_layout():
    return html.Div(children=[
        html.Div(id="hello", children="Hello!"),
        ees.get_datatable(id="datatable"),
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
    ees.update(primary_key="123", column="company_name", value=value)
    return "Saved"
