# AUTO GENERATED FILE - DO NOT EDIT

export dashtabulator

"""
    dashtabulator(;kwargs...)

A DashTabulator component.

Keyword arguments:
- `id` (String; optional): The ID used to identify this component in Dash callbacks.
- `cellEdited` (Dict; optional): cellEdited captures the cell that was clicked on
- `columns` (Array; optional): A label that will be printed when this component is rendered.
- `data` (Array; optional): The value displayed in the input.
"""
function dashtabulator(; kwargs...)
        available_props = Symbol[:id, :cellEdited, :columns, :data]
        wild_props = Symbol[]
        return Component("dashtabulator", "DashTabulator", "dash_tabulator", available_props, wild_props; kwargs...)
end

