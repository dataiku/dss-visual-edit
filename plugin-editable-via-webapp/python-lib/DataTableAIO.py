from dash import html, Input, Output, State, callback, MATCH
from tabulator_utils import get_columns_tabulator
from EditableEventSourced import EditableEventSourced
from dash_tabulator import DashTabulator
import uuid

# from dash_tabulator import DashTabulator


class DataTableAIO(html.Div):  # html.Div will be the "parent" component
    class ids:
        """
        A set of functions that create pattern-matching callbacks of the subcomponents.
        """

        dashtabulator = lambda aio_id: {
            "component": "DataTableAIO",
            "subcomponent": "DashTabulator",
            "aio_id": aio_id,
        }
        div = lambda aio_id: {
            "component": "DataTableAIO",
            "subcomponent": "div",
            "aio_id": aio_id,
        }

    # Make the ids class a public class
    ids = ids

    # Define the arguments of the All-in-One component
    def __init__(self, ds_name, primary_keys, editable_column_names, aio_id=None):
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

        ees = EditableEventSourced(ds_name, primary_keys, editable_column_names)
        columns = get_columns_tabulator(ees)

        # Define the component's layout
        super().__init__(
            [
                DashTabulator(
                    id=self.ids.dashtabulator(aio_id),
                    datasetName=ds_name,
                    columns=columns,
                    data=ees.get_edited_df().to_dict("records"),
                ),
                html.Div(id=self.ids.div(aio_id), children="Info zone for tabulator"),
            ]
        )

    # Define the component's callbacks
    @callback(
        Output(ids.div(MATCH), "children"),
        Input(ids.dashtabulator(MATCH), "cellEdited"),
        State(ids.dashtabulator(MATCH), "datasetName"),
        State(ids.dashtabulator(MATCH), "primaryKeys"),
        State(ids.dashtabulator(MATCH), "editableColumns"),
        prevent_initial_call=True,
    )
    def add_edit(cell, ds_name, primary_keys, editable_column_names):
        """
        Record edit in editlog, once a cell has been edited

        If the cell is in the Reviewed column, we also update values for all other editable columns in the same row (except Comments). The values in these columns are generated by the upstream data flow and subject to change. We record them, in case the user didn't edit them before marking the row as reviewed.
        """
        info = ""
        ees = EditableEventSourced(
            ds_name,
            primary_keys=primary_keys,
            editable_column_names=editable_column_names,
        )
        if cell["field"] == "Reviewed":
            for col_name in editable_column_names:
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
