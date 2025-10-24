var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

dagfuncs.dkuLinkedRecordsCellEditor = function(params) {
    const linkedDsName = params.colDef.linkedDatasetName;
    const url = `${window.location.href}lookup/${linkedDsName}`;

    const request = new XMLHttpRequest();
    request.open("GET", url, false);
    request.send(null);

    repeatedFetch(params.node.id, "");

    return {
        values: JSON.parse(request.responseText),
        allowTyping: true,
        filterList: true,
        highlightMatch: true,
        searchType: "matchAny"
    }
}

async function fetchMatchingValuesAndUpdateEditorValues(cb, nodeId, previousSearchTerm) {
    const gridApi = await dash_ag_grid.getApiAsync("datatable");
    const cellEditors = gridApi.getCellEditorInstances();
    const editor = cellEditors.find(inst => inst.params && inst.params.node && inst.params.node.id === nodeId && inst.richSelect);
    if (editor) {
        const currentSearchTerm = editor.richSelect.searchString;
        if (currentSearchTerm !== previousSearchTerm) {
            const response = await fetch(`${window.location.href}lookup/${editor.params.colDef.linkedDatasetName}?term=${encodeURIComponent(editor.richSelect.searchString)}`)
            const newValues = await response.json()
            editor.richSelect.setValueList({ valueList: [...newValues], refresh: true });
            editor.richSelect.values = [...newValues]
            editor.richSelect.searchTextFromString(currentSearchTerm)
        }
        
        return true
    }

    return false
}

const debounceTimers = {};

function repeatedFetch(nodeId, previousSearchTerm) {
    if (debounceTimers[nodeId]) {
        clearTimeout(debounceTimers[nodeId]);
    }
    debounceTimers[nodeId] = setTimeout(async () => {
        if (await fetchMatchingValuesAndUpdateEditorValues(repeatedFetch, nodeId, previousSearchTerm)) {
            repeatedFetch(nodeId, previousSearchTerm);
        }
    }, 200)
}