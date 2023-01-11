# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashTabulator(Component):
    """A DashTabulator component.


Keyword arguments:

- id (string; optional):
    ID used to identify this component in Dash callbacks.

- applyBulkEdit (list; optional):
    applyBulkEdit, apply bulk edit that has happened.

- cellEdited (dict; optional):
    cellEdited captures the cell that was clicked on.

- columns (list; optional):
    Column definitions.

- data (list; optional):
    Data to display in the table.

- groupBy (list; optional):
    Columns to group by.

- multiRowsClicked (list; optional):
    multiRowsClicked, when multiple rows are clicked."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_tabulator'
    _type = 'DashTabulator'
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, data=Component.UNDEFINED, columns=Component.UNDEFINED, groupBy=Component.UNDEFINED, cellEdited=Component.UNDEFINED, multiRowsClicked=Component.UNDEFINED, applyBulkEdit=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'applyBulkEdit', 'cellEdited', 'columns', 'data', 'groupBy', 'multiRowsClicked']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'applyBulkEdit', 'cellEdited', 'columns', 'data', 'groupBy', 'multiRowsClicked']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashTabulator, self).__init__(**args)
