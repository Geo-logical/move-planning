import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Sample initial data: Each task has a Name, Category, Assigned Owner, Notes, Location, Start, and End
initial_data = [
    {
        "Name": "Hardtail mountina Bike",
        "Category": "recreation",
        "Assigned Owner": "Andy",
        "Notes": "Living room sofa",
        "Location": "Hawaii",
        "Start": "2023-09-01",
        "End": "2023-09-03"
    },
    {
        "Name": "Dining Set",
        "Category": "kitchen",
        "Assigned Owner": "Andy",
        "Notes": "Table and chairs",
        "Location": "Connecticut",
        "Start": "2023-09-03",
        "End": "2023-09-05"
    }
]

# Default dropdown options for categories and locations
default_categories = [
    "furniture", "kitchen", "bed and bath", "recreation",
    "tools", "work stuff", "Eris stuff", "Kilo stuff", "family stuff"
]
default_locations = [
    "Hawaii", "Connecticut", "Sydney",
    "Uhaul shipping container", "sold", "trash", "California", "Baltimore"
]

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Move Tracking Dashboard"

app.layout = dbc.Container([
    html.H1("Move Tracking Dashboard", style={"textAlign": "center", "marginTop": "20px"}),

    # Data table that is editable and sortable (native sorting enabled)
    dash_table.DataTable(
        id="tasks-table",
        columns=[
            {"name": "Name", "id": "Name", "editable": True},
            {"name": "Category", "id": "Category", "editable": True, "presentation": "dropdown"},
            {"name": "Assigned Owner", "id": "Assigned Owner", "editable": True},
            {"name": "Notes", "id": "Notes", "editable": True},
            {"name": "Location", "id": "Location", "editable": True, "presentation": "dropdown"},
            {"name": "Start", "id": "Start", "editable": True, "type": "datetime"},
            {"name": "End", "id": "End", "editable": True, "type": "datetime"}
        ],
        data=initial_data,
        editable=True,
        row_deletable=True,
        sort_action="native",  # Allow sorting of columns
        dropdown={
            "Category": {
                "options": [{"label": c, "value": c} for c in default_categories]
            },
            "Location": {
                "options": [{"label": l, "value": l} for l in default_locations]
            }
        },
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "Arial, sans-serif", "padding": "5px"}
    ),

    html.Br(),
    dbc.Button("Add New Task", id="open-modal", color="primary", n_clicks=0),
    html.Br(), html.Br(),

    # A sample Gantt chart based on the table data (optional for visualization)
    dcc.Graph(id="gantt-chart"),

    # Modal for pop-up data entry
    dbc.Modal(
        [
            dbc.ModalHeader("Add New Task"),
            dbc.ModalBody([
                html.Div([
                    dbc.Label("Name:"),
                    dbc.Input(id="input-name", type="text", placeholder="Enter task name")
                ], className="mb-3"),

                html.Div([
                    dbc.Label("Category:"),
                    dcc.Dropdown(
                        id="input-category",
                        options=[{"label": c, "value": c} for c in default_categories],
                        value=default_categories[0]
                    )
                ], className="mb-3"),

                html.Div([
                    dbc.Label("Assigned Owner:"),
                    dbc.Input(id="input-owner", type="text", placeholder="Enter owner's name")
                ], className="mb-3"),

                html.Div([
                    dbc.Label("Notes:"),
                    dbc.Textarea(id="input-notes", placeholder="Enter task notes")
                ], className="mb-3"),

                html.Div([
                    dbc.Label("Location:"),
                    dcc.Dropdown(
                        id="input-location",
                        options=[{"label": l, "value": l} for l in default_locations],
                        value=default_locations[0]
                    )
                ], className="mb-3"),

                html.Div([
                    dbc.Label("Start Date:"),
                    dcc.DatePickerSingle(
                        id="input-start",
                        date=pd.to_datetime("today").date()
                    )
                ], className="mb-3"),

                html.Div([
                    dbc.Label("End Date:"),
                    dcc.DatePickerSingle(
                        id="input-end",
                        date=pd.to_datetime("today").date()
                    )
                ], className="mb-3")
            ]),
            dbc.ModalFooter([
                dbc.Button("Submit Task", id="submit-task", color="success", n_clicks=0),
                dbc.Button("Close", id="close-modal", color="secondary", className="ms-2", n_clicks=0)
            ])
        ],
        id="modal",
        is_open=False
    )
], fluid=True, style={"marginTop": "20px"})

# Callback to toggle the modal open/close
@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks"), Input("submit-task", "n_clicks")],
    [State("modal", "is_open")]
)
def toggle_modal(n_open, n_close, n_submit, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return is_open
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id in ["open-modal", "close-modal", "submit-task"]:
        # Toggle state when any of the buttons are pressed.
        return not is_open
    return is_open

# Callback to add a new task from the modal form into the DataTable
@app.callback(
    Output("tasks-table", "data"),
    Input("submit-task", "n_clicks"),
    State("input-name", "value"),
    State("input-category", "value"),
    State("input-owner", "value"),
    State("input-notes", "value"),
    State("input-location", "value"),
    State("input-start", "date"),
    State("input-end", "date"),
    State("tasks-table", "data"),
    prevent_initial_call=True
)
def add_task(n_clicks, name, category, owner, notes, location, start, end, current_data):
    if n_clicks:
        new_task = {
            "Name": name if name else "New Task",
            "Category": category if category else default_categories[0],
            "Assigned Owner": owner if owner else "",
            "Notes": notes if notes else "",
            "Location": location if location else default_locations[0],
            "Start": start if start else pd.to_datetime("today").date().isoformat(),
            "End": end if end else pd.to_datetime("today").date().isoformat()
        }
        current_data.append(new_task)
    return current_data

# Callback to update the Gantt chart based on table data (optional visualization)
@app.callback(
    Output("gantt-chart", "figure"),
    Input("tasks-table", "data")
)
def update_gantt(data):
    if not data or len(data) == 0:
        return {}
    df = pd.DataFrame(data)
    # Filter out rows without valid dates
    df = df[df["Start"].astype(bool) & df["End"].astype(bool)]
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["End"] = pd.to_datetime(df["End"], errors="coerce")
    df = df.dropna(subset=["Start", "End"])
    if df.empty:
        return {}

    # Build a timeline chart using Plotly Express
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Name",
        color="Category",
        hover_data=["Assigned Owner", "Notes", "Location"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title="Move Tracking Gantt Chart",
        margin={"l": 20, "r": 20, "t": 40, "b": 20}
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True)
