import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context, MATCH, ALL, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json
import sqlite3
from datetime import datetime

# ----------------------------
# Sample data and default options
# ----------------------------
class MoveDatabase:
    def __init__(self, db_path='move_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    assigned_owner TEXT,
                    notes TEXT
                )
            ''')
            # Create intervals table with foreign key to items
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intervals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    location TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    FOREIGN KEY (item_id) REFERENCES items (id)
                )
            ''')
            conn.commit()
    
    def add_item(self, name, category, owner, notes, intervals=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (name, category, assigned_owner, notes)
                VALUES (?, ?, ?, ?)
            ''', (name, category, owner, notes))
            item_id = cursor.lastrowid
            
            if intervals:
                for interval in intervals:
                    cursor.execute('''
                        INSERT INTO intervals (item_id, location, start_date, end_date)
                        VALUES (?, ?, ?, ?)
                    ''', (item_id, interval['Location'], interval['Start'], interval['End']))
            conn.commit()
    
    def get_all_items(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            try:
                # Get all items with their intervals
                cursor.execute('''
                    SELECT i.*, GROUP_CONCAT(
                        json_object(
                            'Location', iv.location,
                            'Start', iv.start_date,
                            'End', iv.end_date
                        )
                    ) as intervals
                    FROM items i
                    LEFT JOIN intervals iv ON i.id = iv.item_id
                    GROUP BY i.id
                ''')
                
                items = []
                for row in cursor.fetchall():
                    item = dict(row)
                    intervals_str = item.get('intervals', '[]')
                    
                    try:
                        if intervals_str:
                            intervals = json.loads(f"[{intervals_str}]")
                        else:
                            intervals = []
                        intervals_json = json.dumps(intervals)
                    except json.JSONDecodeError:
                        print(f"Error parsing intervals for item {item.get('name')}")
                        intervals_json = "[]"
                    
                    items.append({
                        "Name": item['name'],
                        "Category": item['category'],
                        "Assigned Owner": item['assigned_owner'],
                        "Notes": item['notes'],
                        "Intervals": intervals_json
                    })
                
                return items
                
            except Exception as e:
                print(f"Error in get_all_items: {e}")
                return []

    def delete_item(self, name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                print(f"Starting deletion process for item: {name}")
                
                # First get the item_id
                cursor.execute('SELECT id FROM items WHERE name = ?', (name,))
                result = cursor.fetchone()
                
                if result:
                    item_id = result[0]
                    print(f"Found item_id: {item_id}")
                    
                    # Delete related intervals first
                    cursor.execute('DELETE FROM intervals WHERE item_id = ?', (item_id,))
                    print(f"Deleted intervals for item_id: {item_id}")
                    
                    # Then delete the item
                    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
                    print(f"Deleted item with id: {item_id}")
                    
                    conn.commit()
                    print(f"Committed deletion of item: {name}")
                else:
                    print(f"No item found with name: {name}")
                    
            except Exception as e:
                print(f"Error in delete_item: {e}")
                conn.rollback()
                raise e

    def update_item(self, old_name, name, category, owner, notes, intervals=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                # First get the item_id
                cursor.execute('SELECT id FROM items WHERE name = ?', (old_name,))
                result = cursor.fetchone()
                
                if result:
                    item_id = result[0]
                    
                    # Update the item
                    cursor.execute('''
                        UPDATE items 
                        SET name=?, category=?, assigned_owner=?, notes=?
                        WHERE id=?
                    ''', (name, category, owner, notes, item_id))
                    
                    # Handle intervals if provided
                    if intervals is not None:
                        # Delete existing intervals
                        cursor.execute('DELETE FROM intervals WHERE item_id=?', (item_id,))
                        
                        # Add new intervals
                        for interval in intervals:
                            cursor.execute('''
                                INSERT INTO intervals (item_id, location, start_date, end_date)
                                VALUES (?, ?, ?, ?)
                            ''', (item_id, interval['Location'], interval['Start'], interval['End']))
                    
                    conn.commit()
                    print(f"Successfully updated item: {old_name} -> {name}")
                else:
                    print(f"No item found with name: {old_name}")
                    
            except Exception as e:
                print(f"Error in update_item: {e}")
                conn.rollback()
                raise e

    def save_notes(self, notes):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS general_notes
                (id INTEGER PRIMARY KEY, notes TEXT)
            ''')
            cursor.execute('DELETE FROM general_notes')  # Clear existing
            cursor.execute('INSERT INTO general_notes (notes) VALUES (?)', (notes,))
            conn.commit()

    def get_notes(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS general_notes
                (id INTEGER PRIMARY KEY, notes TEXT)
            ''')
            cursor.execute('SELECT notes FROM general_notes LIMIT 1')
            result = cursor.fetchone()
            return result[0] if result else ""

db = MoveDatabase()

# Replace initial_data with database query
initial_data = db.get_all_items()

default_categories = [
    "Furniture", "Kitchen", "Bed and Bath", "Rec",
    "Tools", "Work", "Eris stuff", "Kilo stuff", "family stuff"
]
default_locations = [
    "Hawaii", "Connecticut", "Sydney",
    "Uhaul Shipping Container", "Sold", "Trash/Donate", "California", "Baltimore",
    "Uncertain", "In-Transit"
]
#d85413
# Add this near your other default settings at the top of the file
location_colors = {
    "Hawaii": "#FF9999",
    "Connecticut": "#66B2FF",
    "Sydney": "#99FF99",
    "Uhaul shipping container": "#FFCC99",
    "Sold": "#170215",
    "Trash": "#808080",
    "California": "#FFB366",
    "Baltimore": "#530953",
    "Uncertain": "#E6E6E6",
    "In-Transit": "#fb09cf"
}

category_colors = {
    "furniture": "#FFB6C1",
    "kitchen": "#98FB98",
    "bed and bath": "#87CEEB",
    "recreation": "#DDA0DD",
    "tools": "#F0E68C",
    "work stuff": "#E6E6FA",
    "Eris stuff": "#FFB347",
    "Kilo stuff": "#87CEFA",
    "family stuff": "#F08080"
}

owner_colors = {
    "Andy": "#4169E1",
    "Lucia": "#FF69B4",
    "NA": "#A9A9A9"
}

# ----------------------------
# Initialize the Dash app
# ----------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder='assets',
    serve_locally=True
)
app.title = "Move Tracking Dashboard"

app.layout = dbc.Container([
    dcc.Store(id='edit-mode-store', data=False),
    
    html.H1("Move Tracking Dashboard", style={"textAlign": "center", "marginTop": "20px"}),
    
    dcc.Tabs([
        dcc.Tab(label="Item Management", children=[
            html.Div([
                html.Br(),
                dbc.Button("Add New Task", id="open-modal", color="secondary", n_clicks=0),
                html.Br(), html.Br(),
                dash_table.DataTable(
                    id="tasks-table",
                    columns=[
                        {"name": "Actions", "id": "actions", "presentation": "markdown"},
                        {"name": "Name", "id": "Name", "editable": True},
                        {"name": "Category", "id": "Category", "editable": True, "presentation": "dropdown"},
                        {"name": "Assigned Owner", "id": "Assigned Owner", "editable": True},
                        {"name": "Notes", "id": "Notes", "editable": True},
                        {"name": "Intervals", "id": "Intervals", "editable": False}
                    ],
                    data=[{
                        "actions": "✏️",
                        **row
                    } for row in initial_data],
                    row_deletable=True,
                    sort_action="native",
                    dropdown={
                        "Category": {"options": [{"label": c, "value": c} for c in default_categories]}
                    },
                    style_table={"overflowX": "auto"},
                    style_cell={"fontFamily": "Arial, sans-serif", "padding": "5px"}
                )
            ])
        ]),
        
        dcc.Tab(label="Timeline View", children=[
            html.Div([
                html.Br(),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Color By:"),
                        dcc.Dropdown(
                            id="color-by-dropdown",
                            options=[
                                {"label": "Location", "value": "Location"},
                                {"label": "Category", "value": "Category"},
                                {"label": "Assigned Owner", "value": "Assigned Owner"}
                            ],
                            value="Location",
                            clearable=False
                        )
                    ], width=3)
                ]),
                html.Br(),
                dcc.Graph(id="gantt-chart")
            ])
        ]),
        
        dcc.Tab(label="Notes", children=[
            html.Div([
                html.Br(),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("General Notes"),
                            dbc.CardBody([
                                dbc.Textarea(
                                    id="general-notes",
                                    placeholder="Enter general notes here...",
                                    style={"height": "300px"}
                                ),
                                html.Br(),
                                dbc.Button("Save Notes", id="save-notes", color="primary")
                            ])
                        ])
                    ])
                ])
            ])
        ])
    ]),
    
    # Modal for data entry
    dbc.Modal(
        [
            dbc.ModalHeader("Add New Task"),
            dbc.ModalBody([
                # Standard fields
                html.Div([
                    dbc.Label("Name:"),
                    dbc.Input(id="input-name", type="text", placeholder="Household Item")
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
                dbc.Button("Submit", id="submit-button", color="success", n_clicks=0),
                dbc.Button("Close", id="close-modal", color="secondary", className="ms-2", n_clicks=0)
            ])
        ],
        id="modal",
        is_open=False
    )
], fluid=True)

# Separate callback for handling intervals
@app.callback(
    Output("intervals-container", "children", allow_duplicate=True),
    Input("add-interval", "n_clicks"),
    [State("intervals-container", "children"),
     State("edit-mode-store", "data")],
    prevent_initial_call=True
)
def update_intervals(n_clicks, existing_children, is_edit_mode):
    if n_clicks == 0:
        return []
    
    intervals = existing_children if existing_children else []
    
    # Get the last interval's end date if it exists
    default_start_date = pd.to_datetime("today").date()
    if isinstance(intervals, list) and intervals:
        try:
            last_interval = intervals[-1]
            last_end_date = last_interval['props']['children'][3]['props']['date']
            if last_end_date:
                default_start_date = pd.to_datetime(last_end_date).date()
        except (KeyError, IndexError):
            pass
    
    new_interval = html.Div([
        dbc.Label(f"Interval {n_clicks}:"),
        dcc.Dropdown(
            id={"type": "interval-location", "index": n_clicks-1},
            options=[{"label": l, "value": l} for l in default_locations],
            value=default_locations[0],
            style={"marginBottom": "5px"}
        ),
        dcc.DatePickerSingle(
            id={"type": "interval-start", "index": n_clicks-1},
            date=default_start_date,
            style={"marginBottom": "5px"}
        ),
        dcc.DatePickerSingle(
            id={"type": "interval-end", "index": n_clicks-1},
            date=default_start_date,
            style={"marginBottom": "5px"}
        )
    ], className="mb-3")
    
    if isinstance(intervals, list):
        intervals.append(new_interval)
    else:
        intervals = [intervals, new_interval]
    
    return intervals

# Callback to handle modal opening/closing and form population
@app.callback(
    [
        Output("modal", "is_open"),
        Output("input-name", "value"),
        Output("input-category", "value"),
        Output("input-owner", "value"),
        Output("input-notes", "value"),
        Output("add-interval", "n_clicks"),
        Output("intervals-container", "children"),
        Output("edit-mode-store", "data")
    ],
    [
        Input("open-modal", "n_clicks"),
        Input("close-modal", "n_clicks"),
        Input("submit-button", "n_clicks"),
        Input("tasks-table", "active_cell")
    ],
    [
        State("tasks-table", "data"),
        State("modal", "is_open")
    ],
    prevent_initial_call=True
)
def handle_modal_state(n_open, n_close, n_submit, active_cell, data, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Handle new task
    if trigger_id == "open-modal":
        return True, "", default_categories[0], "", "", 0, [], False
    
    # Handle modal closing
    elif trigger_id in ["close-modal", "submit-button"]:
        return False, "", default_categories[0], "", "", 0, [], False
    
    # Handle edit click
    elif trigger_id == "tasks-table" and active_cell and active_cell['column_id'] == 'actions':
        row = data[active_cell['row']]
        try:
            intervals = json.loads(row["Intervals"]) if row["Intervals"] else []
            if isinstance(intervals, str):
                intervals = json.loads(intervals)
        except json.JSONDecodeError:
            intervals = []
            
        interval_components = []
        for i, interval in enumerate(intervals):
            interval_component = html.Div([
                dbc.Label(f"Interval {i+1}:"),
                dcc.Dropdown(
                    id={"type": "interval-location", "index": i},
                    options=[{"label": l, "value": l} for l in default_locations],
                    value=interval["Location"],
                    style={"marginBottom": "5px"}
                ),
                dcc.DatePickerSingle(
                    id={"type": "interval-start", "index": i},
                    date=interval["Start"],
                    style={"marginBottom": "5px"}
                ),
                dcc.DatePickerSingle(
                    id={"type": "interval-end", "index": i},
                    date=interval["End"],
                    style={"marginBottom": "5px"}
                )
            ], className="mb-3")
            interval_components.append(interval_component)
        
        return True, row["Name"], row["Category"], row["Assigned Owner"], row["Notes"], len(intervals), interval_components, True
    
    return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

# ----------------------------
# Callback to update the Gantt chart based on table data (optional visualization)
# ----------------------------
@app.callback(
    Output("gantt-chart", "figure"),
    [Input("tasks-table", "data"),
     Input("color-by-dropdown", "value")]
)
def update_gantt(data, color_by):
    if not data:
        return {}

    gantt_data = []
    
    for task in data:
        try:
            intervals = json.loads(task["Intervals"]) if task["Intervals"] else []
            if isinstance(intervals, str):
                intervals = json.loads(intervals)
            
            for interval in intervals:
                gantt_data.append({
                    "Name": task["Name"],
                    "Category": task["Category"],
                    "Assigned Owner": task["Assigned Owner"],
                    "Notes": task["Notes"],
                    "Location": interval["Location"],
                    "Start": interval["Start"],
                    "End": interval["End"]
                })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing intervals for task {task.get('Name')}: {e}")
            continue

    if not gantt_data:
        return {}

    df = pd.DataFrame(gantt_data)
    df["Start"] = pd.to_datetime(df["Start"])
    df["End"] = pd.to_datetime(df["End"])
    
    # Select color palette based on grouping
    color_map = {
        "Location": location_colors,
        "Category": category_colors,
        "Assigned Owner": owner_colors
    }
    
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Name",
        color=color_by,
        color_discrete_map=color_map[color_by],
        hover_data=["Assigned Owner", "Notes", "Category", "Location"]
    )
    
    fig.update_layout(
        title="Move Planning Timeline",
        xaxis_title="Date",
        yaxis_title="Items",
        height=600,  # Made taller
        showlegend=True,
        yaxis={'autorange': 'reversed'},
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Update the submit callback to handle the updated data format
@app.callback(
    Output("tasks-table", "data", allow_duplicate=True),
    Input("submit-button", "n_clicks"),
    [
        State("input-name", "value"),
        State("input-category", "value"),
        State("input-owner", "value"),
        State("input-notes", "value"),
        State({"type": "interval-location", "index": ALL}, "value"),
        State({"type": "interval-start", "index": ALL}, "date"),
        State({"type": "interval-end", "index": ALL}, "date"),
        State("tasks-table", "data"),
        State("tasks-table", "active_cell"),
        State("edit-mode-store", "data")
    ],
    prevent_initial_call=True
)
def handle_submit(n_clicks, name, category, owner, notes,
                 interval_locs, interval_starts, interval_ends, 
                 current_data, active_cell, is_edit_mode):
    if not n_clicks:
        return no_update
    
    intervals = []
    if interval_locs and interval_starts and interval_ends:
        for loc, start, end in zip(interval_locs, interval_starts, interval_ends):
            if loc and start and end:
                intervals.append({
                    "Location": loc,
                    "Start": start,
                    "End": end
                })
    
    try:
        if is_edit_mode and active_cell:
            # Update existing task
            row_index = active_cell['row']
            old_name = current_data[row_index]["Name"]
            db.update_item(
                old_name,
                name=name if name else "New Task",
                category=category if category else default_categories[0],
                owner=owner if owner else "",
                notes=notes if notes else "",
                intervals=intervals
            )
        else:
            # Add new task
            db.add_item(
                name=name if name else "New Task",
                category=category if category else default_categories[0],
                owner=owner if owner else "",
                notes=notes if notes else "",
                intervals=intervals
            )
        
        # Get fresh data from database
        updated_data = db.get_all_items()
        return [{
            "actions": "✏️",
            **row
        } for row in updated_data]
    except Exception as e:
        print(f"Error in handle_submit: {e}")
        return current_data

# Add a callback to handle row deletions
@app.callback(
    Output("tasks-table", "data", allow_duplicate=True),
    [Input("tasks-table", "data")],
    [State("tasks-table", "data_previous")],
    prevent_initial_call=True
)
def handle_row_deletion(current_data, previous_data):
    if not previous_data or not current_data:
        return no_update
    
    if len(current_data) < len(previous_data):
        try:
            # Find the deleted row
            deleted_row = next(row for row in previous_data if row not in current_data)
            print(f"Attempting to delete: {deleted_row['Name']}")
            
            # Delete from database
            db.delete_item(deleted_row["Name"])
            print(f"Successfully deleted from database: {deleted_row['Name']}")
            
            # Get fresh data
            updated_data = db.get_all_items()
            return [{
                "actions": "✏️",
                **row
            } for row in updated_data]
            
        except Exception as e:
            print(f"Error in deletion callback: {e}")
            import traceback
            traceback.print_exc()
            return current_data
    
    return no_update

@app.callback(
    Output("tasks-table", "data", allow_duplicate=True),
    Input("tasks-table", "data_timestamp"),
    State("tasks-table", "data"),
    State("tasks-table", "data_previous"),
    prevent_initial_call=True
)
def handle_table_edit(timestamp, current_data, previous_data):
    if not previous_data or not current_data:
        return no_update
    
    try:
        # Find the edited row by comparing current and previous data
        for i, (curr_row, prev_row) in enumerate(zip(current_data, previous_data)):
            if curr_row != prev_row:
                # Update the database with the new values
                db.update_item(
                    prev_row["Name"],  # Use previous name as identifier
                    name=curr_row["Name"],
                    category=curr_row["Category"],
                    owner=curr_row["Assigned Owner"],
                    notes=curr_row["Notes"],
                    intervals=json.loads(curr_row["Intervals"]) if curr_row["Intervals"] else []
                )
                print(f"Updated item: {prev_row['Name']} -> {curr_row['Name']}")
                
                # Get fresh data from database
                updated_data = db.get_all_items()
                return [{
                    "actions": "✏️",
                    **row
                } for row in updated_data]
    
    except Exception as e:
        print(f"Error updating item: {e}")
        import traceback
        traceback.print_exc()
        return previous_data
    
    return current_data

# Add callbacks for notes
@app.callback(
    Output("general-notes", "value"),
    Input("save-notes", "n_clicks"),
    State("general-notes", "value"),
    prevent_initial_call=True
)
def handle_notes(n_clicks, notes):
    if n_clicks:
        db.save_notes(notes)
    return db.get_notes()

if __name__ == '__main__':
    app.run(debug=True)

