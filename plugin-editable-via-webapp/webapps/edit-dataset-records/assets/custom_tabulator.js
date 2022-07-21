window.myNamespace = Object.assign({}, window.myNamespace, {

    tabulator: {

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
            if (term !== null) {
                term = String(term).toLowerCase();
                if (term.length>2 && label !== null && typeof label !== "undefined") {
                    label = String(label).toLowerCase();
                    if (label.startsWith(term)) {
                        return true;
                    }
                }
            }
            return false;
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
