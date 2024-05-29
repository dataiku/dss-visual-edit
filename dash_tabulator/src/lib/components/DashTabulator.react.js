import React from 'react';
import PropTypes from 'prop-types';
import { resolveProp } from 'dash-extensions';
import { TabulatorFull as Tabulator } from "tabulator-tables"; //import Tabulator library
import "tabulator-tables/dist/css/tabulator.min.css";
import "tabulator-tables/dist/css/tabulator_semanticui.min.css";
import "../../../assets/custom_tabulator.js";
import "../../../assets/tabulator_dataiku.css";
import "../../../assets/jquery-3.5.1.min.js";
import "../../../assets/luxon.min.js";
import "../../../assets/semantic-ui-react.min.js";
import "../../../assets/semantic.min.css";

const crypto = require('crypto');

const plugin_version = "2.0.0";

function md5(string) {
    return crypto.createHash('md5').update(string).digest('hex');
}

export default class DashTabulator extends React.Component {
    el = React.createRef();
    tabulator = null; //variable to hold your table

    componentDidMount() {
        // Instantiate Tabulator when element is mounted

        const { id, datasetName, data, columns, groupBy, cellEdited } = this.props;

        // Interpret column formatters as function handles.
        for (let i = 0; i < columns.length; i++) {
            let header = columns[i];
            for (let key in header) {
                let o = header[key];
                if (o instanceof Object) {
                    header[key] = resolveProp(o, this);
                    if (!o.variable && !o.arrow) {
                        for (let key2 in o) {
                            let o2 = o[key2]
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
            "datasetName": datasetName,
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
            "footerElement": "<button class='tabulator-page' onclick='localStorage.clear(); window.location.reload();'>Reset View</button>"
        });

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

    constructor(props) {
        super(props);
        this.ref = null;
    }

    render() {
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

        // const {id, data, columns, groupBy, cellEdited} = this.props;
        // if (this.tabulator) this.tabulator.setData(data)

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
