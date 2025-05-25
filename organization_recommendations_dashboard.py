import json
import pandas as pd
from shiny import App, ui, render, reactive
from pathlib import Path

# Load the recommendations data
def load_recommendations():
    """Load the recommendations data from JSON file"""
    try:
        with open("dataset/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

# Load data
recommendations_data = load_recommendations()
organization_list = sorted(list(recommendations_data.keys()))

# Define UI
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
            .select-input {
                margin-bottom: 1.5rem;
            }
        """)
    ),
    
    # Header
    ui.div(
        ui.h1("🤝 Organization Collaboration Recommendations", class_="main-header"),
        class_="container-fluid"
    ),
    
    # Main content
    ui.div(
        ui.row(
            ui.column(
                4,
                ui.div(
                    ui.h3("Select Organization", style="color: #2c3e50; margin-bottom: 1rem;"),
                    ui.input_selectize(
                        "selected_org",
                        "",
                        choices=organization_list,
                        selected=organization_list[0] if organization_list else None,
                        options={"placeholder": "Type to search organizations..."}
                    ),
                    ui.br(),
                    ui.div(
                        ui.h4("📊 Quick Stats", style="color: #2c3e50;"),
                        ui.output_text("stats_text"),
                        style="background: #e8f4f8; padding: 1rem; border-radius: 8px; margin-top: 1rem;"
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
        ),
        class_="container-fluid"
    ),
    
    # Footer
    ui.div(
        ui.hr(),
        ui.p(
            "💡 This dashboard helps identify the most likely collaboration partners for your next funding round based on the Graph Autoencoder(GAE).",
            style="text-align: center; color: #6c757d; margin-top: 2rem;"
        ),
        class_="container-fluid"
    )
)

# Define server logic
def server(input, output, session):
    
    @output
    @render.ui
    def recommendations_output():
        selected = input.selected_org()
        
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
        
        # Create recommendation cards
        recommendation_cards = []
        for i, (org_name, score) in enumerate(recommendations[:5], 1):
            card = ui.div(
                ui.div(
                    ui.span(f"#{i}", style="color: #667eea; font-weight: bold; margin-right: 0.5rem;"),
                    ui.span(org_name.title(), class_="organization-name"),
                    ui.span(f"{score:.2f}", class_="score-badge"),
                    style="clear: both;"
                ),
                class_="recommendation-item"
            )
            recommendation_cards.append(card)
        
        return ui.div(*recommendation_cards)
    
    @output
    @render.text
    def stats_text():
        selected = input.selected_org()
        
        if not selected or selected not in recommendations_data:
            return "Select an organization to see statistics."
        
        recommendations = recommendations_data[selected]
        total_orgs = len(recommendations_data)
        avg_score = sum(score for _, score in recommendations) / len(recommendations) if recommendations else 0
        
        return f"""
        📈 Total organizations in database: {total_orgs:,}
        🎯 Recommendations available: {len(recommendations)}
        ⭐ Average recommendation score: {avg_score:.2f}
        """

# Create the app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run() 