# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args

ComponentType = typing.Union[
    str,
    int,
    float,
    Component,
    None,
    typing.Sequence[typing.Union[str, int, float, Component, None]],
]

NumberType = typing.Union[
    typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
]


class DashTabulator(Component):
    """A DashTabulator component.
DashTabulator is a wrapper for a data table library (e.g. Tabulator).
All table operations are abstracted for easier migration to another library.

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
    Name of the corresponding Dataiku dataset. Used for analytics
    purposes only, as a hash (not the actual name).

- groupBy (list; optional):
    Columns to group by."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_tabulator'
    _type = 'DashTabulator'


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        data: typing.Optional[typing.Sequence] = None,
        columns: typing.Optional[typing.Sequence] = None,
        datasetName: typing.Optional[str] = None,
        groupBy: typing.Optional[typing.Sequence] = None,
        cellEdited: typing.Optional[dict] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'cellEdited', 'columns', 'data', 'datasetName', 'groupBy']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'cellEdited', 'columns', 'data', 'datasetName', 'groupBy']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashTabulator, self).__init__(**args)

setattr(DashTabulator, "__init__", _explicitize_args(DashTabulator.__init__))
