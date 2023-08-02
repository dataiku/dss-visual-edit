import logging
from dash import Input, Output, State, callback, MATCH
from dash.html import Div
from dash.dcc import Interval
from datetime import datetime
from commons import get_last_build_date
from tabulator_utils import get_columns_tabulator
from EditableEventSourced import EditableEventSourced
from dash_tabulator import DashTabulator
import uuid

# from dash_tabulator import DashTabulator


class DataTableAIO(Div):  # Div will be the "parent" component
    class ids:
        """
        A set of functions that create pattern-matching callbacks of the subcomponents.
        """

        refresh_div = lambda aio_id: {
            "component": "DataTableAIO",
            "subcomponent": "refresh_div",
            "aio_id": aio_id,
        }
        interval = lambda aio_id: {
            "component": "DataTableAIO",
            "subcomponent": "interval",
            "aio_id": aio_id,
        }
        dashtabulator = lambda aio_id: {
            "component": "DataTableAIO",
            "subcomponent": "dashtabulator",
            "aio_id": aio_id,
        }
        editinfo_div = lambda aio_id: {
            "component": "DataTableAIO",
            "subcomponent": "editinfo_div",
            "aio_id": aio_id,
        }

    # Make the ids class a public class
    ids = ids

    last_build_date_initial = ""
    last_build_date_ok = False

    # Define the arguments of the All-in-One component
    def __init__(self, ds_name, freeze_editable_columns=False, aio_id=None):
        """
        DataTableAIO is a Dash All-in-One component that is composed of a parent `html.Div`, with a `DashTabulator` component whose data comes from a Dataiku dataset.

        Arguments:
        - `ds_name` - name of the Dataiku dataset (required)
        - `aio_id` - The All-in-One component ID used to generate the components dictionary IDs.

        The All-in-One component dictionary IDs are available as DataTableAIO.ids.datatable(aio_id)
        """

        # Allow developers to pass in their own `aio_id` if they're binding their own callback to a particular component. Otherwise, generate a random one.
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        ees = EditableEventSourced(ds_name)
        columns = get_columns_tabulator(ees, freeze_editable_columns)
        self.project = ees.project

        try:
            self.last_build_date_initial = get_last_build_date(ds_name, self.project)
            self.last_build_date_ok = True
        except:
            self.last_build_date_initial = ""
            self.last_build_date_ok = False

        # Define the component's layout
        super().__init__(
            [
                Div(
                    id="self.ids.refresh_div(aio_id)",
                    children=[
                        Div(
                            id="data-refresh-message",
                            children="The original dataset has changed, please refresh this page to load it here. (Your edits are safe.)",
                            style={"display": "inline"},
                        ),
                        Div(
                            id="last-build-date",
                            children=str(self.last_build_date_initial),
                            style={"display": "none"},
                        ),  # when the original dataset was last built
                    ],
                    className="ui compact warning message",
                    style={"display": "none"},
                ),
                Interval(
                    id="self.ids.interval(aio_id)",
                    interval=10 * 1000,  # in milliseconds
                    n_intervals=0,
                ),
                DashTabulator(
                    id=self.ids.dashtabulator(aio_id),
                    datasetName=ds_name,
                    columns=columns,
                    data=ees.get_edited_df().to_dict("records"),
                ),
                Div(
                    id=self.ids.editinfo_div(aio_id), children="Info zone for tabulator"
                ),
            ]
        )

    self.data_fresh = True

    @callback(
        [
            Output("refresh-div", "style"),
            Output("last-build-date", "children"),
        ],  # TODO: fix ids
        [
            # Changes in the Inputs trigger the callback
            Input("interval-component-iu", "n_intervals"),
            # Changes in States don't trigger the callback
            State("refresh-div", "style"),
            State("last-build-date", "children"),
        ],
        prevent_initial_call=True,
    )
    def toggle_refresh_div_visibility(n_intervals, refresh_div_style, last_build_date):
        """
        Toggle visibility of refresh div, when the interval component fires: check last build date of original dataset and if it's more recent than what we had, display the refresh div
        """
        style_new = refresh_div_style
        if self.last_build_date_ok:
            last_build_date_new = str(get_last_build_date(ds_name, self.project))
            if int(last_build_date_new) > int(last_build_date):
                logging.info("The original dataset has changed.")
                last_build_date_new_fmtd = datetime.utcfromtimestamp(
                    int(last_build_date_new) / 1000
                ).isoformat()
                last_build_date_fmtd = datetime.utcfromtimestamp(
                    int(last_build_date) / 1000
                ).isoformat()
                logging.info(
                    f"""Last build date: {last_build_date_new} ({last_build_date_new_fmtd}) — previously {last_build_date} ({last_build_date_fmtd})"""
                )
                style_new["display"] = "block"
                self.data_fresh = False
        else:
            last_build_date_new = last_build_date
        return style_new, last_build_date_new

    @callback(
        Output(ids.editinfo_div(MATCH), "children"),
        Input(ids.dashtabulator(MATCH), "cellEdited"),
        State(ids.dashtabulator(MATCH), "datasetName"),
        prevent_initial_call=True,
    )
    def add_edit(cell, ds_name):
        """
        Record edit in editlog, once a cell has been edited

        If the cell is in the Reviewed column, we also update values for all other editable columns in the same row (except Comments). The values in these columns are generated by the upstream data flow and subject to change. We record them, in case the user didn't edit them before marking the row as reviewed.
        """
        info = ""
        ees = EditableEventSourced(ds_name)
        if cell["field"] == "Reviewed":
            for col_name in ees.editable_column_names:
                if col_name != "Comments":
                    info += (
                        ees.update_row(
                            primary_keys=cell.get(
                                "row"
                            ),  # contains values for primary keys — and other columns too, but they'll be discarded
                            column=col_name,
                            value=cell.get("row").get(col_name),
                        )
                        + "\n"
                    )
        else:
            info = ees.update_row(
                primary_keys=cell.get("row"),
                column=cell.get("field"),
                value=cell.get("value"),
            )
        return info
