from shiny import App, ui, render, reactive
import pandas as pd
import os
from pathlib import Path
import asyncio 

# Assuming interactive_graph_visualization.py is in the same directory or accessible in PYTHONPATH
from interactive_graph_visualization import create_interactive_heterogeneous_graph

# --- Configuration ---
DATA_BASE_PATH = "dataset/projects/"
ORG_FILE = os.path.join(DATA_BASE_PATH, "organization.xlsx")
PROJ_FILE = os.path.join(DATA_BASE_PATH, "project.xlsx")
TOPIC_FILE = os.path.join(DATA_BASE_PATH, "topics.xlsx")
GRAPH_OUTPUT_DIR = Path("graph") # This will be a directory at the same level as app.py
GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True) # Ensure the graph directory exists

# --- Load Data Globally (but reactively for Shiny context) ---
@reactive.calc
def load_data_reactive(): # Renamed to avoid confusion with a regular function
    print("Loading all data sources...")
    try:
        org_df = pd.read_excel(ORG_FILE)
        proj_df = pd.read_excel(PROJ_FILE)
        topic_df = pd.read_excel(TOPIC_FILE)
        print(f"Data loaded: {len(org_df)} orgs, {len(proj_df)} projects, {len(topic_df)} topics.")
        
        if 'name' not in org_df.columns or 'organisationID' not in org_df.columns:
            raise ValueError("Organization DataFrame must contain 'name' and 'organisationID' columns.")
        
        org_df_cleaned = org_df.dropna(subset=['name', 'organisationID'])
        
        org_options_df = org_df_cleaned[['name', 'organisationID']].copy() 
        org_options_df['organisationID'] = org_options_df['organisationID'].astype(str)
        org_options_df = org_options_df.drop_duplicates(subset=['organisationID'])

        org_options_df['display_name'] = org_options_df['name'] + " (" + org_options_df['organisationID'] + ")"
        org_options_df = org_options_df.sort_values(by='name')
        
        organization_choices = pd.Series(org_options_df.display_name.values, index=org_options_df.organisationID).to_dict()

        org_df['organisationID'] = org_df['organisationID'].astype(str)

        # Calculate Top 10 organizations by project participation
        if 'projectID' in org_df.columns:
            org_project_counts = org_df['organisationID'].value_counts()
            top_10_org_ids_list = org_project_counts.nlargest(10).index.astype(str).tolist()
        else:
            print("Warning: 'projectID' column not found in organization data for Top 10 calculation.")
            top_10_org_ids_list = []


        return {
            "org_df": org_df,
            "proj_df": proj_df,
            "topic_df": topic_df,
            "organization_choices": organization_choices,
            "all_org_ids": org_options_df.organisationID.tolist(),
            "top_10_org_ids": top_10_org_ids_list
        }
    except FileNotFoundError as e:
        print(f"ERROR: Data file not found: {e}")
        return {"org_df": pd.DataFrame(), "proj_df": pd.DataFrame(), "topic_df": pd.DataFrame(), "organization_choices": {"Error": f"Data loading failed: {e}"}, "all_org_ids": []}
    except ValueError as e:
        print(f"ERROR: Data processing error: {e}")
        return {"org_df": pd.DataFrame(), "proj_df": pd.DataFrame(), "topic_df": pd.DataFrame(), "organization_choices": {"Error": f"Data processing failed: {e}"}, "all_org_ids": []}
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during data loading: {e}")
        import traceback
        traceback.print_exc()
        return {"org_df": pd.DataFrame(), "proj_df": pd.DataFrame(), "topic_df": pd.DataFrame(), "organization_choices": {"Error": f"Unexpected error: {e}"}, "all_org_ids": []}
