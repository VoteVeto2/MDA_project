import pandas as pd
import networkx as nx 
from pyvis.network import Network
import os

def create_interactive_heterogeneous_graph(org_df: pd.DataFrame, proj_df: pd.DataFrame, topic_df: pd.DataFrame, selected_org_ids: list):
    print(f"Generating interactive graph for selected organization IDs: {selected_org_ids}")

    try:
        if not selected_org_ids:
            print("No organization IDs selected. Skipping graph generation.")
            net = Network(height="900px", width="100%", notebook=False, directed=False, cdn_resources="remote")
            net.set_options("""
            {
              "interaction": { "tooltipDelay": 200 },
              "nodes": { "font": { "size": 10 } }
            }
            """)
            return net
            
        filtered_org_df = org_df[org_df['organisationID'].isin(selected_org_ids)]
        related_project_ids = filtered_org_df['projectID'].unique().tolist()
        
        participating_org_df = org_df[org_df['organisationID'].isin(selected_org_ids)]
        project_ids_for_selected_orgs = participating_org_df['projectID'].unique()

        current_proj_df = proj_df[proj_df['projectID'].isin(project_ids_for_selected_orgs)]
        current_topic_df = topic_df[topic_df['projectID'].isin(project_ids_for_selected_orgs)]
        current_org_df = org_df[org_df['organisationID'].isin(selected_org_ids)]

        print(f"Filtered data for graph: {len(current_org_df)} org participations, {len(current_proj_df)} projects, {len(current_topic_df)} topics.")

        net = Network(height="900px", width="100%", notebook=False, directed=False, cdn_resources="remote") 

        # Add nodes
        # Layer 1: Projects (Group 1)
        for _, row in current_proj_df.iterrows():
            node_id = f"P_{row['projectID']}"
            label = str(row['acronym'])[:30] if pd.notna(row['acronym']) else f"Proj_{row['projectID']}"
            title_text = f"Project: {row['title']}\nID: {row['projectID']}"
            net.add_node(node_id, label=label, title=title_text, group=1, color="skyblue", shape="ellipse")

        # Layer 2: Organizations (Group 2)
        unique_orgs_to_add = current_org_df.drop_duplicates(subset=['organisationID'])
        for _, row in unique_orgs_to_add.iterrows():
            node_id = f"O_{row['organisationID']}"
            label = str(row['name'])[:40] if pd.notna(row['name']) else f"Org_{row['organisationID']}"
            title_text = f"Organization: {row['name']}\nID: {row['organisationID']}\nCountry: {row['country']}"
            net.add_node(node_id, label=label, title=title_text, group=2, color="lightgreen", shape="box")

        # Layer 3: Topics (Group 3)
        unique_topics = current_topic_df.drop_duplicates(subset=['title'])
        for _, row in unique_topics.iterrows():
            topic_title_str = str(row['title']) if pd.notna(row['title']) else "Unknown_Topic"
            clean_title_id = topic_title_str.replace(" ", "_").replace("/", "_").replace("-", "_").replace(":", "_").replace(";", "_").replace(",", "_")
            node_id = f"T_{clean_title_id}"
            label = str(row['title'])[:30] if pd.notna(row['title']) else "Unknown Topic"
            title_text = f"Topic: {row['title']}"
            net.add_node(node_id, label=label, title=title_text, group=3, color="salmon", shape="dot", size=10)

        # Add edges
        # Project to Organization
        for _, row in current_org_df.iterrows():
            proj_node_id = f"P_{row['projectID']}"
            org_node_id = f"O_{row['organisationID']}"
            if proj_node_id in [n['id'] for n in net.nodes] and org_node_id in [n['id'] for n in net.nodes]:
                net.add_edge(proj_node_id, org_node_id, title="participates in", color={"color": "#D3D3D3", "opacity": 0.3})

        # Project to Topic
        for _, row in current_topic_df.iterrows():
            proj_node_id = f"P_{row['projectID']}"
            topic_title_str = str(row['title']) if pd.notna(row['title']) else "Unknown_Topic"
            clean_title_id = topic_title_str.replace(" ", "_").replace("/", "_").replace("-", "_").replace(":", "_").replace(";", "_").replace(",", "_")
            topic_node_id = f"T_{clean_title_id}"
            if proj_node_id in [n['id'] for n in net.nodes] and topic_node_id in [n['id'] for n in net.nodes]:
                net.add_edge(proj_node_id, topic_node_id, title="covers topic", color={"color": "#D3D3D3", "opacity": 0.3})
        
        print(f"Interactive graph has {len(net.nodes)} nodes and {len(net.edges)} edges.")

        # Network options with IMMEDIATE physics disable after initial layout
        json_options = """
        {
          "nodes": {
            "font": {
              "size": 12
            }
          },
          "edges": {
            "width": 0.5,
            "color": { "color": "#D3D3D3", "opacity": 0.3 },
            "smooth": {
                "type": "continuous"
            }
          },
          "interaction": {
            "hover": true,
            "hoverConnectedEdges": true,
            "navigationButtons": true,
            "keyboard": true,
            "tooltipDelay": 200,
            "dragNodes": true,
            "dragView": true
          },
          "physics": {
            "enabled": true,
            "stabilization": { 
              "enabled": true,
              "iterations": 500,
              "updateInterval": 50,
              "onlyDynamicEdges": false,
              "fit": true
            },
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08,
              "damping": 0.4
            },
            "solver": "forceAtlas2Based",
            "minVelocity": 0.75,
            "maxVelocity": 5
          }
        }
        """
        net.set_options(json_options)
        
        # Enhanced JavaScript for static network and transparency effects
        enhanced_js = """
        // Store original colors and opacity for all nodes
        var allNodesOriginalData = {};
        var physicsDisabled = false;
        var initialStabilizationComplete = false;
        
        // Function to store original node data
        function storeOriginalNodeData() {
          var nodes = network.body.data.nodes;
          var nodeIds = nodes.getIds();
          nodeIds.forEach(function(nodeId) {
            var nodeData = nodes.get(nodeId);
            allNodesOriginalData[nodeId] = {
              color: nodeData.color,
              opacity: nodeData.opacity || 1.0,
              size: nodeData.size
            };
          });
        }
        
        // Immediate physics disable on network ready
        network.once("afterDrawing", function() {
          console.log("Network drawn - disabling physics immediately");
          network.setOptions({physics:{enabled:false}});
          physicsDisabled = true;
          storeOriginalNodeData();
        });
        
        // Backup: disable physics after stabilization
        network.on("stabilizationIterationsDone", function() {
          if (!physicsDisabled) {
            console.log("Stabilization complete - disabling physics");
            network.setOptions({physics:{enabled:false}});
            physicsDisabled = true;
            storeOriginalNodeData();
          }
          initialStabilizationComplete = true;
        });
        
        // Force disable physics after very short timeout
        setTimeout(function() {
          if (!physicsDisabled) {
            console.log("Force disabling physics");
            network.setOptions({physics:{enabled:false}});
            physicsDisabled = true;
            if (Object.keys(allNodesOriginalData).length === 0) {
              storeOriginalNodeData();
            }
          }
        }, 100);
        
        // Function to highlight connected nodes with extreme transparency for others
        function highlightConnectedNodes(nodeId) {
          if (!nodeId) return;
          
          var allNodes = network.body.data.nodes;
          var allEdges = network.body.data.edges;
          var allNodeIds = allNodes.getIds();
          var connectedNodes = network.getConnectedNodes(nodeId);
          var connectedEdges = network.getConnectedEdges(nodeId);
          var highlightNodes = [nodeId].concat(connectedNodes);
          
          // Update nodes: highlight connected, make others almost invisible
          var nodeUpdates = [];
          allNodeIds.forEach(function(nId) {
            if (highlightNodes.includes(nId)) {
              // Restore original appearance for connected nodes
              var originalData = allNodesOriginalData[nId];
              if (originalData) {
                nodeUpdates.push({
                  id: nId,
                  color: originalData.color,
                  opacity: 1.0,
                  borderWidth: 2,
                  borderWidthSelected: 3
                });
              }
            } else {
              // Make unconnected nodes almost completely transparent
              nodeUpdates.push({
                id: nId,
                opacity: 0.05,  // Almost invisible
                borderWidth: 0
              });
            }
          });
          allNodes.update(nodeUpdates);
          
          // Update edges: highlight connected, make others almost invisible
          var edgeUpdates = [];
          allEdges.getIds().forEach(function(eId) {
            if (connectedEdges.includes(eId)) {
              edgeUpdates.push({
                id: eId,
                color: { color: '#2B7CE9', opacity: 0.8 },
                width: 2
              });
            } else {
              edgeUpdates.push({
                id: eId,
                color: { color: '#D3D3D3', opacity: 0.02 },  // Almost invisible
                width: 0.5
              });
            }
          });
          allEdges.update(edgeUpdates);
        }
        
        // Function to reset all nodes to original state
        function resetAllNodes() {
          var allNodes = network.body.data.nodes;
          var allEdges = network.body.data.edges;
          
          // Reset nodes to original appearance
          var nodeUpdates = [];
          Object.keys(allNodesOriginalData).forEach(function(nodeId) {
            var originalData = allNodesOriginalData[nodeId];
            nodeUpdates.push({
              id: nodeId,
              color: originalData.color,
              opacity: originalData.opacity,
              borderWidth: 1,
              borderWidthSelected: 2
            });
          });
          allNodes.update(nodeUpdates);
          
          // Reset edges to default state
          var edgeUpdates = [];
          allEdges.getIds().forEach(function(eId) {
            edgeUpdates.push({
              id: eId,
              color: { color: '#D3D3D3', opacity: 0.3 },
              width: 0.5
            });
          });
          allEdges.update(edgeUpdates);
        }
        
        // Event handlers for hover effects
        network.on("hoverNode", function(params) {
          var nodeId = params.node;
          var nodeData = network.body.data.nodes.get(nodeId);
          
          // Only apply transparency effect for Project (group 1) and Topic (group 3) nodes
          if (nodeData && (nodeData.group === 1 || nodeData.group === 3)) {
            highlightConnectedNodes(nodeId);
          }
        });
        
        network.on("blurNode", function(params) {
          resetAllNodes();
        });
        
        // Click handling
        network.on("click", function(params) {
          if (params.nodes.length === 0) {
            // Clicked on background
            resetAllNodes();
            return;
          }
          
          var nodeId = params.nodes[0];
          var nodeData = network.body.data.nodes.get(nodeId);
          
          // Reset on organization node click
          if (nodeData && nodeData.group === 2) {
            resetAllNodes();
          }
        });
        
        // Prevent any physics re-enabling
        network.on("dragStart", function() {
          if (!physicsDisabled) {
            network.setOptions({physics:{enabled:false}});
            physicsDisabled = true;
          }
        });
        
        // Ensure physics stays disabled after any interaction
        network.on("dragEnd", function() {
          if (!physicsDisabled) {
            network.setOptions({physics:{enabled:false}});
            physicsDisabled = true;
          }
        });
        
        // Prevent physics from being re-enabled during zoom
        network.on("zoom", function() {
          if (!physicsDisabled) {
            network.setOptions({physics:{enabled:false}});
            physicsDisabled = true;
          }
        });
        """
        
        # Add the enhanced JavaScript to the HTML
        net.html += f"<script>{enhanced_js}</script>"
        
        return net

    except FileNotFoundError as e:
        print(f"Error: {e}. This suggests an issue with how dataframes were passed or internal logic.")
        return None
    except Exception as e:
        print(f"Error building or visualizing interactive graph: {e}")
        import traceback
        traceback.print_exc()
        net = Network(height="100px", width="100%", notebook=False, directed=False, cdn_resources="remote")
        net.add_node("ErrorNode", label=f"Error: {str(e)[:50]}", title=str(e), color="red")
        return net