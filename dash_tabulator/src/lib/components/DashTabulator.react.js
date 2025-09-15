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
import { extractFilterValues } from '../helpers/dashboardFilters.js'

/**
 * Hash a string using MD5.
 * This is used to hash the dataset name and column names before sending them to WT1.
 * @param {string} string
 * @returns {string}
 */
const crypto = require('crypto');
const plugin_version = "2.0.8";
function md5(string) {
    return crypto.createHash('md5').update(string).digest('hex');
}

/**
 * DashTabulator is a wrapper for a data table library (e.g. Tabulator).
 * All table operations are abstracted for easier migration to another library.
 */
export default class DashTabulator extends React.Component {
    el = React.createRef(); // ref to the DOM element that will contain the table
    tableInstance = null; // holds the table instance (Tabulator or other)

    constructor(props) {
        super(props);
    }

    /**
     * Initialize the data table instance.
     * This is the only place Tabulator-specific code should exist.
     */
    initTable() {
        const { datasetName, data, columns, groupBy } = this.props;
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
         * Create the data table instance:
         * Pass the DOM element that will contain the table.
         * Pass fixed data table options, and options from props.
         */
        this.tableInstance = new Tabulator(this.el, this.getTableOptions(datasetName, data, columns, groupBy));
        this.tableInstance.on("cellEdited", this.handleCellEdited);
    }

    /**
     * Return table options for Tabulator.
     * Replace this method when switching to another table library.
     */
    getTableOptions(datasetName, data, columns, groupBy) {
        return {
            datasetName,
            data,
            columns,
            groupBy,
            reactiveData: true,
            selectable: 1,
            layout: "fitDataTable",
            pagination: "local",
            paginationSize: 20,
            paginationSizeSelector: [10, 20, 50, 100],
            movableColumns: true,
            persistence: true,
            footerElement: "<button class='tabulator-page' onclick='localStorage.clear(); window.location.reload();'>Reset View</button>"
        };
    }

    /**
     * Destroy the table instance.
     */
    destroyTable() {
        if (this.tableInstance) {
            this.tableInstance.destroy();
            this.tableInstance = null;
        }
    }

    /**
     * Set table data.
     * @param {Array} data
     */
    setTableData(data) {
        if (this.tableInstance) {
            this.tableInstance.replaceData(data);
        }
    }

    /**
     * Set table columns.
     * @param {Array} columns
     */
    setTableColumns(columns) {
        if (this.tableInstance) {
            this.tableInstance.setColumns(columns);
        }
    }

    /**
     * Set table filters.
     * @param {Array} filters
     * @param {String} type
     */
    setTableFilter(filters, type) {
        if (this.tableInstance) {
            this.tableInstance.setFilter(filters, type);
        }
    }

    /**
     * Clear all table filters.
     */
    clearTableFilter() {
        if (this.tableInstance) {
            this.tableInstance.clearFilter();
        }
    }

    /**
     * Handle cell edit event.
     * @param {Object} cell
     */
    handleCellEdited = (cell) => {
        const edited = {
            field: cell.getField(),
            type: cell.getColumn().getDefinition()["editor"],
            initialValue: cell.getInitialValue(),
            oldValue: cell.getOldValue(),
            value: cell.getValue(),
            row: cell.getData()
        };
        this.props.setProps({ cellEdited: edited });
        try {
            window.parent.WT1SVC.event("visualedit-edit-cell", {
                "dataset_name_hash": md5(this.props.datasetName),
                "column_name_hash": md5(edited.field),
                "column_type": edited.type,
                "plugin_version": plugin_version
            });
        } catch (e) { }
    }

    /**
     * Handle external filter events.
     * @param {Event} event
     */
    handleFilterEvent = (event) => {
        const data = event.data;
        if (!data || data.type !== 'filters') return;

        const filters = data.filters;
        if (filters.length === 0) {
            this.clearTableFilter();
            return;
        }

        const filter = filters[0];
        if (!filter.active || filter.filterType !== 'ALPHANUM_FACET') {
            this.clearTableFilter();
            return;
        }

        const columnFields = this.props.columns.map(col => col.field);
        if (!columnFields.includes(filter.column)) {
            return;
        }

        const { includedValues, excludedValues } = extractFilterValues(filter);
        if (includedValues.length > 0) {
            const includeFilters = includedValues.map(value => ({
                field: filter.column,
                type: "=",
                value: value
            }));
            this.setTableFilter(includeFilters, "OR");
        } else if (excludedValues.length > 0) {
            const excludeFilters = excludedValues.map(value => ({
                field: filter.column,
                type: "!=",
                value: value
            }));
            this.setTableFilter(excludeFilters);
        } else {
            this.clearTableFilter();
        }
    }

    /**
     * React lifecycle: componentDidMount
     */
    componentDidMount() {
        this.initTable();
        window.addEventListener('message', this.handleFilterEvent);
    }

    /**
     * React lifecycle: componentWillUnmount
     */
    componentWillUnmount() {
        window.removeEventListener('message', this.handleFilterEvent);
        this.destroyTable();
    }

    /**
     * React lifecycle: componentDidUpdate
     * Update table data/columns if props change.
     */
    componentDidUpdate(prevProps) {
        if (prevProps.data !== this.props.data) {
            this.setTableData(this.props.data);
        }
        if (prevProps.columns !== this.props.columns) {
            this.setTableColumns(this.props.columns);
        }
    }

    /**
     * Render the table container. This is run when the component receives new props.
     */
    render() {
        // Log display event
        try {
            window.parent.WT1SVC.event("visualedit-display-table", {
                "dataset_name_hash": md5(this.props.datasetName),
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
