# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashTabulator(Component):
    """A DashTabulator component.


Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- cellEdited (dict; optional):
    cellEdited captures the cell that was clicked on.

- columns (list; optional):
    A label that will be printed when this component is rendered.

- data (list; optional):
    The value displayed in the input."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_tabulator'
    _type = 'DashTabulator'
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, columns=Component.UNDEFINED, data=Component.UNDEFINED, cellEdited=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'cellEdited', 'columns', 'data']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'cellEdited', 'columns', 'data']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}
        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(DashTabulator, self).__init__(**args)
