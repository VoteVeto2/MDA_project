import pandas as pd
import networkx as nx # Still useful for data structure before pyvis
from pyvis.network import Network
import os

def create_interactive_heterogeneous_graph(org_df: pd.DataFrame, proj_df: pd.DataFrame, topic_df: pd.DataFrame, selected_org_ids: list):
    print(f"Generating interactive graph for selected organization IDs: {selected_org_ids}")
    # base_path = "dataset/projects/"
    # org_file = os.path.join(base_path, "organization.xlsx")
    # proj_file = os.path.join(base_path, "project.xlsx")
    # topic_file = os.path.join(base_path, "topics.xlsx")

    try:
        # org_df = pd.read_excel(org_file)
        # proj_df = pd.read_excel(proj_file)
        # topic_df = pd.read_excel(topic_file)
        # print(f"Loaded {len(org_df)} orgs, {len(proj_df)} projects, {len(topic_df)} topics.")

        # Determine top 5 organizations by project participation count
        # org_project_counts = org_df['organisationID'].value_counts()
        # top_5_org_ids = org_project_counts.nlargest(5).index.tolist()
        # print(f"Top 5 organization IDs: {top_5_org_ids}")

        # top_org_df = org_df[org_df['organisationID'].isin(top_5_org_ids)]
        if not selected_org_ids:
            print("No organization IDs selected. Skipping graph generation.")
            # Return an empty network or handle as an error/message in Shiny
            net = Network(height="900px", width="100%", notebook=False, directed=False, cdn_resources="remote")
            net.set_options("""
            {
              "interaction": { "tooltipDelay": 200 },
              "nodes": { "font": { "size": 10 } }
            }
            """) # Basic options for empty graph
            return net # Or return None, or an error message
            
        filtered_org_df = org_df[org_df['organisationID'].isin(selected_org_ids)]
        related_project_ids = filtered_org_df['projectID'].unique().tolist()
        
        # filtered_proj_df = proj_df[proj_df['projectID'].isin(related_project_ids)]
        # filtered_topic_df = topic_df[topic_df['projectID'].isin(related_project_ids)]
        # print(f"Filtered to {len(top_org_df)} top org observations, {len(filtered_proj_df)} projects, {len(filtered_topic_df)} topics.")
        
        # Ensure we only use projects that these selected organizations are part of
        participating_org_df = org_df[org_df['organisationID'].isin(selected_org_ids)]
        project_ids_for_selected_orgs = participating_org_df['projectID'].unique()

        # Further filter projects and topics to only those related to the selected organizations
        current_proj_df = proj_df[proj_df['projectID'].isin(project_ids_for_selected_orgs)]
        current_topic_df = topic_df[topic_df['projectID'].isin(project_ids_for_selected_orgs)]
        # The org_df for node creation should be the one filtered by selected_org_ids
        current_org_df = org_df[org_df['organisationID'].isin(selected_org_ids)]


        print(f"Filtered data for graph: {len(current_org_df)} org participations, {len(current_proj_df)} projects, {len(current_topic_df)} topics.")


        net = Network(height="900px", width="100%", notebook=False, directed=False, cdn_resources="remote") 

        # Add nodes
        # Layer 1: Projects (Group 1)
        # for _, row in filtered_proj_df.iterrows():
        for _, row in current_proj_df.iterrows():
            node_id = f"P_{row['projectID']}"
            label = str(row['acronym'])[:30] if pd.notna(row['acronym']) else f"Proj_{row['projectID']}"
            title_text = f"Project: {row['title']}\nID: {row['projectID']}"
            net.add_node(node_id, label=label, title=title_text, group=1, color="skyblue", shape="ellipse")

        # Layer 2: Organizations (Group 2)
        # for _, row in top_org_df.iterrows():
        # Use current_org_df which contains all entries for the selected organisations,
        # but we only need to add each organization once.
        unique_orgs_to_add = current_org_df.drop_duplicates(subset=['organisationID'])
        for _, row in unique_orgs_to_add.iterrows():
            node_id = f"O_{row['organisationID']}"
            label = str(row['name'])[:40] if pd.notna(row['name']) else f"Org_{row['organisationID']}"
            title_text = f"Organization: {row['name']}\nID: {row['organisationID']}\nCountry: {row['country']}"
            # if node_id not in [n['id'] for n in net.nodes]: # Check should be redundant if unique_orgs_to_add is used
            net.add_node(node_id, label=label, title=title_text, group=2, color="lightgreen", shape="box")

        # Layer 3: Topics (Group 3)
        # for _, row in filtered_topic_df.iterrows():
        # Make topic nodes unique by title
        unique_topics = current_topic_df.drop_duplicates(subset=['title'])
        for _, row in unique_topics.iterrows():
            # clean_title = str(row['title']).replace(" ", "_").replace("/", "_").replace("-", "_")[:30]
            # node_id = f"T_{clean_title}_{row['projectID']}" # Old ID, made topic per project
            clean_title_id = str(row['title']).replace(" ", "_").replace("/", "_").replace("-", "_").replace(":", "_").replace(";", "_").replace(",", "_")
            node_id = f"T_{clean_title_id}" # New ID, unique topic
            label = str(row['title'])[:30] if pd.notna(row['title']) else "Unknown Topic"
            title_text = f"Topic: {row['title']}"
            # if node_id not in [n['id'] for n in net.nodes]: # Check should be redundant
            net.add_node(node_id, label=label, title=title_text, group=3, color="salmon", shape="dot", size=10)

        # Add edges
        # Project to Organization
        # for _, row in top_org_df.iterrows():
        for _, row in current_org_df.iterrows(): # Iterate over all participations for selected orgs
            proj_node_id = f"P_{row['projectID']}"
            org_node_id = f"O_{row['organisationID']}"
            if proj_node_id in [n['id'] for n in net.nodes] and org_node_id in [n['id'] for n in net.nodes]:
                net.add_edge(proj_node_id, org_node_id, title="participates in", color={"inherit": "to"})

        # Project to Topic
        # for _, row in filtered_topic_df.iterrows():
        for _, row in current_topic_df.iterrows(): # Iterate over all topics for relevant projects
            proj_node_id = f"P_{row['projectID']}"
            # clean_title = str(row['title']).replace(" ", "_").replace("/", "_").replace("-", "_")[:30]
            # topic_node_id = f"T_{clean_title}_{row['projectID']}" # Old ID
            clean_title_id = str(row['title']).replace(" ", "_").replace("/", "_").replace("-", "_").replace(":", "_").replace(";", "_").replace(",", "_")
            topic_node_id = f"T_{clean_title_id}" # New ID
            if proj_node_id in [n['id'] for n in net.nodes] and topic_node_id in [n['id'] for n in net.nodes]:
                net.add_edge(proj_node_id, topic_node_id, title="covers topic", color={"inherit": "to"})
        
        print(f"Interactive graph has {len(net.nodes)} nodes and {len(net.edges)} edges.")

        # Corrected JSON options string
        json_options_physics = """
        {
          "nodes": {
            "font": {
              "size": 12
            }
          },
          "edges": {
            "width": 0.5,
            "color": { "color": "#D3D3D3", "highlight": "#000000", "hover": "#000000" },
            "smooth": {
                "type": "continuous"
            }
          },
          "interaction": {
            "hover": true,
            "hoverConnectedEdges": true,
            "navigationButtons": true,
            "keyboard": true,
            "tooltipDelay": 200
          },
          "physics": {
            "enabled": true,
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
          }
        }
        """
        net.set_options(json_options_physics)

        # output_html_path = "graph/interactive_heterogeneous_graph.html"
        # net.show(output_html_path, notebook=False)
        
        # print(f"Interactive graph visualization saved to {output_html_path}")
        # if os.path.exists(output_html_path):
        #     print(f"File check after save: {output_html_path} exists.")
        # else:
        #     print(f"File check after save: {output_html_path} DOES NOT EXIST.")
        # return output_html_path
        return net

    except FileNotFoundError as e: # This should not happen if dataframes are passed correctly
        print(f"Error: {e}. This suggests an issue with how dataframes were passed or internal logic.")
        return None
    except Exception as e:
        print(f"Error building or visualizing interactive graph: {e}")
        import traceback
        traceback.print_exc()
        # Return an empty network or a specific error object if preferred
        net = Network(height="100px", width="100%", notebook=False, directed=False, cdn_resources="remote")
        net.add_node("ErrorNode", label=f"Error: {str(e)[:50]}", title=str(e), color="red")
        return net


# if __name__ == "__main__":
#     html_path = create_interactive_heterogeneous_graph_top_orgs()
#     if html_path:
#         print(f"Successfully generated interactive graph: {html_path}")
#     else:
#         print("Failed to generate interactive graph.")


