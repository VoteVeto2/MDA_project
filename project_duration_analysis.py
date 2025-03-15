import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from shiny import App, ui, render
from pathlib import Path

# Define the UI
app_ui = ui.page_fluid(
    ui.h1("Project Duration Analysis", align="center"),
    
    # Statistics cards section
    ui.card(
        ui.card_header("Duration Statistics"),
        ui.layout_columns(
            ui.value_box(
                "Sample Size",
                ui.output_text("count"),
                showcase=ui.output_text("count_unit"),
                theme="bg-blue-50"
            ),
            ui.value_box(
                "Mean",
                ui.output_text("mean"),
                showcase=ui.output_text("mean_unit"),
                theme="bg-blue-50"
            ),
            ui.value_box(
                "Median",
                ui.output_text("median"),
                showcase=ui.output_text("median_unit"),
                theme="bg-blue-50"
            ),
            ui.value_box(
                "Standard Deviation",
                ui.output_text("std_dev"),
                showcase=ui.output_text("std_dev_unit"),
                theme="bg-blue-50"
            ),
            col_widths=[3, 3, 3, 3]
        ),
        ui.layout_columns(
            ui.value_box(
                "Minimum",
                ui.output_text("min"),
                showcase=ui.output_text("min_unit"),
                theme="bg-blue-50"
            ),
            ui.value_box(
                "Maximum",
                ui.output_text("max"),
                showcase=ui.output_text("max_unit"),
                theme="bg-blue-50"
            ),
            ui.value_box(
                "Q1 (25th percentile)",
                ui.output_text("q1"),
                showcase=ui.output_text("q1_unit"),
                theme="bg-blue-50"
            ),
            ui.value_box(
                "Q3 (75th percentile)",
                ui.output_text("q3"),
                showcase=ui.output_text("q3_unit"),
                theme="bg-blue-50"
            ),
            col_widths=[3, 3, 3, 3]
        ),
        ui.card(
            ui.card_header("Coefficient of Variation"),
            ui.output_text("cv"),
            class_="mt-4 bg-yellow-50"
        ),
        full_screen=True
    ),
    
    # Add Trend Analysis card
    ui.card(
        ui.card_header("Trend Analysis"),
        ui.output_ui("trend_analysis"),
        class_="mt-4",
        full_screen=True
    ),
    
    # Add Duration Distribution card
    ui.card(
        ui.card_header("Duration Distribution"),
        ui.output_ui("duration_plot"),  # Changed from output_plot to output_ui
        class_="mt-4",
        full_screen=True
    ),
)

# Move perform_trend_analysis outside server function
def perform_trend_analysis(durations):
    # Identify clusters in the data using KMeans
    from sklearn.cluster import KMeans
    
    # Convert durations to 2D array for KMeans
    X = durations.reshape(-1, 1)
    
    # Determine optimal number of clusters (simplified)
    k = min(3, len(durations))  # 3 clusters or less if we have less data points
    
    skew_str = ""
    multimodal_str = ""
    cluster_analysis = ""
    
    if len(durations) >= 5:  # Only perform clustering with enough data
        kmeans = KMeans(n_clusters=k, random_state=42).fit(X)
        centers = kmeans.cluster_centers_.flatten()
        centers_str = ", ".join([f"{center:.1f} months" for center in sorted(centers)])
        
        # Check for bimodal distribution
        if k >= 2 and len(durations) >= 10:
            # Calculate Hartigan's dip test for unimodality
            try:
                from diptest import diptest
                dip, pval = diptest(durations)
                is_multimodal = pval < 0.05
                multimodal_str = f"The distribution appears to be {'multimodal' if is_multimodal else 'unimodal'}."
            except:
                multimodal_str = ""
        else:
            multimodal_str = ""
            
        # Skewness calculation
        skewness = stats.skew(durations)
        if abs(skewness) < 0.5:
            skew_str = "The distribution is approximately symmetric."
        elif skewness > 0:
            skew_str = f"The distribution is positively skewed (skewness: {skewness:.2f}), indicating a tail toward longer project durations."
        else:
            skew_str = f"The distribution is negatively skewed (skewness: {skewness:.2f}), indicating a tail toward shorter project durations."
            
        cluster_analysis = f"Analysis identified {k} potential duration clusters centered at {centers_str}."
    else:
        cluster_analysis = "Insufficient data for cluster analysis."
        
    return {
        "cluster_analysis": cluster_analysis,
        "multimodal_str": multimodal_str,
        "skew_str": skew_str
    }

