var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

dagfuncs.visualEditGetLinkedRecords = function(params) {
    // debugger;
    // return { values: ['English', 'Spanish', 'French', 'Portuguese', '(other)']};
    const linkedDsName = params.colDef.linkedDatasetName;
    const url = `${window.location.href}lookup/${linkedDsName}`;

    const request = new XMLHttpRequest();
    request.open("GET", url, false);
    request.send(null);

    console.log(request.responseText)

    return {
        values: JSON.parse(request.responseText),
        allowTyping: true,
        filterList: true,
        highlightMatch: true,
        searchType: "matchAny"
    }
}
// const json = await result.json();

// console.log("Fetched linked records:", json);

// debugger;

// return {
//     "values": json,
//     // "allowTyping": true,
//     // "filterList": true,
//     // "highlightMatch": true
// }
// return new Promise((resolve) => {
//     setTimeout(() => resolve(['English', 'Spanish', 'French', 'Portuguese', '(other)']), 1000);
// });