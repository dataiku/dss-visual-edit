import React from 'react';
import PropTypes from 'prop-types';
import {resolveProp} from 'dash-extensions';
import {TabulatorFull as Tabulator} from "tabulator-tables"; //import Tabulator library
import "tabulator-tables/dist/css/tabulator.min.css";
import "tabulator-tables/dist/css/tabulator_semanticui.min.css";
import "../../../assets/custom_tabulator.js";
import "../../../assets/tabulator_dataiku.css";

const crypto = require('crypto');

function md5(string) {
    return crypto.createHash('md5').update(string).digest('hex');
}

export default class DashTabulator extends React.Component {
    el = React.createRef();
    tabulator = null; //variable to hold your table

    componentDidMount() {
        // Instantiate Tabulator when element is mounted

        const {id, dataset_name, data, columns, groupBy, cellEdited} = this.props;

        // Interpret column formatters as function handles.
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

        this.tabulator = new Tabulator(this.el, {
            "data": data,
            "reactiveData": true,
            "columns": columns,
            "groupBy": groupBy,
            "selectable": 1,
            "layout": "fitDataTable",
            "pagination": "local",
            "paginationSize": 20,
            "paginationSizeSelector": [10, 20, 50, 100],
            "movableColumns": true,
            "persistence": true,
            "footerElement":"<button class='tabulator-page' onclick='localStorage.clear(); window.location.reload();'>Reset View</button>"
        });

        this.tabulator.on("cellEdited", (cell) => { 
            console.log("Cell edited!")
            console.log('cellEdited', cell)
            var edited = new Object() 
            edited.field = cell.getField()
            edited.type = cell.getColumn().getDefinition()["editor"]
            edited.initialValue = cell.getInitialValue()
            edited.oldValue = cell.getOldValue()
            edited.value = cell.getValue()
            edited.row = cell.getData()
            this.props.setProps({cellEdited: edited})
            try {
                window.parent.WT1SVC.event("lca-datatable-edited", {
                    "dataset_name_hash": md5(dataset_name),
                    "column_name_hash": md5(edited.field),
                    "column_type": edited.type
                });
            } catch (e) { }
        })
    }

    constructor(props) {
        super(props);
        this.ref = null;
    }

    render() {
        console.log("Rendering!")
        try {
            window.parent.WT1SVC.event("lca-datatable-viewed", {
                "dataset_name_hash": md5(this.props.dataset_name),
                // create columns_hashed as a copy of the columns array where each item's "field" property has been hashed and other properties have been kept as they were
                "rows_count": this.props.data.length,
                "columns_hashed": this.props.columns.map((item) => {
                    let item_hashed = Object.assign({}, item);
                    item_hashed["field"] = md5(item["field"]);
                    item_hashed["title"] = md5(item["title"]);
                    return item_hashed;
                })
            })
        }
        catch (e) { }

        // const {id, data, columns, groupBy, cellEdited} = this.props;
        // if (this.tabulator) this.tabulator.setData(data)

        return (
            <div ref={el => (this.el = el)} />
        )
    }
}

DashTabulator.defaultProps = {
    data: [],
    columns : [],
    groupBy : []
};

DashTabulator.propTypes = {
    /**
     * ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Data to display in the table.
     */
     data: PropTypes.array,

    /**
     * Column definitions.
     */
    columns: PropTypes.array,

    /**
     * Columns to group by.
     */
     groupBy: PropTypes.array,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,

    /**
     * cellEdited captures the cell that was clicked on
     */
    cellEdited: PropTypes.object,
};
