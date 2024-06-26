# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashTabulator(Component):
    """A DashTabulator component.


Keyword arguments:

- id (string; optional):
    ID used to identify this component in Dash callbacks.

- cellEdited (dict; optional):
    cellEdited captures the cell that was clicked on.

- columns (list; optional):
    Column definitions.

- data (list; optional):
    Data to display in the table.

- datasetName (string; default ""):
    Name of the corresponding Dataiku dataset.

- groupBy (list; optional):
    Columns to group by."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_tabulator'
    _type = 'DashTabulator'
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, data=Component.UNDEFINED, columns=Component.UNDEFINED, datasetName=Component.UNDEFINED, groupBy=Component.UNDEFINED, cellEdited=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'cellEdited', 'columns', 'data', 'datasetName', 'groupBy']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'cellEdited', 'columns', 'data', 'datasetName', 'groupBy']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashTabulator, self).__init__(**args)
