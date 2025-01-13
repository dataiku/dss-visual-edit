import React from 'react';
import PropTypes from 'prop-types';
import { resolveProp } from 'dash-extensions';
import { TabulatorFull as Tabulator } from "tabulator-tables";
import "tabulator-tables/dist/css/tabulator.min.css";
import "tabulator-tables/dist/css/tabulator_semanticui.min.css";
import "../../../assets/custom_tabulator.js";
import "../../../assets/tabulator_dataiku.css";
import "../../../assets/jquery-3.5.1.min.js";
import "../../../assets/luxon.min.js";
import "../../../assets/semantic-ui-react.min.js";
import "../../../assets/semantic.min.css";

const plugin_version = "2.0.3";

/**
 * We define a function to hash a string using the MD5 algorithm.
 * This is used to hash the dataset name and column names before sending them to WT1.
 */

const crypto = require('crypto');

function md5(string) {
    return crypto.createHash('md5').update(string).digest('hex');
}

/**
 * We define a wrapper around the Tabulator library as a React component.
 * We also define the properties that can be passed to this component, their types, and default values.
 */

export default class DashTabulator extends React.Component {
    el = React.createRef(); // ref to the DOM element that will contain the table
    tabulator = null; // variable to hold the Tabulator instance

    /**
     * Create the Tabulator instance when the React component mounts.
     */
    componentDidMount() {
        const { id, datasetName, data, columns, groupBy, cellEdited } = this.props;

        /**
         * Resolve column properties as functions when relevant.
         */
        for (let i = 0; i < columns.length; i++) { // iterate over columns
            let column = columns[i];
            for (let property in column) { // iterate over column properties
                let value = column[property];
                if (value instanceof Object) {
                    // value could be an arrow function (e.g. when property is "headerFilter") or a nested object (e.g. when property is "editorParams")
                    column[property] = resolveProp(o, this);
                    if (!value.variable && !value.arrow) {
                        // value is a nested object and we iterate over its properties
                        for (let sub_property in value) {
                            let sub_value = value[sub_property]
                            if (sub_value instanceof Object) { // this is likely to be an arrow function (e.g. when property is "editorParams" and sub_property is "itemFormatter")
                                o[key2] = resolveProp(o2, this); // resolve as such
                            }
                        }
                    }
                }
            }
        }

        /**
         * Create the Tabulator instance:
         * Pass the DOM element that will contain the table.
         * Pass fixed data table options, and options from props.
         */
        this.tabulator = new Tabulator(this.el, {
            "datasetName": datasetName,
            "data": data,
            "columns": columns,
            "groupBy": groupBy,
            "reactiveData": true,

            // Fixed options
            "selectable": 1,
            "layout": "fitDataTable",
            "pagination": "local",
            "paginationSize": 20,
            "paginationSizeSelector": [10, 20, 50, 100],
            "movableColumns": true,
            "persistence": true,
            "footerElement": "<button class='tabulator-page' onclick='localStorage.clear(); window.location.reload();'>Reset View</button>"
        });

        /**
         * Tabulator event listener for cell editing
         */
        this.tabulator.on("cellEdited", (cell) => {
            var edited = new Object()
            edited.field = cell.getField()
            edited.type = cell.getColumn().getDefinition()["editor"]
            edited.initialValue = cell.getInitialValue()
            edited.oldValue = cell.getOldValue()
            edited.value = cell.getValue()
            edited.row = cell.getData()
            this.props.setProps({ cellEdited: edited })
            try {
                window.parent.WT1SVC.event("visualedit-edit-cell", {
                    "dataset_name_hash": md5(datasetName),
                    "column_name_hash": md5(edited.field),
                    "column_type": edited.type,
                    "plugin_version": plugin_version
                });
            } catch (e) { }
        })
    }

    /**
     * 
     * @param {*} props 
     */
    constructor(props) {
        super(props);
        this.ref = null;
    }

    /**
     * Update table data when component receives new props
     */
    render() {
        // Send event to parent window to log the display of the table
        try {
            window.parent.WT1SVC.event("visualedit-display-table", {
                "dataset_name_hash": md5(this.props.datasetName),
                // create columns_hashed as a copy of the columns array where each item's "field" property has been hashed and other properties have been kept as they were
                "rows_count": this.props.data.length,
                "columns_hashed": this.props.columns.map((item) => {
                    let item_hashed = Object.assign({}, item);
                    item_hashed["field"] = md5(item["field"]);
                    item_hashed["title"] = md5(item["title"]);
                    return item_hashed;
                }),
                "plugin_version": plugin_version
            })
        }
        catch (e) { }

        // Use the ref attribute to assign the element to this instance
        return (
            <div ref={el => (this.el = el)} />
        )
    }
}

DashTabulator.defaultProps = {
    data: [],
    datasetName: "",
    columns: [],
    groupBy: []
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
     * Name of the corresponding Dataiku dataset.
     */
    datasetName: PropTypes.string,

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
