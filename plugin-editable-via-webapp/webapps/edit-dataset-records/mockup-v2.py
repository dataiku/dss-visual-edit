import DataTableAIO

project_key = getenv("DKU_CURRENT_PROJECT_KEY")
component_id = "xxx" # component_id would be the id of the Data Editing Visual Webapp, such that the webapp can be viewed at http(s)://{DSS_URL}/public-webapps/{project_key}/{component_id}/

def serve_layout():
    return html.Div(children=[
        html.Div(id="hello", children="Hello!"),
        DataTableAIO(id="datatable", component_id=component_id), # passing component_id as an id of a Dataiku webapp is an alternative to passing the settings of original dataset, primary keys, editable columns, etc., that are already defined in that Dataiku webapp object! (and available even if the webapp is not running)
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
    client._perform_raw( # TODO: not sure this will work
        "POST", f"/public-webapps/{project_key}/{component_id}/update-row", # calling API served by another webapp's backend — this means that the other webapp has to be running; other example with the lookup endpoint: https://dss-1c81e77d-7bc4d1e1-int2.gis-dataiker-2.getitstarted.dataiku.com/public-webapps/JOIN_COMPANIES_SIMPLE/Vao2Cr9/lookup/companies_ext?term=Apple
        params={
            "key": "123",
            "column": "company_name",
            "value": value
        })
    return "Saved"
