from shiny import App, ui, render, reactive
import pandas as pd
import json
import os
from pathlib import Path
import asyncio 
from interactive_graph_visualization import create_interactive_heterogeneous_graph

# --- Configuration of Relative Paths ---
DATA_BASE_PATH = "dataset/projects/"
ORG_FILE = os.path.join(DATA_BASE_PATH, "organization.xlsx")
PROJ_FILE = os.path.join(DATA_BASE_PATH, "project.xlsx")
TOPIC_FILE = os.path.join(DATA_BASE_PATH, "topics.xlsx")
RECOMMENDATIONS_FILE = "dataset/data.json"
GRAPH_OUTPUT_DIR = Path("graph")
GRAPH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load Recommendations Data 
def load_recommendations():
    """Load the recommendations data from JSON file"""
    try:
        with open(RECOMMENDATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading recommendations data: {e}")
        return {}

# Load Data Reactively ---
@reactive.calc
def load_data_reactive():
    """Load all data sources reactively"""
    print("Loading all data sources...")
    try:
        # Load Excel data
        org_df = pd.read_excel(ORG_FILE)
        proj_df = pd.read_excel(PROJ_FILE)
        topic_df = pd.read_excel(TOPIC_FILE)
        
        # Load recommendations data
        recommendations_data = load_recommendations()
        
        print(f"Data loaded: {len(org_df)} orgs, {len(proj_df)} projects, {len(topic_df)} topics, {len(recommendations_data)} recommendation entries.")
        
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

        # Create recommendation choices (intersection of org data and recommendations)
        recommendation_orgs = list(recommendations_data.keys())
        
        return {
            "org_df": org_df,
            "proj_df": proj_df,
            "topic_df": topic_df,
            "recommendations_data": recommendations_data,
            "organization_choices": organization_choices,
            "all_org_ids": org_options_df.organisationID.tolist(),
            "top_10_org_ids": top_10_org_ids_list,
            "recommendation_orgs": sorted(recommendation_orgs)
        }
    except FileNotFoundError as e:
        print(f"ERROR: Data file not found: {e}")
        return {"org_df": pd.DataFrame(), "proj_df": pd.DataFrame(), "topic_df": pd.DataFrame(), 
                "recommendations_data": {}, "organization_choices": {"Error": f"Data loading failed: {e}"}, 
                "all_org_ids": [], "recommendation_orgs": []}
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during data loading: {e}")
        import traceback
        traceback.print_exc()
        return {"org_df": pd.DataFrame(), "proj_df": pd.DataFrame(), "topic_df": pd.DataFrame(), 
                "recommendations_data": {}, "organization_choices": {"Error": f"Unexpected error: {e}"}, 
                "all_org_ids": [], "recommendation_orgs": []}

# UI 
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                margin-bottom: 2rem;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .card {
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            .recommendation-item {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 5px;
                transition: transform 0.2s;
            }
            .recommendation-item:hover {
                transform: translateX(5px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            }
            .score-badge {
                background: #667eea;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: bold;
                float: right;
            }
            .organization-name {
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 0.5rem;
            }
            .network-controls {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            .stats-box {
                background: #e8f4f8;
                padding: 1rem;
                border-radius: 8px;
                margin-top: 1rem;
            }
        """)
    ),
    
    # Header
    ui.div(
        ui.h1("🌐 Organization Network & Collaboration Prediction", class_="main-header"),
        class_="container-fluid"
    ),
    
    # Navigation Tabs
    ui.navset_tab(
        ui.nav_panel(
            "🔗 Network Visualization",
            ui.layout_sidebar(
                ui.sidebar(
                    ui.div(
                        ui.h4("Graph Controls", style="color: #2c3e50; margin-bottom: 1rem;"),
                        ui.input_selectize(
                            "network_selected_orgs_ids", 
                            "Select Organizations:",
                            choices={}, 
                            multiple=True,
                            options={"placeholder": "Search and select organizations..."}
                        ),
                        ui.br(),
                        ui.input_action_button("update_graph", "🎯 Update Graph", class_="btn-primary w-100 mb-2"),
                        ui.hr(),
                        ui.h5("Quick Actions", style="color: #2c3e50;"),
                        ui.input_action_button("select_top_10", "📊 Select Top 10 Orgs", class_="btn-info w-100 mb-2"),
                        ui.input_action_button("clear_selection", "🗑️ Clear Selection", class_="btn-warning w-100"),
                        class_="network-controls"
                    ),
                    width=300
                ),
                ui.div(
                    ui.output_ui("pyvis_graph_display"),
                    ui.br(),
                    ui.output_text_verbatim("network_status_message"),
                    class_="card"
                )
            )
        ),
        
        ui.nav_panel(
            "🤝 Collaboration Recommendations", 
            ui.row(
                ui.column(
                    4,
                    ui.div(
                        ui.h3("Select Organization", style="color: #2c3e50; margin-bottom: 1rem;"),
                        ui.input_selectize(
                            "recommendations_selected_org",
                            "",
                            choices=[],
                            selected=None,
                            options={"placeholder": "Type to search organizations..."}
                        ),
                        ui.div(
                            ui.h4("📊 Statistics", style="color: #2c3e50;"),
                            ui.output_text("recommendation_stats_text"),
                            class_="stats-box"
                        ),
                        class_="card"
                    )
                ),
                ui.column(
                    8,
                    ui.div(
                        ui.h3("🎯 Top 5 Collaboration Recommendations", style="color: #2c3e50; margin-bottom: 1.5rem;"),
                        ui.output_ui("recommendations_output"),
                        class_="card"
                    )
                )
            )
        ),
    )
)

# Server Logic 
def server(input, output, session):
    loaded_data_reactive_calc = load_data_reactive
    
    # Reactive values for managing state
    graph_html_file_reactive = reactive.value(None)
    network_status_message_reactive = reactive.value("Please select organizations and click 'Update Graph'.")
    
    # Update organization choices for both tabs
    @reactive.effect
    def _update_choices():
        current_data = loaded_data_reactive_calc()
        network_choices = current_data.get("organization_choices", {"Error": "Choices not available"})
        recommendation_choices = current_data.get("recommendation_orgs", [])
        
        # Update network visualization choices
        ui.update_selectize("network_selected_orgs_ids", choices=network_choices, selected=None)
        
        # Update recommendation choices
        ui.update_selectize("recommendations_selected_org", choices=recommendation_choices, 
                          selected=recommendation_choices[0] if recommendation_choices else None)
        
        print("Organization choices updated in both tabs.")
    
    # Network Visualization Logic
    @reactive.effect
    @reactive.event(input.select_top_10)
    def _handle_select_top_10():
        current_data = loaded_data_reactive_calc()
        top_10_ids = current_data.get("top_10_org_ids", [])
        if top_10_ids:
            ui.update_selectize("network_selected_orgs_ids", selected=top_10_ids)
            network_status_message_reactive.set(f"{len(top_10_ids)} Top organizations selected. Click 'Update Graph'.")
        else:
            network_status_message_reactive.set("Could not determine Top 10 organizations. Data might be missing.")

    @reactive.effect
    @reactive.event(input.clear_selection)
    def _handle_clear_selection():
        ui.update_selectize("network_selected_orgs_ids", selected=[])
        graph_html_file_reactive.set(None)
        network_status_message_reactive.set("Selection cleared. Graph removed.")

    @reactive.effect
    @reactive.event(input.update_graph)
    async def _generate_and_save_graph():
        print("Update graph button clicked.")
        current_data = loaded_data_reactive_calc()
        org_df = current_data.get("org_df")
        proj_df = current_data.get("proj_df")
        topic_df = current_data.get("topic_df")
        
        selected_ids_tuple = input.network_selected_orgs_ids()
        print(f"Selected organization IDs from input: {selected_ids_tuple}")

        if not selected_ids_tuple:
            network_status_message_reactive.set("Please select at least one organization.")
            graph_html_file_reactive.set(None)
            return

        if org_df.empty or proj_df.empty or topic_df.empty:
            network_status_message_reactive.set("Data not loaded correctly. Cannot generate graph.")
            graph_html_file_reactive.set(None)
            return
        
        selected_ids_list = list(selected_ids_tuple)
        print(f"Calling create_interactive_heterogeneous_graph with {len(selected_ids_list)} organization IDs.")
        
        net = create_interactive_heterogeneous_graph(org_df.copy(), proj_df.copy(), topic_df.copy(), selected_ids_list)

        if net and hasattr(net, 'nodes'):
            filename = f"interactive_graph_{session.id}.html"
            absolute_path_to_save = GRAPH_OUTPUT_DIR / filename
            
            try:
                net.save_graph(str(absolute_path_to_save))
                print(f"Graph saved to: {absolute_path_to_save}")
                
                iframe_src_path = f"/{GRAPH_OUTPUT_DIR.name}/{filename}"
                graph_html_file_reactive.set(iframe_src_path)
                network_status_message_reactive.set(f"Graph generated for {len(selected_ids_list)} organization(s). View below.")
            except Exception as e:
                print(f"Error saving graph: {e}")
                network_status_message_reactive.set(f"Error saving graph: {str(e)}")
                graph_html_file_reactive.set(None)
        else:
            print("Graph generation failed or returned an invalid network object.")
            network_status_message_reactive.set("Graph generation failed. Check logs for details.")
            graph_html_file_reactive.set(None)

    # Output renderers
    @output
    @render.ui
    def pyvis_graph_display():
        iframe_src = graph_html_file_reactive.get()
        if iframe_src:
            filename = Path(iframe_src).name
            expected_file_path = GRAPH_OUTPUT_DIR / filename
            if os.path.exists(expected_file_path):
                return ui.HTML(f'''
                    <iframe src="{iframe_src}" width="100%" height="850px" style="border:none;" title="Pyvis Graph"></iframe>
                ''')
            else:
                return ui.TagList(
                    ui.p(f"Graph file expected at {expected_file_path} not found."),
                    ui.p("Please check selection and try updating again.")
                )
        else:
            return ui.p("📊 Graph will appear here. Select organizations and click 'Update Graph'.", 
                       style="text-align: center; color: #6c757d; font-style: italic; padding: 2rem;")

    @output
    @render.text
    def network_status_message():
        return network_status_message_reactive.get()

    # Recommendations Logic
    @output
    @render.ui
    def recommendations_output():
        selected = input.recommendations_selected_org()
        current_data = loaded_data_reactive_calc()
        recommendations_data = current_data.get("recommendations_data", {})
        
        if not selected or selected not in recommendations_data:
            return ui.div(
                ui.p("Please select an organization to see recommendations.", 
                     style="text-align: center; color: #6c757d; font-style: italic;"),
                style="padding: 2rem;"
            )
        
        recommendations = recommendations_data[selected]
        
        if not recommendations:
            return ui.div(
                ui.p("No recommendations available for this organization.", 
                     style="text-align: center; color: #6c757d; font-style: italic;"),
                style="padding: 2rem;"
            )
        
        recommendation_cards = []
        for i, (org_name, score) in enumerate(recommendations[:5], 1):
            card = ui.div(
                ui.div(
                    ui.span(f"#{i}", style="color: #667eea; font-weight: bold; margin-right: 0.5rem;"),
                    ui.span(org_name.title(), class_="organization-name"),
                    ui.span(f"{score:.3f}", class_="score-badge"),
                    style="clear: both;"
                ),
                class_="recommendation-item"
            )
            recommendation_cards.append(card)
        
        return ui.div(*recommendation_cards)
    
    @output
    @render.text
    def recommendation_stats_text():
        selected = input.recommendations_selected_org()
        current_data = loaded_data_reactive_calc()
        recommendations_data = current_data.get("recommendations_data", {})
        
        if not selected or selected not in recommendations_data:
            return "Select an organization to see statistics."
        
        recommendations = recommendations_data[selected]
        total_orgs = len(recommendations_data)
        avg_score = sum(score for _, score in recommendations) / len(recommendations) if recommendations else 0
        
        return f"""📈 Total organizations in database: {total_orgs:,}. 
        
        \n\n

        Predictions is made by Graph Autoencoders (GAE) Model."""


# App Instantiation ---
app_dir = Path(__file__).parent
absolute_graph_path_for_static_assets = app_dir / GRAPH_OUTPUT_DIR.name

app = App(
    app_ui, 
    server, 
    static_assets={f"/{GRAPH_OUTPUT_DIR.name}": str(absolute_graph_path_for_static_assets)}
)

# To run this app:
# - Install dependencies: pip install -r dependencies.txt
# - Run the app in terminal: python -m shiny run app.py