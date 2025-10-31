webpackHotUpdatedash_tabulator("main",{

/***/ "./src/lib/components/DashTabulator.react.js":
/*!***************************************************!*\
  !*** ./src/lib/components/DashTabulator.react.js ***!
  \***************************************************/
/*! exports provided: default */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "default", function() { return DashTabulator; });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "./node_modules/react/index.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var prop_types__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! prop-types */ "./node_modules/prop-types/index.js");
/* harmony import */ var prop_types__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(prop_types__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var dash_extensions__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! dash-extensions */ "./node_modules/dash-extensions/index.js");
/* harmony import */ var tabulator_tables__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! tabulator-tables */ "./node_modules/tabulator-tables/dist/js/tabulator_esm.js");
/* harmony import */ var tabulator_tables_dist_css_tabulator_min_css__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! tabulator-tables/dist/css/tabulator.min.css */ "./node_modules/tabulator-tables/dist/css/tabulator.min.css");
/* harmony import */ var tabulator_tables_dist_css_tabulator_min_css__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(tabulator_tables_dist_css_tabulator_min_css__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var tabulator_tables_dist_css_tabulator_semanticui_min_css__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! tabulator-tables/dist/css/tabulator_semanticui.min.css */ "./node_modules/tabulator-tables/dist/css/tabulator_semanticui.min.css");
/* harmony import */ var tabulator_tables_dist_css_tabulator_semanticui_min_css__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(tabulator_tables_dist_css_tabulator_semanticui_min_css__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _assets_custom_tabulator_js__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../../../assets/custom_tabulator.js */ "./assets/custom_tabulator.js");
/* harmony import */ var _assets_custom_tabulator_js__WEBPACK_IMPORTED_MODULE_6___default = /*#__PURE__*/__webpack_require__.n(_assets_custom_tabulator_js__WEBPACK_IMPORTED_MODULE_6__);
/* harmony import */ var _assets_tabulator_dataiku_css__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ../../../assets/tabulator_dataiku.css */ "./assets/tabulator_dataiku.css");
/* harmony import */ var _assets_tabulator_dataiku_css__WEBPACK_IMPORTED_MODULE_7___default = /*#__PURE__*/__webpack_require__.n(_assets_tabulator_dataiku_css__WEBPACK_IMPORTED_MODULE_7__);
/* harmony import */ var _assets_jquery_3_5_1_min_js__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ../../../assets/jquery-3.5.1.min.js */ "./assets/jquery-3.5.1.min.js");
/* harmony import */ var _assets_jquery_3_5_1_min_js__WEBPACK_IMPORTED_MODULE_8___default = /*#__PURE__*/__webpack_require__.n(_assets_jquery_3_5_1_min_js__WEBPACK_IMPORTED_MODULE_8__);
/* harmony import */ var _assets_luxon_min_js__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ../../../assets/luxon.min.js */ "./assets/luxon.min.js");
/* harmony import */ var _assets_luxon_min_js__WEBPACK_IMPORTED_MODULE_9___default = /*#__PURE__*/__webpack_require__.n(_assets_luxon_min_js__WEBPACK_IMPORTED_MODULE_9__);
/* harmony import */ var _assets_semantic_ui_react_min_js__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ../../../assets/semantic-ui-react.min.js */ "./assets/semantic-ui-react.min.js");
/* harmony import */ var _assets_semantic_ui_react_min_js__WEBPACK_IMPORTED_MODULE_10___default = /*#__PURE__*/__webpack_require__.n(_assets_semantic_ui_react_min_js__WEBPACK_IMPORTED_MODULE_10__);
/* harmony import */ var _assets_semantic_min_css__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ../../../assets/semantic.min.css */ "./assets/semantic.min.css");
/* harmony import */ var _assets_semantic_min_css__WEBPACK_IMPORTED_MODULE_11___default = /*#__PURE__*/__webpack_require__.n(_assets_semantic_min_css__WEBPACK_IMPORTED_MODULE_11__);
function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _classCallCheck(a, n) { if (!(a instanceof n)) throw new TypeError("Cannot call a class as a function"); }
function _defineProperties(e, r) { for (var t = 0; t < r.length; t++) { var o = r[t]; o.enumerable = o.enumerable || !1, o.configurable = !0, "value" in o && (o.writable = !0), Object.defineProperty(e, _toPropertyKey(o.key), o); } }
function _createClass(e, r, t) { return r && _defineProperties(e.prototype, r), t && _defineProperties(e, t), Object.defineProperty(e, "prototype", { writable: !1 }), e; }
function _callSuper(t, o, e) { return o = _getPrototypeOf(o), _possibleConstructorReturn(t, _isNativeReflectConstruct() ? Reflect.construct(o, e || [], _getPrototypeOf(t).constructor) : o.apply(t, e)); }
function _possibleConstructorReturn(t, e) { if (e && ("object" == _typeof(e) || "function" == typeof e)) return e; if (void 0 !== e) throw new TypeError("Derived constructors may only return object or undefined"); return _assertThisInitialized(t); }
function _assertThisInitialized(e) { if (void 0 === e) throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); return e; }
function _isNativeReflectConstruct() { try { var t = !Boolean.prototype.valueOf.call(Reflect.construct(Boolean, [], function () {})); } catch (t) {} return (_isNativeReflectConstruct = function _isNativeReflectConstruct() { return !!t; })(); }
function _getPrototypeOf(t) { return _getPrototypeOf = Object.setPrototypeOf ? Object.getPrototypeOf.bind() : function (t) { return t.__proto__ || Object.getPrototypeOf(t); }, _getPrototypeOf(t); }
function _inherits(t, e) { if ("function" != typeof e && null !== e) throw new TypeError("Super expression must either be null or a function"); t.prototype = Object.create(e && e.prototype, { constructor: { value: t, writable: !0, configurable: !0 } }), Object.defineProperty(t, "prototype", { writable: !1 }), e && _setPrototypeOf(t, e); }
function _setPrototypeOf(t, e) { return _setPrototypeOf = Object.setPrototypeOf ? Object.setPrototypeOf.bind() : function (t, e) { return t.__proto__ = e, t; }, _setPrototypeOf(t, e); }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }



 //import Tabulator library








