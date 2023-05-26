from pandas import DataFrame
from dataiku import Dataset
from dash_extensions.javascript import Namespace
from commons import get_values_from_linked_df
import logging
from dash_extensions.javascript import assign

# used to reference javascript functions in custom_tabulator.js
__ns__ = Namespace("myNamespace", "tabulator")


def __get_column_tabulator_type__(ees, col_name):
    # Determine column type as string, boolean, boolean_tick, or number
    # - based on the type given in editschema_manual, if any
    # - the dataset's schema, otherwise
    ###

    t_type = "string"  # default type
    if not ees.editschema_manual_df.empty and "type" in ees.editschema_manual_df.columns and col_name in ees.editschema_manual_df.index:
        editschema_manual_type = ees.editschema_manual_df.loc[col_name, "type"]
    else:
        editschema_manual_type = None

    # this tests that 1) editschema_manual_type isn't None, and 2) it isn't a nan
    if editschema_manual_type and editschema_manual_type == editschema_manual_type:
        t_type = editschema_manual_type
    else:
        schema_df = DataFrame(data=ees.schema_columns).set_index("name")
        if "meaning" in schema_df.columns.to_list():
            schema_meaning = schema_df.loc[col_name, "meaning"]
        else:
            schema_meaning = None
        # If a meaning has been defined, we use it to infer t_type
        if schema_meaning and schema_meaning == schema_meaning:
            if schema_meaning == "Boolean":
                t_type = "boolean"
            if schema_meaning == "DoubleMeaning" or schema_meaning == "LongMeaning" or schema_meaning == "IntMeaning":
                t_type = "number"
            if schema_meaning == "Date":
                t_type = "date"
        else:
            # type coming from schema
            schema_type = schema_df.loc[col_name, "type"]
            if schema_type == "boolean":
                t_type = "boolean"
            if schema_type in ["tinyint", "smallint", "int", "bigint", "float", "double"]:
                t_type = "number"
            if schema_type == "date":
                t_type = "date"

    return t_type


def __get_column_tabulator_formatter__(t_type):
    # IDEA: improve this code with a dict to do matching (instead of if/else)?
    t_col = {}
    if t_type == "boolean":
        t_col["formatter"] = "tickCross"
        t_col["formatterParams"] = {"allowEmpty": True}
        t_col["hozAlign"] = "center"
        t_col["headerFilterParams"] = {"tristate": True}
    elif t_type == "boolean_tick":
        t_col["formatter"] = "tickCross"
        t_col["formatterParams"] = {
            "allowEmpty": True, "crossElement": " "}
        t_col["hozAlign"] = "center"
    elif t_type == "number":
        t_col["headerFilter"] = __ns__("minMaxFilterEditor")
        t_col["headerFilterFunc"] = __ns__("minMaxFilterFunction")
        t_col["headerFilterLiveFilter"] = False
    elif t_type == "date":
        t_col["formatter"] = "datetime"
        t_col["formatterParams"] = {
            "inputFormat": "iso",
            "outputFormat": "yyyy-MM-dd"
        }
        t_col["headerFilterParams"] = {"format": "yyyy-MM-dd"}
    return t_col


def __get_column_tabulator_editor__(t_type):
    t_col = {}
    if t_type == "boolean":
        t_col["editor"] = "list"
        t_col["editorParams"] = {"values": {
            "true": "True",
            "false": "False",
            "": "(empty)"
        }}
        t_col["headerFilter"] = "input"
        t_col["headerFilterParams"] = {}
    elif t_type == "boolean_tick":
        t_col["editor"] = "tickCross"
    elif t_type == "number":
        t_col["editor"] = "number"
    elif t_type == "date":
        t_col["editor"] = "date"
        t_col["editorParams"] = {"format": "yyyy-MM-dd"}
    else:
        t_col["editor"] = "input"
    return t_col

def __get_column_tabulator_formatter_linked_record__(ees, linked_record_name):
    """Define Tabulator formatter settings for a column whose type is linked record"""

    t_col = {}
    t_col["formatter"] = "lookup"
    # define formatterParams property as an inline javascript function which takes cell as parameter and always returns "toto", using the assign function of the javascript module of dash_extensions
    # TODO: use paramLookup function from custom_tabulator.js instead of inline javascript function
    t_col["formatterParams"] = assign(
        """
        function(cell){
            // TODO: cache results
            url_base = "http://localhost:8000/label/companies_ext"
            key = cell.getValue()
            label = ""
            // Assign value returned by GET request to url_base with parameter key, to label variable; in case connection fails, assign empty value to label
            $.ajax({
                url: url_base + "?key=" + key,
                async: false,
                success: function(result){
                    label = result
                },
                error: function(result){
                    label = ""
                    console.log("Could not retrieve label from server")
                }
            });
            d = {}
            d[key] = label
            return d
        }
        """
    )
    return t_col

