import React from 'react';
import PropTypes from 'prop-types';
import {resolveProp} from 'dash-extensions';
import {TabulatorFull as Tabulator} from "tabulator-tables"; //import Tabulator library
import "tabulator-tables/dist/css/tabulator.min.css";
import "tabulator-tables/dist/css/tabulator_semanticui.min.css";

export default class DashTabulator extends React.Component {
    el = React.createRef();
    tabulator = null; //variable to hold your table

    componentDidMount() {
        // Instantiate Tabulator when element is mounted

        const {id, data, columns, groupBy, cellEdited} = this.props;

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
            "selectable": true,
            "layout": "fitDataTable",
            "renderHorizontal": "virtual",
            "pagination": "local",
            "paginationSize": 20,
            "paginationSizeSelector": [10, 20, 50, 100],
            "movableColumns": true,
            "persistence": true,
            "footerElement": "<button class='tabulator-page' onclick='localStorage.clear(); window.location.reload();'>Reset View</button>"
        })

        this.tabulator.on("cellEdited", (cell) => { 
            console.log("Cell edited!")
            console.log('cellEdited', cell)
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
        })

        dropdownValues = []
        columns.forEach((col) => {
            dropdownValues.push({"value": col.get("field"), "name": col.get("field")})
        });
        $("#bulk-edit-modal-column-name")
            .dropdown({ values: dropdownValues })
        ;

        $("#bulk-edit-show-button").on("click", function () {
            $('#bulk-edit-modal')
                .modal('show')
            ;
        });

        $("#bulk-edit-modal-ok").on("click", function () {
            console.log("Bulk editing!")
            var rows = table.getSelectedRows()
            colName = $("#bulk-edit-modal-column-name").dropdown("get value")
            val = $("#bulk-edit-modal-value")[0].value
            table.blockRedraw()
            d = {}
            d[colName] = val
            rows.forEach((row) => {
                row.update(d)
            })
            table.restoreRedraw()
        })
    }

    constructor(props) {
        super(props);
        this.ref = null;
    }

    render() {
        console.log("Rendering!")
        try { window.parent.WT1SVC.event("lca-datatable-viewed"); }
        catch (e) { }

        // const {id, data, columns, groupBy, cellEdited} = this.props;
        // if (this.tabulator) this.tabulator.setData(data)

        return (
            <div>
                <button class="ui button" id="bulk-edit-show-button">Edit Selected Rows</button>
                <div class="ui tiny modal" id="bulk-edit-modal">
                    <i class="close icon"></i>
                    <div class="header">Edit Selected Rows</div>
                    <div class="content">
                        <form class="ui form">
                            <div class="field">
                                <label>Column to edit</label>
                                <div class="ui dropdown" id="bulk-edit-modal-column-name">
                                    <div class="text"></div>
                                    <i class="dropdown icon"></i>
                                </div>
                            </div>
                            <div class="field">
                                <label>Value to assign</label>
                                <input type="text" id="bulk-edit-modal-value" placeholder=""/>
                            </div>
                            <div class="actions">
                                <div class="ui approve button" id="bulk-edit-modal-ok">OK</div>
                            </div>
                        </form>
                    </div>
                </div>
                <div ref={el => (this.el = el)} />
            </div>
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
