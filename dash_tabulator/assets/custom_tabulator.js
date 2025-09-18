// Custom Formatters, Filter Editors and Functions, and Header Menu options for columns in Tabulator tables.
// Can be referenced in column definitions passed to the Dash Tabulator component.

window.myNamespace = Object.assign({}, window.myNamespace, {

    tabulator: {

        //
        // Header Menu options
        //
        // "Hide" and "Group by" (right-click on column header)

        labels: {},
        columnHeaderMenu: [
            {
                label: "Hide Column",
                action: function (e, column) {
                    column.toggle(); // or hide()
                }
            },
            {
                label: "Group By",
                action: function (e, column) {
                    column.getTable().setGroupBy(column.getField());
                }
            },
        ],

        //
        // Formatters
        // 

        // Rich formatting of items in `list` editor: when items are objects with multiple properties, show the label in bold and other properties below it.
        listItemRichFormatter: function (label, value, item, element) {
            //label - the text label for the item -> this would be the value of the linked dataset's label column
            //value - the value for the item -> this would be the value of the linked dataset's primary key -> we don't display it
            //item - the original value object for the item
            //element - the DOM element for the item

            o = "<strong>" + label + "</strong><br/><div>"
            for (const key in item) { // the first two keys are for linked_ds_key and linked_ds_label
                if (key != "label" && key != "value") {
                    o += item[key] + " - "
                }
            }
            o = o.substring(0, o.length - 3)
            o += "</div>"
            return o;
        },

        //
        // Filter Editors and Functions
        //

        //// Min/Max for numerical columns
        ////

        ////// Editor: widget with one input for min value and one input for max value
        minMaxFilterEditor: function (cell, onRendered, success, cancel, editorParams) {

            var end;

            var container = document.createElement("span");

            //create and style inputs
            var start = document.createElement("input");
            start.setAttribute("type", "number");
            start.setAttribute("placeholder", "Min");
            start.setAttribute("min", 0);
            start.setAttribute("max", 100);
            start.style.padding = "4px";
            start.style.width = "50%";
            start.style.boxSizing = "border-box";

            start.value = cell.getValue();

            function buildValues() {
                success({
                    start: start.value,
                    end: end.value,
                });
            }

            function keypress(e) {
                if (e.keyCode == 13) {
                    buildValues();
                }

                if (e.keyCode == 27) {
                    cancel();
                }
            }

            end = start.cloneNode();
            end.setAttribute("placeholder", "Max");

            start.addEventListener("change", buildValues);
            start.addEventListener("blur", buildValues);
            start.addEventListener("keydown", keypress);

            end.addEventListener("change", buildValues);
            end.addEventListener("blur", buildValues);
            end.addEventListener("keydown", keypress);


            container.appendChild(start);
            container.appendChild(end);

            return container;
        },

        ////// Filter function: filters rows to those with values between min and max (if set)
        minMaxFilterFunction: function (headerValue, rowValue, rowData, filterParams) {
            // headerValue - the value of the header filter element
            // rowValue - the value of the column in this row
            // rowData - the data for the row being filtered
            // filterParams - params object passed to the headerFilterFuncParams property

            // No filter set, all values pass.
            if (headerValue.start === "" && headerValue.end === "") {
                return true
            }

            // Filter set, empty or NaN values fail.
            if (rowValue == null || rowValue === "" || isNaN(Number(rowValue))) {
                return false;
            }

            if (headerValue.start != "") {
                if (headerValue.end != "") {
                    return rowValue >= headerValue.start && rowValue <= headerValue.end;
                } else {
                    return rowValue >= headerValue.start;
                }
            } else {
                if (headerValue.end != "") {
                    return rowValue <= headerValue.end;
                }
            }
        },

    }

});
