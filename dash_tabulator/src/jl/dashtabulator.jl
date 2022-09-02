# AUTO GENERATED FILE - DO NOT EDIT

export dashtabulator

"""
    dashtabulator(;kwargs...)

A DashTabulator component.

Keyword arguments:
- `id` (String; optional): ID used to identify this component in Dash callbacks.
- `cellEdited` (Dict; optional): cellEdited captures the cell that was clicked on
- `columns` (Array; optional): Column definitions.
- `data` (Array; optional): Data to display in the table.
- `groupBy` (Array; optional): Columns to group by.
"""
function dashtabulator(; kwargs...)
        available_props = Symbol[:id, :cellEdited, :columns, :data, :groupBy]
        wild_props = Symbol[]
        return Component("dashtabulator", "DashTabulator", "dash_tabulator", available_props, wild_props; kwargs...)
end

