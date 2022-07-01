window.myNamespace = Object.assign({}, window.myNamespace, {

    tabulator: {

        // TODO: min-max filter
        searchFunc: function (term, values) { //search for exact matches
            var matches = [];
    
            values.forEach(function(value){
                //value - one of the values from the value property
    
                if(value === term){
                    matches.push(value);
                }
            });
    
            return matches;
        },

    }

});
