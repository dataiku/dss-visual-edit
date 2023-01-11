import React from 'react';
import PropTypes from 'prop-types';
import {resolveProp} from 'dash-extensions';
import {TabulatorFull as Tabulator, EditModule} from "tabulator-tables"; //import Tabulator library
import "tabulator-tables/dist/css/tabulator.min.css";
import "tabulator-tables/dist/css/tabulator_semanticui.min.css";




export default class DashTabulator extends React.Component {
    el = React.createRef();
    tabulator = null; //variable to hold your table

    bulkEditEditor(cell, onRendered, success, cancel, editorParams) {
        const editorByColumnName = editorParams.editorByColumnName;
        const cellRow = cell.getRow();
        const editedColumn = cellRow.getData().field;
        const editedColumnEditor = editorByColumnName[editedColumn]
        const editor = EditModule.editors[editedColumnEditor.editor]
        const realEditorParams = editedColumnEditor.editorParams
        return editor.call(this, cell, onRendered, success, cancel, realEditorParams)
    };

    getProcessedColumns() {
        const propsColumns = this.props.columns;
        const processedColumns = propsColumns.map((c) => {
            if (c.editor === "customColumnBased") {
                c.editor = this.bulkEditEditor
            }
            return c
        })
        return processedColumns
    }

    resolvePropRec(prop) {
        if (!(prop instanceof Object)) {
            return resolveProp(prop, this);
        }
        
        for (let key in prop){
            prop[key] = resolveProp(this.resolvePropRec(prop[key]));
        }
        return prop
    }

    componentDidMount() {
        // Instantiate Tabulator when element is mounted

        const {id, data, columns, groupBy, cellEdited, multiRowsClicked} = this.props;
        this.resolvePropRec(columns);

        this.tabulator = new Tabulator(this.el, {
            "data": data,
            "reactiveData": true,
            "columns": this.getProcessedColumns(),
            "groupBy": groupBy,
            "layout": "fitDataTable",
            "pagination": "local",
            "paginationSize": 20,
            "paginationSizeSelector": [10, 20, 50, 100],
            "movableColumns": true,
            "persistence": true,
            "footerElement":"<button class='tabulator-page' onclick='localStorage.clear(); window.location.reload();'>Reset View</button>"
        });

        this.tabulator.on("cellEdited", (cell) => {
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

        this.tabulator.on("rowSelectionChanged", (data, rows) => {
            this.props.setProps({multiRowsClicked: data})

        })
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.props.data && prevProps.data !== this.props.data) {
            this.tabulator.replaceData(this.props.data);
        }
    }

    constructor(props) {
        super(props);
        this.ref = null;
    }

    render() {
        try { window.parent.WT1SVC.event("lca-datatable-viewed"); }
        catch (e) { }

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

    /**
     * multiRowsClicked, when multiple rows are clicked
     */
    multiRowsClicked: PropTypes.array,
};
