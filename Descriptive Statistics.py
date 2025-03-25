# ============ Descriptive Statistics for the data =================
import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations
from datetime import datetime

def build_network_analysis():
    print('Loading data...')

    try: 
        # ============= 0. Preprocessing Data =============
        # Read the excel files
        org_df = pd.read_excel('dataset/projects/organization.xlsx') 
        print(f'Loaded {len(org_df)} organization observations.')

        proj_df = pd.read_excel('dataset/projects/project.xlsx')
        print(f'Loaded {len(proj_df)} projects.')

        topic_df = pd.read_excel('dataset/projects/topics.xlsx')    
        print(f'Loaded {len(topic_df)} topics.')

        # Group organizations by `projectID`
        project_org = org_df.groupby('projectID').apply(lambda x: x.to_dict('records')).to_dict()
        # lambda x: x.to_dict('records') converts each df to a list of dictionaries. keys = col, values = row  
        print(f'{len(project_org)} unique projects with organizations.')

        # Identify collaborations between organizations 
        collaborative_proj = [project_id for project_id, orgs in project_org.items() if len(orgs) > 1] 
        print(f'{len(collaborative_proj)} projects with multiple organizations.')

        # Calculate the distribution of organizations per project
        orgs_per_proj_counts = org_df['projectID'].value_counts().value_counts().sort_index()
        print('\n Distribution of organizations per project:\n')
        for count, projects in orgs_per_proj_counts.items():
            print(f'{count} organizations: {projects} projects')

        # ================= 1. Build Network pairs =================
        collaborations = []
        total_collaborations_pairs = 0 

        for project_id in collaborative_proj:
            orgs = project_org[project_id]

            # Generate all possible pairs of organizations
            for org1, org2 in combinations(orgs, 2):
            # combinations() returns all possible pairs between orgs
                collaborations.append({
                    'projectID': project_id,
                    'org1': org1.get('organizationID'),
                    'org1_name': org1.get('name'),
                    'org1_country': org1.get('country'),
                    'org2': org2.get('organizationID'),
                    'org2_name': org2.get('name'),
                    'org2_country': org2.get('country')
                })
                total_collaborations_pairs += 1 

        print(f'Generated {total_collaborations_pairs} collaboration pairs.')

        # ================= 2. Calculate Degrees =================
        

        return {
            'org_df': org_df,
            'proj_df': proj_df,
            'topic_df': topic_df, 
            'collaborations': collaborations, 

        }
    
    except Exception as e:
        print(f'Error building network analysis: {e}')
        return None

if __name__ == '__main__':
    results = build_network_analysis()