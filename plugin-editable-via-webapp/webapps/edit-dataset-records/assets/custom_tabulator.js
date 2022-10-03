filterFuncResultCount = 0
addEventListener('keyup', (event) => {filterFuncResultCount = 0});

window.myNamespace = Object.assign({}, window.myNamespace, {

    tabulator: {

        headerMenu: [
            {
                label:"Hide Column",
                action:function(e, column){
                    column.toggle(); // or hide()
                }
            },
            {
                label:"Group By",
                action:function(e, column){
                    column.getTable().setGroupBy(column.getField());
                }
            },
        ],

        // headerMenu: function() {
        //     var menu = [];
        //     var columns = this.getColumns();
        
        //     for(let column of columns){
        
        //         //create checkbox element using font awesome icons
        //         let icon = document.createElement("i");
        //         icon.classList.add("fas");
        //         icon.classList.add(column.isVisible() ? "fa-check-square" : "fa-square");
        
        //         //build label
        //         let label = document.createElement("span");
        //         let title = document.createElement("span");
        
        //         title.textContent = " " + column.getDefinition().title;
        
        //         label.appendChild(icon);
        //         label.appendChild(title);
        
        //         //create menu item
        //         menu.push({
        //             label:label,
        //             action:function(e){
        //                 //prevent menu closing
        //                 e.stopPropagation();
        
        //                 //toggle current column visibility
        //                 column.toggle();
        
        //                 //change menu item icon
        //                 if(column.isVisible()){
        //                     icon.classList.remove("fa-square");
        //                     icon.classList.add("fa-check-square");
        //                 }else{
        //                     icon.classList.remove("fa-check-square");
        //                     icon.classList.add("fa-square");
        //                 }
        //             }
        //         });
        //     }

        //    return menu;
        // },

        searchFunc: function (term, values) { //search for exact matches
            var matches = [];
            if (term && term.length>2) {
                values.forEach(function(value){
                    //value - one of the values from the value property
                    if(value.toString().startsWith(term)){
                        matches.push(value);
                    }
                });
            }
            return matches;
        },

        filterFunc: function (term, label, value, item) {
            if (filterFuncResultCount>=100) {
                return false;
            } else {
                if (term !== null) {
                    term = String(term).toLowerCase();
                    if (term.length>2 && label !== null && typeof label !== "undefined") {
                        label = String(label).toLowerCase();
                        if (label.startsWith(term)) {
                            filterFuncResultCount += 1
                            return true;
                        }
                    }
                }
                return false;
            }
        },
        
        itemFormatter: function (label, value, item, element) {
            //label - the text label for the item -> this would be the value of linked_ds_label
            //value - the value for the item -> this would be the value of linked_ds_key -> we don't display it
            //item - the original value object for the item
            //element - the DOM element for the item

            // TODO: loop over properties of `item`
            o = "<strong>" + label + "</strong><br/><div>"
            for (const key in item) { // the first two keys are for linked_ds_key and linked_ds_label
                if (key!="label" && key!="value") {
                    o += item[key] + " - "
                }
            }
            o = o.substring(0, o.length-3)
            o += "</div>"
            return o;
        },

        //custom max min filter function
        minMaxFilterFunction: function (headerValue, rowValue, rowData, filterParams) {
            //headerValue - the value of the header filter element
            //rowValue - the value of the column in this row
            //rowData - the data for the row being filtered
            //filterParams - params object passed to the headerFilterFuncParams property
            if(rowValue){
                if(headerValue.start != ""){
                    if(headerValue.end != ""){
                        return rowValue >= headerValue.start && rowValue <= headerValue.end;
                    }else{
                        return rowValue >= headerValue.start;
                    }
                }else{
                    if(headerValue.end != ""){
                        return rowValue <= headerValue.end;
                    }
                }
            }
            return true; //must return a boolean, true if it passes the filter.
        },

        minMaxFilterEditor: function(cell, onRendered, success, cancel, editorParams) {

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
        
            function buildValues(){
                success({
                    start:start.value,
                    end:end.value,
                });
            }
        
            function keypress(e){
                if(e.keyCode == 13){
                    buildValues();
                }
        
                if(e.keyCode == 27){
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
         }

    }

});