# --- Shiny UI Definition ---
app_ui = ui.page_fluid(
    ui.panel_title("Interactive Heterogeneous Network Visualization"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.card(
                ui.card_header("Graph Controls"),
                ui.input_selectize(
                    "selected_orgs_ids", 
                    "Select Organizations:",
                    choices={}, 
                    multiple=True
                ),
                ui.input_action_button("update_graph", "Update Graph", class_="btn-primary w-100 mb-2"),
                ui.hr(),
                ui.h5("Quick Actions"),
                ui.input_action_button("select_top_10", "Select Top 10 Orgs (by Projects)", class_="btn-info w-100 mb-2"),
                ui.input_action_button("clear_selection", "Clear Selection & Graph", class_="btn-warning w-100"),
            ),
            # title="Controls" # Replaced by card header
        ),
        ui.output_ui("pyvis_graph_display"),
        ui.output_text_verbatim("status_message")
    )
)

# --- Shiny Server Logic ---
def server(input, output, session):
    # Get the loaded data by calling the reactive calc
    # This will be a dictionary or the error dictionary from load_data_reactive
    # app_data = load_data_reactive() # Incorrect: this calls the calc immediately
    
    # Correct: Assign the reactive calculation itself. It will be called (executed)
    # when its value is requested by another reactive function (effect, output).
    loaded_data_reactive_calc = load_data_reactive 

    @reactive.effect
    def _update_org_choices():
        # Access the dictionary returned by the reactive calc by CALLING it.
        current_data = loaded_data_reactive_calc() # Call the reactive calc to get its current value
        choices = current_data.get("organization_choices", {"Error": "Choices not available"})
        if "Error" in choices:
             print(f"Error in choices for dropdown: {choices['Error']}") 
        ui.update_selectize(
            "selected_orgs_ids",
            choices=choices,
            selected=None 
        )
        print("Organization choices updated in UI.")

    graph_html_file_reactive = reactive.value(None) # Stores the relative path for the iframe src
    current_status_message = reactive.value("Please select organizations and click 'Update Graph'.") # Initialize status message

    @reactive.effect
    @reactive.event(input.select_top_10)
    def _handle_select_top_10():
        current_data = loaded_data_reactive_calc()
        top_10_ids = current_data.get("top_10_org_ids", [])
        if top_10_ids:
            ui.update_selectize("selected_orgs_ids", selected=top_10_ids)
            current_status_message.set(f"{len(top_10_ids)} Top organizations selected. Click 'Update Graph'.")
        else:
            current_status_message.set("Could not determine Top 10 organizations. Data might be missing.")

    @reactive.effect
    @reactive.event(input.clear_selection)
    def _handle_clear_selection():
        ui.update_selectize("selected_orgs_ids", selected=[]) # Clear dropdown
        graph_html_file_reactive.set(None) # Clear the displayed graph
        current_status_message.set("Selection cleared. Graph removed.")


    @reactive.effect
    @reactive.event(input.update_graph)
    async def _generate_and_save_graph():
        print("Update graph button clicked.")
        current_data = loaded_data_reactive_calc() # Get current data from reactive calc
        org_df = current_data.get("org_df")
        proj_df = current_data.get("proj_df")
        topic_df = current_data.get("topic_df")
        
        selected_ids_tuple = input.selected_orgs_ids() 
        print(f"Selected organization IDs from input: {selected_ids_tuple}")

        if not selected_ids_tuple:
            # await output.set("status_message", "Please select at least one organization.") # Old way
            current_status_message.set("Please select at least one organization.")
            graph_html_file_reactive.set(None) 
            return

        if org_df.empty or proj_df.empty or topic_df.empty or "Error" in current_data.get("organization_choices", {}):
            # await output.set("status_message", "Data not loaded correctly or error in data. Cannot generate graph.") # Old way
            current_status_message.set("Data not loaded correctly or error in data. Cannot generate graph.")
            graph_html_file_reactive.set(None)
            return
        
        selected_ids_list = list(selected_ids_tuple) # These are string IDs from selectize

        print(f"Calling create_interactive_heterogeneous_graph with {len(selected_ids_list)} organization IDs.")
        
        # Pass copies of dataframes to avoid modifying the original reactive data
        net = create_interactive_heterogeneous_graph(org_df.copy(), proj_df.copy(), topic_df.copy(), selected_ids_list)

        if net and hasattr(net, 'nodes'): # Basic check if 'net' is a valid PyVis network object
            # Save graph to a file within the configured static assets directory (GRAPH_OUTPUT_DIR)
            # The filename includes session.id for uniqueness if multiple sessions occur.
            filename = f"interactive_graph_{session.id}.html"
            absolute_path_to_save = GRAPH_OUTPUT_DIR / filename
            
            try:
                net.save_graph(str(absolute_path_to_save))
                print(f"Graph saved to: {absolute_path_to_save}")
                
                # For iframe src, we need path relative to how static_assets is configured.
                # If static_assets={"/graph_assets": "graph"}, then src = "/graph_assets/filename.html"
                iframe_src_path = f"/{GRAPH_OUTPUT_DIR.name}/{filename}" 
                graph_html_file_reactive.set(iframe_src_path) 
                # await output.set("status_message", f"Graph generated for {len(selected_ids_list)} organization(s). View below.") # Old way
                current_status_message.set(f"Graph generated for {len(selected_ids_list)} organization(s). View below.")
            except Exception as e:
                print(f"Error saving graph: {e}")
                import traceback; traceback.print_exc()
                # await output.set("status_message", f"Error saving graph: {e}") # Old way
                current_status_message.set(f"Error saving graph: {str(e)}")
                graph_html_file_reactive.set(None)
        else:
            print("Graph generation failed or returned an invalid network object.")
            # await output.set("status_message", "Graph generation failed. Check logs for details.") # Old way
            current_status_message.set("Graph generation failed. Check logs for details.")
            graph_html_file_reactive.set(None)

    @output
    @render.ui
    async def pyvis_graph_display():
        iframe_src = graph_html_file_reactive.get()
        if iframe_src:
            filename = Path(iframe_src).name
            expected_file_path = GRAPH_OUTPUT_DIR / filename
            if os.path.exists(expected_file_path):
                print(f"Rendering iframe with src: {iframe_src}")
                return ui.HTML(f'''
                    <iframe src="{iframe_src}" width="100%" height="850px" style="border:none;" title="Pyvis Graph"></iframe>
                ''')
            else:
                print(f"Graph file {expected_file_path} does not exist. Iframe src was {iframe_src}.")
                return ui.TagList(
                    ui.p(f"Graph file expected at {expected_file_path} not found."),
                    ui.p("Please check selection and try updating again. Detailed status below.")
                )
        else:
             return ui.p("Graph will appear here. Select organizations and click 'Update Graph'.")

    @output
    @render.text
    def status_message():
        return current_status_message.get()

# --- App Instantiation ---
# Serve files from GRAPH_OUTPUT_DIR (e.g. "graph" directory in app's root)
# under the URL path that is the name of the directory (e.g. "/graph")

# Ensure GRAPH_OUTPUT_DIR is an absolute path for static_assets
app_dir = Path(__file__).parent
absolute_graph_dir = app_dir / GRAPH_OUTPUT_DIR.name # GRAPH_OUTPUT_DIR is already Path("graph")

# The static_assets value needs to be an absolute path to the directory on the filesystem.
# GRAPH_OUTPUT_DIR is Path("graph"). To make it absolute relative to app.py:
absolute_graph_path_for_static_assets = Path(__file__).resolve().parent / GRAPH_OUTPUT_DIR.name

app = App(
    app_ui, 
    server, 
    static_assets={f"/{GRAPH_OUTPUT_DIR.name}": str(absolute_graph_path_for_static_assets)}
)

# To run this app:
# Install dependencies: pip install shiny pandas openpyxl pyvis networkx
# Run from terminal: python -m shiny run app.py
