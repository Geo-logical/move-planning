import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context, MATCH, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json

# ----------------------------
# Sample data and default options
# ----------------------------
initial_data = [
    {
        "Name": "Sofa",
        "Category": "furniture",
        "Assigned Owner": "Andy",
        "Notes": "Living room sofa",
        "Intervals": ""  # Intervals will be stored as a JSON string
    },
    {
        "Name": "Dining Set",
        "Category": "kitchen",
        "Assigned Owner": "Andy",
        "Notes": "Table and chairs",
        "Intervals": ""
    }
]

default_categories = [
    "furniture", "kitchen", "bed and bath", "recreation",
    "tools", "work stuff", "Eris stuff", "Kilo stuff", "family stuff"
]
default_locations = [
    "Hawaii", "Connecticut", "Sydney",
    "Uhaul shipping container", "sold", "trash", "California", "Baltimore"
]

# ----------------------------
# Initialize the Dash app
# ----------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Move Tracking Dashboard"

app.layout = dbc.Container([
    html.H1("Move Tracking Dashboard", style={"textAlign": "center", "marginTop": "20px"}),
    
    # Data Table
    dash_table.DataTable(
        id="tasks-table",
        columns=[
            {"name": "Name", "id": "Name", "editable": True},
            {"name": "Category", "id": "Category", "editable": True, "presentation": "dropdown"},
            {"name": "Assigned Owner", "id": "Assigned Owner", "editable": True},
            {"name": "Notes", "id": "Notes", "editable": True},
            {"name": "Intervals", "id": "Intervals", "editable": False}  # This will show the intervals summary
        ],
        data=initial_data,
        editable=True,
        row_deletable=True,
        sort_action="native",
        dropdown={
            "Category": {"options": [{"label": c, "value": c} for c in default_categories]}
        },
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": "Arial, sans-serif", "padding": "5px"}
    ),

    html.Br(),
    dbc.Button("Add New Task", id="open-modal", color="secondary", n_clicks=0),
    html.Br(), html.Br(),

    dcc.Graph(id="gantt-chart"),
    
    # Modal for data entry
    dbc.Modal(
        [
            dbc.ModalHeader("Add New Task"),
            dbc.ModalBody([
                # Standard fields
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
                    dbc.Input(id="input-owner", type="text", placeholder="Name for who's stuff or responsibility, nothing is fine too.")
                ], className="mb-3"),
                
                html.Div([
                    dbc.Label("Notes:"),
                    dbc.Textarea(id="input-notes", placeholder="notes")
                ], className="mb-3"),
                
                html.H5("Location Intervals"),
                # Container for dynamically added intervals
                html.Div(id="intervals-container"),
                dbc.Button("Add Interval", id="add-interval", color="secondary", n_clicks=0, className="mb-3"),
                
                # Each interval row will consist of:
                # - Location Dropdown
                # - Start Date Picker
                # - End Date Picker
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

# ----------------------------
# Callback to toggle the modal open/close
# ----------------------------
@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"),
     Input("close-modal", "n_clicks"),
     Input("submit-task", "n_clicks")],
    [State("modal", "is_open")]
)
def toggle_modal(n_open, n_close, n_submit, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return is_open
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id in ["open-modal", "close-modal", "submit-task"]:
        return not is_open
    return is_open

# ----------------------------
# Callback to update the intervals container dynamically
# ----------------------------
@app.callback(
    Output("intervals-container", "children"),
    Input("add-interval", "n_clicks")
)
def update_intervals(n_clicks):
    # Create one interval input group per click
    intervals = []
    for i in range(n_clicks):
        interval = html.Div([
            dbc.Label(f"Interval {i+1}:"),
            dcc.Dropdown(
                id={"type": "interval-location", "index": i},
                options=[{"label": l, "value": l} for l in default_locations],
                value=default_locations[0],
                style={"marginBottom": "5px"}
            ),
            dcc.DatePickerSingle(
                id={"type": "interval-start", "index": i},
                date=pd.to_datetime("today").date(),
                style={"marginBottom": "5px"}
            ),
            dcc.DatePickerSingle(
                id={"type": "interval-end", "index": i},
                date=pd.to_datetime("today").date()
            )
        ], className="mb-3")
        intervals.append(interval)
    return intervals

# ----------------------------
# Callback to add the new task (including intervals) into the DataTable
# ----------------------------
@app.callback(
    Output("tasks-table", "data"),
    Input("submit-task", "n_clicks"),
    State("input-name", "value"),
    State("input-category", "value"),
    State("input-owner", "value"),
    State("input-notes", "value"),
    State("add-interval", "n_clicks"),
    State({"type": "interval-location", "index": ALL}, "value"),
    State({"type": "interval-start", "index": ALL}, "date"),
    State({"type": "interval-end", "index": ALL}, "date"),
    State("tasks-table", "data"),
    prevent_initial_call=True
)
def add_task(n_clicks, name, category, owner, notes, interval_clicks, interval_locs, interval_starts, interval_ends, current_data):
    if n_clicks:
        # Build interval objects from the dynamic inputs
        intervals = []
        if interval_locs and interval_starts and interval_ends:
            for loc, start, end in zip(interval_locs, interval_starts, interval_ends):
                intervals.append({"Location": loc, "Start": start, "End": end})
        
        new_task = {
            "Name": name if name else "New Task",
            "Category": category if category else default_categories[0],
            "Assigned Owner": owner if owner else "",
            "Notes": notes if notes else "",
            # Store intervals as JSON text (you could later parse it if needed)
            "Intervals": json.dumps(intervals)
        }
        current_data.append(new_task)
    return current_data

# ----------------------------
# Callback to update the Gantt chart based on table data (optional visualization)
# ----------------------------
@app.callback(
    Output("gantt-chart", "figure"),
    Input("tasks-table", "data")
)
def update_gantt(data):
    if not data or len(data) == 0:
        return {}
    # Convert the task data into a DataFrame.
    # For visualization, we need to extract each interval into its own row.
    rows = []
    for task in data:
        base = {k: task[k] for k in ["Name", "Category", "Assigned Owner", "Notes"]}
        # If intervals is present and parseable, iterate
        if task.get("Intervals"):
            try:
                intervals = json.loads(task["Intervals"])
            except:
                intervals = []
            for interval in intervals:
                row = base.copy()
                row["Location"] = interval.get("Location", "")
                row["Start"] = interval.get("Start", "")
                row["End"] = interval.get("End", "")
                rows.append(row)
    if not rows:
        return {}

    df = pd.DataFrame(rows)
    # Convert date fields
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["End"] = pd.to_datetime(df["End"], errors="coerce")
    df = df.dropna(subset=["Start", "End"])
    if df.empty:
        return {}

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Name",
        color="Location",
        hover_data=["Assigned Owner", "Notes", "Location"]#need to format this
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Move Tracking Gantt Chart", margin=dict(l=20, r=20, t=40, b=20))
    return fig

if __name__ == '__main__':
    app.run(debug=True)

