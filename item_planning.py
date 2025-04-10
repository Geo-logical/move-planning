import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.express as px
import pandas as pd

# Define default data and options

# Initial data: each move part (or "task") has a name, category, owner, notes, location, start date, and end date.
initial_data = [
    {
        "Name": "Sofa",
        "Category": "furniture",
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

# Pre-defined options for dropdowns:
default_locations = [
    "Hawaii", "Connecticut", "Sydney", "Uhaul shipping container", "sold", "trash", "California", "Baltimore"
]
default_categories = [
    "furniture", "kitchen", "bed and bath", "recreation", "tools", "work stuff", "Eris stuff", "Kilo stuff", "family stuff"
]

# Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Move Tracking Gantt Chart"),
    
    # Editable table for move items
    dash_table.DataTable(
        id='tasks-table',
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
        dropdown={
            "Category": {
                "options": [{"label": c, "value": c} for c in default_categories]
            },
            "Location": {
                "options": [{"label": l, "value": l} for l in default_locations]
            }
        },
        style_table={'overflowX': 'auto'},
    ),
    
    html.Br(),
    html.Button("Add Task", id="add-row-button", n_clicks=0),
    html.Br(), html.Br(),
    
    # Graph to display the Gantt chart
    dcc.Graph(id="gantt-chart")
], style={"width": "80%", "margin": "auto", "fontFamily": "Arial, sans-serif"})

# Callback to add a new row when button is clicked
@app.callback(
    Output('tasks-table', 'data'),
    Input('add-row-button', 'n_clicks'),
    State('tasks-table', 'data'),
    State('tasks-table', 'columns')
)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        new_row = {col['id']: '' for col in columns}
        # Set default category and location if desired
        new_row["Category"] = default_categories[0]
        new_row["Location"] = default_locations[0]
        rows.append(new_row)
    return rows

# Callback to update the Gantt chart based on table data
@app.callback(
    Output("gantt-chart", "figure"),
    Input("tasks-table", "data")
)
def update_gantt(data):
    if not data or len(data) == 0:
        return {}
    
    df = pd.DataFrame(data)
    
    # Filter out rows missing temporal data
    df = df[df["Start"].astype(bool) & df["End"].astype(bool)]
    
    # Convert start and end dates to datetime
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["End"] = pd.to_datetime(df["End"], errors="coerce")
    df = df.dropna(subset=["Start", "End"])
    
    if df.empty:
        return {}
    
    # Create the timeline (Gantt chart) using Plotly Express
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Name",
        color="Category",
        hover_data=["Assigned Owner", "Notes", "Location"]
    )
    
    # Reverse the y-axis so tasks are ordered like a Gantt chart (top to bottom)
    fig.update_yaxes(autorange="reversed")
    
    fig.update_layout(
        title="Move Tracking Gantt Chart",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True)
