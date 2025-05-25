# 🌐 Organization Network & Collaboration Prediction Platform

An interactive platform for analyzing European research collaboration networks and predicting future partnerships using Graph Autoencoder (GAE). This project provides interactive visualizations and machine learning-powered recommendations for research organizations seeking collaboration opportunities.

## 🎯 Project Overview

This platform visulaize collaboration pbetween research organizations, universities, and companies under HORIZON EUROPE (2021-2027). Using advanced graph neural networks and network analysis techniques, it provides:

- **Comprehensive Analytics Dashboard**: Detailed statistics and insights about research collaboration patterns (see ([EU-research repository](https://github.com/VoteVeto2/EU-research))) 
- **Interactive Network Visualization**: Explore heterogeneous networks of organizations, projects, and research topics.
- **Data Processing Pipeline**: Tools for cleaning and preprocessing large-scale research datasets
- **AI-Powered Collaboration Recommendations**: Get top-5 partnership suggestions using Graph Autoencoder models


## 🏗️ Architecture & Features

### Core Components

1. **Descriptive Data Analytics Module** (`Descriptive_Statistics.py`)
   - Network topology analysis
   - Country collaboration patterns
   - Research topic clustering
   - Deploy online in [EU Research Network](https://eu-research-visualization.netlify.app/)

2. **Graph Autoencoder & Recommendation Module** (`graph_giovanni.ipynb`)
   - Details the implementation and training of Graph Autoencoder (GAE) models.
   - Includes data preprocessing steps for heterogeneous network data (organizations, projects, topics).
   - Applies GAEs for link prediction to identify potential future research collaborations.
   - Generates ranked recommendations for research partnerships from GAE outputs.

3. **Main Application** (`app.py` & `interactive_graph_visualization.py`)
   - Multi-tab Shiny web interface Real-time network visualization 
   - Heterogeneous graph creation (Organizations ↔ Projects ↔ Topics) powered by PyVis.
   - Integrated recommendation system predicted from `graph_giovanni.ipynb`

### Key Features

- 🔗 **Interactive Heterogeneous Network Analysis**: Organizations, projects, and topics as interconnected entities
- 🤖 **Graph Autoencoder Recommendations**: ML-powered partnership predictions
- 🌍 **Network Metrics**(Online!): European research collaboration patterns

## 📊 Dataset Structure

```
dataset/
├── projects/
│   ├── organization.xlsx    # 100K+ organization records
│   ├── project.xlsx         # 15K+ research projects
│   ├── topics.xlsx          # Research topic classifications
│   ├── euroSciVoc.xlsx      # European Science Vocabulary
│   └── legalBasis.xlsx      # Legal framework data
├── data.json                # Processed recommendations (13MB)
├── deliverables.xlsx        # Project deliverables
├── publications.xlsx        # Research publications
└── summaries.xlsx           # Project summaries
```

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd MDA_project
   ```

2. **Install dependencies:**
   ```bash
   pip install -r dependencies.txt
   ```

3. **Launch the main application:**
   ```bash
   python -m shiny run app.py
   ```

4. **Access the platform:**
   - Open your browser to `http://127.0.0.1:8000`
   - Navigate between tabs: Network Visualization, Recommendations


---

**Group Project for [Modern Data Analytics(2024-2025)](https://onderwijsaanbod.kuleuven.be/syllabi/e/G0Z39CE.htm#activetab=doelstellingen_idp1222816)** at KU Leuven

