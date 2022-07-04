# AUTO GENERATED FILE - DO NOT EDIT

export dashtabulator

"""
    dashtabulator(;kwargs...)

A DashTabulator component.
DashTabulator is an implementation of the React Tabulator from 
https://github.com/ngduc/react-tabulator/ and https://github.com/olifolkerd/tabulator.
It takes a property, `column`, and `data`
displays it in tabulator.
The `options` property is passed to Tabulator to perform regular options
downloading as xlsx is enabled by default.
Keyword arguments:
- `id` (String; optional): The ID used to identify this component in Dash callbacks.
- `ajaxError` (Bool | Real | String | Dict | Array; optional)
- `ajaxRequesting` (Bool | Real | String | Dict | Array; optional)
- `ajaxResponse` (Bool | Real | String | Dict | Array; optional)
- `cellClick` (Bool | Real | String | Dict | Array; optional)
- `cellContext` (Bool | Real | String | Dict | Array; optional)
- `cellDblClick` (Bool | Real | String | Dict | Array; optional)
- `cellDblTap` (Bool | Real | String | Dict | Array; optional)
- `cellEditCancelled` (Bool | Real | String | Dict | Array; optional)
- `cellEdited` (Dict; optional): cellEdited captures the cell that was clicked on
- `cellEditing` (Bool | Real | String | Dict | Array; optional)
- `cellTap` (Bool | Real | String | Dict | Array; optional)
- `cellTapHold` (Bool | Real | String | Dict | Array; optional)
- `clearFilterButtonType` (Dict; optional): clearFilterButtonType, takes a css style, text to display on button
e.g.
 clearFilterButtonType = {"css": "btn btn-primary", "text":"Export"}
- `clipboardCopied` (Bool | Real | String | Dict | Array; optional)
- `clipboardPasteError` (Bool | Real | String | Dict | Array; optional)
- `clipboardPasted` (Bool | Real | String | Dict | Array; optional)
- `columnMoved` (Bool | Real | String | Dict | Array; optional)
- `columnResized` (Bool | Real | String | Dict | Array; optional)
- `columnTitleChanged` (Bool | Real | String | Dict | Array; optional)
- `columnVisibilityChanged` (Bool | Real | String | Dict | Array; optional)
- `columns` (Array; optional): A label that will be printed when this component is rendered.
- `data` (Array; optional): The value displayed in the input.
- `dataChanged` (Array; optional): dataChanged captures the cell that was clicked on
- `dataFiltered` (Dict; optional): dataFiltered based on http://tabulator.info/docs/4.8/callbacks#filter
The dataFiltered callback is triggered after the table dataset is filtered
- `dataFiltering` (Array; optional): dataFiltering based on http://tabulator.info/docs/4.8/callbacks#filter
The dataFiltering callback is triggered whenever a filter event occurs, before the filter happens.
- `dataGrouped` (Bool | Real | String | Dict | Array; optional)
- `dataGrouping` (Bool | Real | String | Dict | Array; optional)
- `dataLoaded` (Bool | Real | String | Dict | Array; optional)
- `dataLoading` (Bool | Real | String | Dict | Array; optional)
- `dataSorted` (Bool | Real | String | Dict | Array; optional)
- `dataSorting` (Bool | Real | String | Dict | Array; optional)
- `downloadButtonType` (Dict; optional): downloadButtonType, takes a css style, text to display on button, type is file type to download
e.g.
 downloadButtonType = {"css": "btn btn-primary", "text":"Export", "type":"xlsx"}
- `downloadComplete` (Bool | Real | String | Dict | Array; optional)
- `downloadReady` (Bool | Real | String | Dict | Array; optional)
- `groupClick` (Bool | Real | String | Dict | Array; optional)
- `groupContext` (Bool | Real | String | Dict | Array; optional)
- `groupDblClick` (Bool | Real | String | Dict | Array; optional)
- `groupDblTap` (Bool | Real | String | Dict | Array; optional)
- `groupTap` (Bool | Real | String | Dict | Array; optional)
- `groupTapHold` (Bool | Real | String | Dict | Array; optional)
- `groupVisibilityChanged` (Bool | Real | String | Dict | Array; optional)
- `headerClick` (Bool | Real | String | Dict | Array; optional)
- `headerContext` (Bool | Real | String | Dict | Array; optional)
- `headerDblClick` (Bool | Real | String | Dict | Array; optional)
- `headerDblTap` (Bool | Real | String | Dict | Array; optional)
- `headerTap` (Bool | Real | String | Dict | Array; optional)
- `headerTapHold` (Bool | Real | String | Dict | Array; optional)
- `htmlImported` (Bool | Real | String | Dict | Array; optional)
- `htmlImporting` (Bool | Real | String | Dict | Array; optional)
- `initialHeaderFilter` (Array; optional): initialHeaderFilter based on http://tabulator.info/docs/4.8/filter#header
can take array of filters
- `localized` (Bool | Real | String | Dict | Array; optional)
- `movableRowsReceived` (Bool | Real | String | Dict | Array; optional)
- `movableRowsReceivedFailed` (Bool | Real | String | Dict | Array; optional)
- `movableRowsReceivingStart` (Bool | Real | String | Dict | Array; optional)
- `movableRowsReceivingStop` (Bool | Real | String | Dict | Array; optional)
- `movableRowsSendingStart` (Bool | Real | String | Dict | Array; optional)
- `movableRowsSendingStop` (Bool | Real | String | Dict | Array; optional)
- `movableRowsSent` (Bool | Real | String | Dict | Array; optional)
- `movableRowsSentFailed` (Bool | Real | String | Dict | Array; optional)
- `multiRowsClicked` (Array; optional): multiRowsClicked, when multiple rows are clicked
- `options` (Dict; optional): Tabulator Options
- `pageLoaded` (Bool | Real | String | Dict | Array; optional)
- `renderComplete` (Bool | Real | String | Dict | Array; optional)
- `renderStarted` (Bool | Real | String | Dict | Array; optional)
- `rowAdded` (Bool | Real | String | Dict | Array; optional)
- `rowClick` (Bool | Real | String | Dict | Array; optional): standard props not used by dash-tabulator directly
can be used as part of custom javascript implementations
- `rowClicked` (Dict; optional): rowClick captures the row that was clicked on
- `rowContext` (Bool | Real | String | Dict | Array; optional)
- `rowDblClick` (Bool | Real | String | Dict | Array; optional)
- `rowDblTap` (Bool | Real | String | Dict | Array; optional)
- `rowDeleted` (Bool | Real | String | Dict | Array; optional)
- `rowDeselected` (Bool | Real | String | Dict | Array; optional)
- `rowMoved` (Bool | Real | String | Dict | Array; optional)
- `rowResized` (Bool | Real | String | Dict | Array; optional)
- `rowSelected` (Bool | Real | String | Dict | Array; optional)
- `rowSelectionChanged` (Bool | Real | String | Dict | Array; optional)
- `rowTap` (Bool | Real | String | Dict | Array; optional)
- `rowTapHold` (Bool | Real | String | Dict | Array; optional)
- `rowUpdated` (Bool | Real | String | Dict | Array; optional)
- `selectableCheck` (Bool | Real | String | Dict | Array; optional)
- `tableBuilding` (Bool | Real | String | Dict | Array; optional)
- `tableBuilt` (Bool | Real | String | Dict | Array; optional)
- `theme` (String; optional): theme
- `validationFailed` (Bool | Real | String | Dict | Array; optional)
"""
function dashtabulator(; kwargs...)
        available_props = Symbol[:id, :ajaxError, :ajaxRequesting, :ajaxResponse, :cellClick, :cellContext, :cellDblClick, :cellDblTap, :cellEditCancelled, :cellEdited, :cellEditing, :cellTap, :cellTapHold, :clearFilterButtonType, :clipboardCopied, :clipboardPasteError, :clipboardPasted, :columnMoved, :columnResized, :columnTitleChanged, :columnVisibilityChanged, :columns, :data, :dataChanged, :dataFiltered, :dataFiltering, :dataGrouped, :dataGrouping, :dataLoaded, :dataLoading, :dataSorted, :dataSorting, :downloadButtonType, :downloadComplete, :downloadReady, :groupClick, :groupContext, :groupDblClick, :groupDblTap, :groupTap, :groupTapHold, :groupVisibilityChanged, :headerClick, :headerContext, :headerDblClick, :headerDblTap, :headerTap, :headerTapHold, :htmlImported, :htmlImporting, :initialHeaderFilter, :localized, :movableRowsReceived, :movableRowsReceivedFailed, :movableRowsReceivingStart, :movableRowsReceivingStop, :movableRowsSendingStart, :movableRowsSendingStop, :movableRowsSent, :movableRowsSentFailed, :multiRowsClicked, :options, :pageLoaded, :renderComplete, :renderStarted, :rowAdded, :rowClick, :rowClicked, :rowContext, :rowDblClick, :rowDblTap, :rowDeleted, :rowDeselected, :rowMoved, :rowResized, :rowSelected, :rowSelectionChanged, :rowTap, :rowTapHold, :rowUpdated, :selectableCheck, :tableBuilding, :tableBuilt, :theme, :validationFailed]
        wild_props = Symbol[]
        return Component("dashtabulator", "DashTabulator", "dash_tabulator", available_props, wild_props; kwargs...)
end