var crypto = __webpack_require__(/*! crypto */ "./node_modules/crypto-browserify/index.js");
var plugin_version = "2.0.2";
function md5(string) {
  return crypto.createHash('md5').update(string).digest('hex');
}
var DashTabulator = /*#__PURE__*/function (_React$Component) {
  function DashTabulator(props) {
    var _this;
    _classCallCheck(this, DashTabulator);
    _this = _callSuper(this, DashTabulator, [props]);
    _defineProperty(_this, "el", /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default.a.createRef());
    _defineProperty(_this, "tabulator", null);
    _this.ref = null;
    return _this;
  }
  _inherits(DashTabulator, _React$Component);
  return _createClass(DashTabulator, [{
    key: "componentDidMount",
    value:
    //variable to hold your table

    function componentDidMount() {
      var _this2 = this;
      // Instantiate Tabulator when element is mounted

      var _this$props = this.props,
        id = _this$props.id,
        datasetName = _this$props.datasetName,
        data = _this$props.data,
        columns = _this$props.columns,
        groupBy = _this$props.groupBy,
        cellEdited = _this$props.cellEdited;

      // Interpret column formatters as function handles.
      for (var i = 0; i < columns.length; i++) {
        var header = columns[i];
        for (var key in header) {
          var o = header[key];
          if (o instanceof Object) {
            header[key] = Object(dash_extensions__WEBPACK_IMPORTED_MODULE_2__["resolveProp"])(o, this);
            if (!o.variable && !o.arrow) {
              for (var key2 in o) {
                var o2 = o[key2];
                if (o2 instanceof Object) {
                  o[key2] = Object(dash_extensions__WEBPACK_IMPORTED_MODULE_2__["resolveProp"])(o2, this);
                }
              }
            }
          }
        }
      }
      this.tabulator = new tabulator_tables__WEBPACK_IMPORTED_MODULE_3__["TabulatorFull"](this.el, {
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
      this.tabulator.on("cellEdited", function (cell) {
        var edited = new Object();
        edited.field = cell.getField();
        edited.type = cell.getColumn().getDefinition()["editor"];
        edited.initialValue = cell.getInitialValue();
        edited.oldValue = cell.getOldValue();
        edited.value = cell.getValue();
        edited.row = cell.getData();
        _this2.props.setProps({
          cellEdited: edited
        });
        try {
          window.parent.WT1SVC.event("visualedit-edit-cell", {
            "dataset_name_hash": md5(datasetName),
            "column_name_hash": md5(edited.field),
            "column_type": edited.type,
            "plugin_version": plugin_version
          });
        } catch (e) {}
      });
      window.addEventListener('message', function (event) {
        var data = event.data;
        if (data && data.type === 'filters' && data.filters.length > 0) {
          filter = data.filters[0];
          filterType = filter.filterType;
          filterColumn = filter.column;
          if (filterType === 'NUMERICAL_FACET') {
            filterMinValue = filter.minValue;
            filterMaxValue = filter.maxValue;
            console.log(filterMinValue + " <= " + filterColumn);
            this.tabulator.setFilter(filterColumn, ">=", filterMinValue);
          }
        }
      });
    }
  }, {
    key: "render",
    value: function render() {
      var _this3 = this;
      try {
        window.parent.WT1SVC.event("visualedit-display-table", {
          "dataset_name_hash": md5(this.props.datasetName),
          // create columns_hashed as a copy of the columns array where each item's "field" property has been hashed and other properties have been kept as they were
          "rows_count": this.props.data.length,
          "columns_hashed": this.props.columns.map(function (item) {
            var item_hashed = Object.assign({}, item);
            item_hashed["field"] = md5(item["field"]);
            item_hashed["title"] = md5(item["title"]);
            return item_hashed;
          }),
          "plugin_version": plugin_version
        });
      } catch (e) {}

      // const {id, data, columns, groupBy, cellEdited} = this.props;
      // if (this.tabulator) this.tabulator.setData(data)

      return /*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("div", {
        ref: function ref(el) {
          return _this3.el = el;
        }
      });
    }
  }]);
}(react__WEBPACK_IMPORTED_MODULE_0___default.a.Component);

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
  id: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.string,
  /**
   * Data to display in the table.
   */
  data: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.array,
  /**
   * Column definitions.
   */
  columns: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.array,
  /**
   * Name of the corresponding Dataiku dataset.
   */
  datasetName: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.string,
  /**
   * Columns to group by.
   */
  groupBy: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.array,
  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.func,
  /**
   * cellEdited captures the cell that was clicked on
   */
  cellEdited: prop_types__WEBPACK_IMPORTED_MODULE_1___default.a.object
};

/***/ })

})
//# sourceMappingURL=22eeef5-main-wps-hmr.js.map
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IiIsImZpbGUiOiIyMmVlZWY1LW1haW4td3BzLWhtci5qcyIsInNvdXJjZVJvb3QiOiIifQ==