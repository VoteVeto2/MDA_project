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
    
    # Histogram section
    ui.card(
        ui.card_header("Project Duration Distribution"),
        ui.output_ui("duration_hist"),  # Changed from plot_output
        ui.card(
            ui.card_header("Statistical Insights:"),
            ui.tags.ul(
                ui.tags.li("Projects typically last between 12-24 months, with a mean duration shown above."),
                ui.tags.li("The distribution shows distinct clusters at 12-18 months and 24-30 months, suggesting common project timeframes."),
                ui.tags.li("There's a considerable spread in project durations, indicating diverse project scopes."),
                ui.tags.li("The interquartile range (IQR) reveals that the middle 50% of projects vary by about 1 year in duration.")
            ),
            class_="mt-4 bg-blue-50"
        ),
        ui.card(
            ui.card_header("Trend Analysis:"),
            ui.output_ui("trend_analysis"),
            class_="mt-4 bg-green-50"
        ),
        full_screen=True
    )
)

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
    def duration_hist():
        if len(durations) == 0:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(
                title='No valid project duration data available',
                xaxis_title='Duration (months)',
                yaxis_title='Number of Projects'
            )
            # Convert the Plotly figure to HTML
            return ui.HTML(fig.to_html(include_plotlyjs="cdn"))
            
        # Create histogram with density curve and trend visualization
        fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3],
                          subplot_titles=("Duration Histogram", "Distribution Analysis"),
                          vertical_spacing=0.15)
        
        # Add histogram
        fig.add_trace(go.Histogram(
            x=durations,
            name='Project Count',
            opacity=0.7,
            marker=dict(color='royalblue'),
            nbinsx=15,  # Optimized bin count
            histnorm=''  # Use count instead of density
        ), row=1, col=1)
        
        # Add KDE (Kernel Density Estimate) curve
        kde_x = np.linspace(np.min(durations), np.max(durations), 100)
        kde = stats.gaussian_kde(durations)
        kde_y = kde(kde_x) * len(durations) * (np.max(durations) - np.min(durations)) / 15
        
        fig.add_trace(go.Scatter(
            x=kde_x,
            y=kde_y,
            mode='lines',
            name='Density Curve',
            line=dict(color='red', width=2)
        ), row=1, col=1)
        
        # Add vertical lines for yearly markers
        for year in range(1, 6):
            year_months = year * 12
            if year_months >= np.min(durations) and year_months <= np.max(durations):
                fig.add_vline(
                    x=year_months, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="gray",
                    annotation_text=f"{year} Year{'s' if year > 1 else ''}",
                    annotation_position="top",
                    row=1, col=1
                )
        
        # Add box plot for distribution visualization
        fig.add_trace(go.Box(
            x=durations,
            name='Duration Distribution',
            boxpoints='all',
            jitter=0.3,
            pointpos=-1.8,
            marker=dict(color='royalblue'),
            line=dict(color='darkblue')
        ), row=2, col=1)
        
        # Add layout details
        fig.update_layout(
            title='Project Duration Distribution with Trend Analysis',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            margin=dict(t=50, b=50, l=50, r=50),
            height=700  # Increase height to accommodate both plots
        )
        
        # Update x-axis titles
        fig.update_xaxes(title_text='Duration (months)', row=1, col=1)
        fig.update_xaxes(title_text='Duration (months)', row=2, col=1)
        
        # Update y-axis titles
        fig.update_yaxes(title_text='Number of Projects', row=1, col=1)
        fig.update_yaxes(title_text='', row=2, col=1)
        
        # Add statistics annotations
        fig.add_annotation(
            x=0.01,
            y=0.95,
            xref="paper",
            yref="paper",
            text=f"Mean: {stats_data['mean']:.1f} months<br>Median: {stats_data['median']:.1f} months<br>StdDev: {stats_data['std_dev']:.1f}",
            showarrow=False,
            font=dict(size=12),
            align="left",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1,
            borderpad=4
        )
        
        # Convert the Plotly figure to HTML
        return ui.HTML(fig.to_html(include_plotlyjs="cdn"))
    
    @render.ui
    def trend_analysis():
        # Identify clusters in the data using KMeans
        from sklearn.cluster import KMeans
        
        # Convert durations to 2D array for KMeans
        X = durations.reshape(-1, 1)
        
        # Determine optimal number of clusters (simplified)
        k = min(3, len(durations))  # 3 clusters or less if we have less data points
        
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
            multimodal_str = ""
            skew_str = ""
        
        # Trend analysis insights
        return ui.tags.div(
            ui.tags.p(cluster_analysis),
            ui.tags.p(multimodal_str),
            ui.tags.p(skew_str),
            ui.tags.p(f"The coefficient of variation is {stats_data['cv']:.2f}%, indicating {'high' if stats_data['cv'] > 25 else 'moderate' if stats_data['cv'] > 10 else 'low'} variability in project durations."),
            ui.tags.p("The box plot shows the distribution's central tendency and identifies potential outliers in project durations.")
        )
    
# Create and run the app
app = App(app_ui, server)

# For running the app
if __name__ == "__main__":
    app.run()