# Define the server
def server(input, output, session):
    # Calculate project durations and statistics
    def get_project_durations():
        # Load project data
        df = pd.read_excel('dataset/projects/project.xlsx')
        
        # Calculate durations in months
        durations = []
        for _, row in df.iterrows():
            try:
                if pd.notna(row['startDate']) and pd.notna(row['endDate']):
                    # Check if date format is valid
                    if isinstance(row['startDate'], str) and isinstance(row['endDate'], str):
                        if row['startDate'].count('-') == 2 and row['endDate'].count('-') == 2:
                            start_date = datetime.strptime(row['startDate'], '%Y-%m-%d')
                            end_date = datetime.strptime(row['endDate'], '%Y-%m-%d')
                            
                            # Calculate duration in months (approximate)
                            duration_months = (end_date - start_date).days / 30
                            
                            # Filter out unreasonable durations
                            if 0 < duration_months < 120:  # Sanity check
                                durations.append(duration_months)
            except:
                # Skip if there are parsing issues
                continue
                
        return np.array(durations)
    
    # Get durations once
    durations = get_project_durations()
    
    # Calculate statistics
    stats_data = {
        'count': len(durations),
        'mean': np.mean(durations),
        'median': np.median(durations),
        'std_dev': np.std(durations),
        'min': np.min(durations),
        'max': np.max(durations),
        'q1': np.percentile(durations, 25),
        'q3': np.percentile(durations, 75),
        'iqr': np.percentile(durations, 75) - np.percentile(durations, 25),
        'cv': (np.std(durations) / np.mean(durations)) * 100
    }
    
    # Output renderers
    @render.text
    def count():
        return f"{stats_data['count']}"
    
    @render.text
    def count_unit():
        return "projects"
    
    @render.text
    def mean():
        return f"{stats_data['mean']:.2f}"
    
    @render.text
    def mean_unit():
        return "months"
    
    @render.text
    def median():
        return f"{stats_data['median']:.2f}"
    
    @render.text
    def median_unit():
        return "months"
    
    @render.text
    def std_dev():
        return f"{stats_data['std_dev']:.2f}"
    
    @render.text
    def std_dev_unit():
        return "months"
    
    @render.text
    def min():
        return f"{stats_data['min']:.2f}"
    
    @render.text
    def min_unit():
        return "months"
    
    @render.text
    def max():
        return f"{stats_data['max']:.2f}"
    
    @render.text
    def max_unit():
        return "months"
    
    @render.text
    def q1():
        return f"{stats_data['q1']:.2f}"
    
    @render.text
    def q1_unit():
        return "months"
    
    @render.text
    def q3():
        return f"{stats_data['q3']:.2f}"
    
    @render.text
    def q3_unit():
        return "months"
    
    @render.text
    def cv():
        return f"{stats_data['cv']:.2f}% (Measures relative variability)"
    
    @render.ui
    def trend_analysis():
        # Get analysis results
        analysis_results = perform_trend_analysis(durations)
        
        # Return trend analysis insights
        return ui.tags.div(
            ui.tags.p(analysis_results["cluster_analysis"]),
            ui.tags.p(analysis_results["multimodal_str"]),
            ui.tags.p(analysis_results["skew_str"]),
            ui.tags.p(f"The coefficient of variation is {stats_data['cv']:.2f}%, indicating {'high' if stats_data['cv'] > 25 else 'moderate' if stats_data['cv'] > 10 else 'low'} variability in project durations."),
            ui.tags.p("")
        )
    
    @render.ui
    def duration_plot():
        import plotly.express as px
        import plotly.offline as offline
        
        # Create histogram
        fig = px.histogram(durations, x=durations, nbins=30, title="Distribution of Project Durations (Months)")
        
        # Generate HTML representation of the plot
        plot_html = offline.plot(fig, include_plotlyjs=True, output_type='div')
        
        # Return the HTML content
        return ui.HTML(plot_html)

# Create and run the app
app = App(app_ui, server)

# For running the app
if __name__ == "__main__":
    app.run()
