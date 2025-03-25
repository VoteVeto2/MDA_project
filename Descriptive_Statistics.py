# ============ Descriptive Statistics for the data =================
import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations
from datetime import datetime
import seaborn as sns
from matplotlib import pyplot as plt
from IPython.display import display

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
        # print('\n Distribution of organizations per project:\n')
        # for count, projects in orgs_per_proj_counts.items():
        #    print(f'{count} organizations: {projects} projects')

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

        # ================= 2. Calculate Institution Degrees =================
        org_partners = defaultdict(set)  # defaultdict is a dictionary that initializes missing keys with a default value

        # Create a dictionary of organizations and their partners
        for collab in collaborations:
            org1_name = collab['org1_name']  
            org2_name = collab['org2_name']
            org_partners[org1_name].add(org2_name)
            org_partners[org2_name].add(org1_name)
            
        print(f'Number of collaboration: {len(collaborations)}\n')

        # Convert sets to counts 
        org_degrees = {org: len(partners) for org, partners in org_partners.items()}

        # Find organizations with the highest degree of collaborations
        print('Top10 organizations with the highest number of collaborations:\n')
        top10_orgs = sorted(org_degrees.items(), key = lambda x: x[1], reverse = True)[:10]

        def get_organization_by_name(org_name, org_df):
            matching_orgs = org_df[org_df['name'] == org_name]
            if matching_orgs.empty:
                return None 
            return matching_orgs.iloc[0] # .iloc[0] returns the first row

        for i, (org_name, degree) in enumerate(top10_orgs, 1): # enumerate(, 1) starts the index at 1
            org = get_organization_by_name(org_name, org_df)
            if org is not None:
                print(f'{i}. {org_name} ({org["country"]}): {degree} partners')
            else:
                print(f'{i}. {org_name} (Unknown): {degree} partners')

        # ================= 3. Calculate Country Contributions =================
        country_collaborations = defaultdict(int)
        # print(collaborations[:2])

        for collab in collaborations:
            # Skip collaborations with missing country information 
            if pd.isna(collab['org1_country']) or pd.isna(collab['org2_country']):
                continue
            country_pair = '-'.join(sorted([collab['org1_country'], collab['org2_country']]))
            country_collaborations[country_pair] += 1

        print('Top 10 country collaborations:\n')
        top_countries = sorted(country_collaborations.items(), key = lambda x: x[1], reverse = True)[:10]
        for i, (country_pair, count) in enumerate(top_countries, 1):
            print(f"{i}. {country_pair}: {count} collaborations")

        # ================= 4. Calculate Network Metrics =================
        unique_organizations = set() # set() is a collection of unique elements
        for collab in collaborations:
            unique_organizations.add(collab['org1_name'])
            unique_organizations.add(collab['org2_name'])
        # list(unique_organizations)[:2]

        # Count nodes
        num_nodes = len(unique_organizations)
        max_possible_edges = (num_nodes * (num_nodes - 1)) / 2 

        # Count unique organization pairs 
        unique_pairs = set()
        for collab in collaborations:
            pair = '-'.join(sorted([collab['org1_name'], collab['org2_name']]))
            unique_pairs.add(pair)

        actual_edges = len(unique_pairs)
        network_density = actual_edges / max_possible_edges 
        print("Network metrics:\n")
        print(f"Nodes (organizations): {num_nodes}")
        print(f"Edges (unique collaborations): {actual_edges}")
        print(f"Maximum possible edges: {max_possible_edges}")
        print(f"Network density: {network_density:.6f}")
        print(f"Average degree (collaborations): {(2 * actual_edges / num_nodes):.2f}")

        # ================= 5. Organization/Coordinator Types =================
        # - `HES`: Higher Education Institutions
        # - `PRC`: PRivate Companies 
        # - `REC`: REsearch Companies
        # - `OTH`: OTHers 
        # - `PUB`: PUblic Body

        # Analyze distribution of organization types
        org_type_dist = org_df['activityType'].value_counts(dropna = False)
        print(org_type_dist[:2])
        print('Organization types distribution:\n')
        for activity_type, count in org_type_dist.items(): # .items() returns key-value pairs
            print(f'{activity_type}: {count} organizations {(count / len(org_df) * 100): .2f}%')
            # 24 missing values for `activityType`

        # Analyze coordinator types
        coordinator_type_dict = org_df[org_df['role'] == 'coordinator']['activityType'].value_counts(dropna = False)
        print('\nProject coordinator types distribution:\n')
        for activity_type, count in coordinator_type_dict.items():
            print(f"{activity_type}: {count} coordinators")

        # ================= 6. Country Participations =================
        country_participation = defaultdict(lambda: {'count': 0, 'coordinatorCount': 0, 'netEcContribution': 0})

        for _, org in org_df.iterrows(): # iterrows() returns an iterator that yields index and row data
            # `_` means we recieve the index but DO NOT use it
            country = org.get('country', 'Unknown')
            country_participation[country]['count'] += 1

            if org.get('role') == 'coordinator': 
                country_participation[country]['coordinatorCount'] += 1 
            
            # convert NaN in netEcContribution to 0 
            if pd.isna(org.get('netEcContribution')):
                org['netEcContribution'] = 0
            country_participation[country]['netEcContribution'] += org.get('netEcContribution')
            # round it to integer
            country_participation[country]['netEcContribution'] = int(country_participation[country]['netEcContribution'])
        top_countries = sorted(country_participation.items(), key = lambda x: x[1]['count'], reverse = True)[:10]

        print('Top 10 countries by participation:\n')
        display(top_countries)


        # ================= 7. Topics Analysis =================
        topic_distribution = topic_df['title'].value_counts(dropna=False)
                
        print("\nTop 10 research topics:")
        for i, (topic, count) in enumerate(topic_distribution.head(10).items(), 1):
            print(f"{i}. {topic}: {count} projects")

        return {
            'org_df': org_df,
            'proj_df': proj_df,
            'topic_df': topic_df, 
            'collaborations': collaborations,
            'org_degrees': org_degrees,
            'country_collaborations': dict(country_collaborations),
            'network_metrics': {
                'nodes': num_nodes,
                'edges': actual_edges,
                'density': network_density,
                'avg_degree': (2 * actual_edges / num_nodes)
            }
        }
    
    except Exception as e:
        print(f'Error building network analysis: {e}')
        return None

if __name__ == '__main__':
    results = build_network_analysis()