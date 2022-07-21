import React, {Component} from 'react';
import PropTypes, { array } from 'prop-types';

//import Tabulator stylesheets
import "tabulator-tables/dist/css/tabulator.min.css";
import "tabulator-tables/dist/css/tabulator_semanticui.min.css";

import { ReactTabulator } from './react-tabulator/lib'
import {resolveProps, resolveProp} from 'dash-extensions'

export default class DashTabulator extends Component {
    constructor(props) {
        super(props);
        this.ref = null;
    }

    render() {
        console.log("Rendering!")

        const {id, data, setProps, columns, options, cellEdited} = this.props;
        
        // Interpret column formatters as function handles.
        // TODO: resolve any columns method
        for(let i=0; i < columns.length; i++){
            let header = columns[i];
            for (let key in header){ 
                let o = header[key];
                console.log(key);
                console.log(o);
                if (o instanceof Object) { 
                    header[key] = resolveProp(o, this);
                    if (!o.variable && !o.arrow) {
                        for (let key2 in o){
                            let o2 = o[key2]
                            console.log(key2);
                            console.log(o2);
                            if (o2 instanceof Object) { 
                                o[key2] = resolveProp(o2, this);
                            }
                        }
                    }
                }
            }
        }

        // check all options for a global windows function in the assets folder
        for (let key in options) {
            let o = options[key] 
            if (o instanceof Object) {
                options[key] = resolveProp(o, this)    
            }
        }

        try {
            window.parent.WT1SVC.event("lca-datatable-viewed");
        }
        catch (e) { }

        return (
            <div>
            <ReactTabulator
                onRef={(ref) => (this.ref = ref)}
                data={data}
                columns={columns}
                options={options}
                layout={"fitData"}
                theme={"semantic-ui/tabulator_semantic-ui"}
                cellEdited={(cell) => {
                    console.log("Cell edited!")
                    console.log(cell)
                    var edited = new Object() 
                    edited.column = cell.getField()
                    edited.initialValue = cell.getInitialValue()
                    edited.oldValue = cell.getOldValue()
                    edited.value = cell.getValue()
                    edited.row = cell.getData()
                    this.props.setProps({cellEdited: edited})
                    try {
                        window.parent.WT1SVC.event("lca-datatable-edited", {
                            "column_name": edited.column
                        });
                    } catch (e) { }
                }}
            />
            </div>
        );
    }
}

DashTabulator.defaultProps = {
    columns : [],
    data: []
};

DashTabulator.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * theme
     */
    theme: PropTypes.string,

    /**
     * A label that will be printed when this component is rendered.
     */
    columns: PropTypes.array,

    /**
     * The value displayed in the input.
     */
    data: PropTypes.array,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,

    /**
     * Tabulator Options
     */
    options: PropTypes.object,

    /**
     * cellEdited captures the cell that was clicked on
     */
    cellEdited: PropTypes.object,
};