def __get_column_tabulator_editor_linked_record__(ees, linked_record_name):
    """Define Tabulator editor settings for a column whose type is linked record"""

    linked_records_df = DataFrame(data=ees.linked_records).set_index("name")

    # Use a list editor
    t_col = {}
    t_col["editor"] = "list"
    t_col["editorParams"] = {
        "autocomplete": True,
        "filterDelay": 300,
        # "freetext": True,
        "listOnEmpty": False,
        "clearable": True
    }

    # If lookup columns have been provided, use an item formatter in the editor
    linked_ds_lookup_columns = linked_records_df.loc[linked_record_name,
                                                     "ds_lookup_columns"]
    if linked_ds_lookup_columns != []:
        t_col["editorParams"]["itemFormatter"] = __ns__(
            "itemFormatter")

    # Define possible values in the list
    linked_ds_name = linked_records_df.loc[linked_record_name, "ds_name"]
    linked_ds = ees.project.get_dataset(linked_ds_name)
    metrics = linked_ds.compute_metrics(metric_ids=["records:COUNT_RECORDS"])[
        "result"]["computed"]
    for m in metrics:
        if (m["metric"]["metricType"] == "COUNT_RECORDS"):
            count_records = int(m["value"])
    if (count_records > 1000):
        # ds_key and ds_label would normally be used, when loading the linked dataset in memory, but here they will be fetched by the API endpoint who has access to an EditableEventSourced dataset and who's given linked_ds_name in the URL
        logging.debug(
            f"Using API to lookup values in {linked_ds_name} since this dataset has {count_records} rows")
        t_col["editorParams"]["filterRemote"] = True
        t_col["editorParams"]["valuesURL"] = "lookup/" + linked_ds_name

    else:
        # The dataset can be loaded in memory
        logging.debug(
            f"Loading {linked_ds_name} in memory since this dataset has {count_records} rows")
        linked_ds_key = linked_records_df.loc[linked_record_name, "ds_key"]
        linked_ds_label = linked_records_df.loc[linked_record_name, "ds_label"]
        linked_df = Dataset(linked_ds_name).get_dataframe()
        editor_values_param = get_values_from_linked_df(
            linked_df, linked_ds_key, linked_ds_label, linked_ds_lookup_columns)
        if (linked_ds_label != linked_ds_key):
            # A label column was provided: use labels in the formatter, instead of the keys; for this we provide a "lookup" parameter which looks like this: {"key1": "label1", "key2": "label2", "null": ""}
            t_col["formatter"] = "lookup"
            formatter_lookup_param = linked_df.set_index(
                linked_ds_key)[linked_ds_label].to_dict()
            # use empty label when key is missing
            formatter_lookup_param["null"] = ""
            t_col["formatterParams"] = formatter_lookup_param
        t_col["editorParams"]["values"] = editor_values_param
        t_col["editorParams"]["filterFunc"] = __ns__("filterFunc")

    return t_col


def get_columns_tabulator(ees, freeze_editable_columns=False):
    """Prepare column settings to pass to Tabulator"""

    linked_records_df = DataFrame(data=ees.linked_records).set_index("name")
    try:
        linked_record_names = linked_records_df.index.values.tolist()
    except:
        linked_record_names = []

    t_cols = []
    for col_name in ees.primary_keys + ees.display_column_names + ees.editable_column_names:

        # Properties to be shared by all columns
        t_col = {"field": col_name, "title": col_name, "headerFilter": True,
                 "resizable": True, "headerContextMenu": __ns__("headerMenu")}

        # Define formatter and header filters based on type
        t_type = __get_column_tabulator_type__(ees, col_name)
        if col_name in linked_record_names:
            t_col.update(
                __get_column_tabulator_formatter_linked_record__(ees, col_name))
        else:
            t_col.update(__get_column_tabulator_formatter__(t_type))
        if col_name in ees.primary_keys:
            t_col["frozen"] = True

        # Define editor, if it's an editable column
        if col_name in ees.editable_column_names:
            if (freeze_editable_columns):
                t_col["frozen"] = True  # freeze to the right
            if col_name in linked_record_names:
                t_col.update(
                    __get_column_tabulator_editor_linked_record__(ees, col_name))
            else:
                t_col.update(__get_column_tabulator_editor__(t_type))

        t_cols.append(t_col)

    return t_cols
