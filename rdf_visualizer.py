import networkx as nx
import matplotlib.pyplot as plt
from rdflib import Graph
import streamlit as st
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any
import json

class RDFVisualizer:
    def __init__(self, rdf_graph: Graph):
        """
        Initialize RDF visualizer with an RDF graph.
        
        Args:
            rdf_graph: rdflib.Graph object containing the RDF data
        """
        if not rdf_graph:
            raise ValueError("RDF graph cannot be None")
        self.rdf_graph = rdf_graph
        self.nx_graph = nx.DiGraph()
        self._build_networkx_graph()

    def _build_networkx_graph(self):
        """Convert RDF graph to NetworkX graph for visualization"""
        for s, p, o in self.rdf_graph:
            # Convert RDF terms to strings for node labels
            s_str = str(s)
            o_str = str(o)
            p_str = str(p)
            
            # Add nodes and edges to NetworkX graph
            self.nx_graph.add_node(s_str, type='subject')
            self.nx_graph.add_node(o_str, type='object')
            self.nx_graph.add_edge(s_str, o_str, label=p_str)
        print("NetworkX graph built successfully")

    def visualize_networkx(self, output_file: Optional[str] = None):
        """
        Create a static visualization using NetworkX and Matplotlib.
        
        Args:
            output_file: Optional path to save the visualization
        """
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.nx_graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.nx_graph, pos, 
                             node_color='lightblue',
                             node_size=500,
                             alpha=0.6)
        
        # Draw edges
        nx.draw_networkx_edges(self.nx_graph, pos, 
                             edge_color='gray',
                             arrows=True,
                             arrowsize=20)
        
        # Draw labels
        nx.draw_networkx_labels(self.nx_graph, pos)
        edge_labels = nx.get_edge_attributes(self.nx_graph, 'label')
        nx.draw_networkx_edge_labels(self.nx_graph, pos, edge_labels=edge_labels)
        
        plt.title("XBRL RDF Graph Visualization")
        plt.axis('off')
        
        if output_file:
            plt.savefig(output_file, format='png', dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def visualize_plotly(self, output_file: Optional[str] = None):
        """
        Create an interactive visualization using Plotly.
        
        Args:
            output_file: Optional path to save the visualization as HTML
        """
        # Create edge trace
        edge_x = []
        edge_y = []
        edge_text = []
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        
        # Get layout positions
        pos = nx.spring_layout(self.nx_graph)
        
        # Add edges
        for edge in self.nx_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_text.append(self.nx_graph.edges[edge]['label'])
        
        # Add nodes
        for node in self.nx_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        # Create edge trace
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Connections',
                    xanchor='left',
                    titleside='right'
                )
            ))
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Interactive XBRL RDF Graph Visualization',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        if output_file:
            fig.write_html(output_file)
        else:
            fig.show()

    def create_streamlit_app(self):
        """
        Create a Streamlit web application for interactive visualization.
        """
        st.title("XBRL RDF Graph Visualizer")
        
        # Sidebar controls
        st.sidebar.header("Visualization Controls")
        viz_type = st.sidebar.selectbox(
            "Select Visualization Type",
            ["Network Graph", "Tree View", "Table View"]
        )
        
        if viz_type == "Network Graph":
            # Network graph visualization
            st.subheader("Network Graph Visualization")
            self.visualize_plotly()
            
        elif viz_type == "Tree View":
            # Tree view visualization
            st.subheader("Tree View")
            root_node = st.sidebar.selectbox(
                "Select Root Node",
                list(self.nx_graph.nodes())
            )
            self._visualize_tree(root_node)
            
        else:  # Table View
            # Table view visualization
            st.subheader("Table View")
            self._visualize_table()

    def _visualize_tree(self, root_node: str):
        """
        Create a tree visualization starting from a root node.
        
        Args:
            root_node: The root node to start the tree visualization
        """
        # Create a tree structure from the graph
        tree = nx.dfs_tree(self.nx_graph, root_node)
        
        # Create edge trace
        edge_x = []
        edge_y = []
        edge_text = []
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        
        # Get layout positions
        pos = nx.spring_layout(tree)
        
        # Add edges
        for edge in tree.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_text.append(self.nx_graph.edges[edge]['label'])
        
        # Add nodes
        for node in tree.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        # Create figure
        fig = go.Figure(data=[
            go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            ),
            go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="top center",
                marker=dict(
                    size=10,
                    color='lightblue'
                )
            )
        ])
        
        fig.update_layout(
            title=f'Tree View from {root_node}',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig)

    def _visualize_table(self):
        """Create a table visualization of the RDF data"""
        # Convert RDF data to table format
        data = []
        for s, p, o in self.rdf_graph:
            data.append({
                'Subject': str(s),
                'Predicate': str(p),
                'Object': str(o)
            })
        
        # Display as table
        st.dataframe(data)

    def export_to_json(self, output_file: str):
        """
        Export the RDF graph to a JSON format.
        
        Args:
            output_file: Path to save the JSON file
        """
        graph_data = {
            'nodes': [],
            'edges': []
        }
        
        # Add nodes
        for node in self.nx_graph.nodes():
            graph_data['nodes'].append({
                'id': node,
                'type': self.nx_graph.nodes[node].get('type', 'unknown')
            })
        
        # Add edges
        for edge in self.nx_graph.edges():
            graph_data['edges'].append({
                'source': edge[0],
                'target': edge[1],
                'label': self.nx_graph.edges[edge]['label']
            })
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)

def main():
    """Example usage of the RDF Visualizer"""
    # Example usage
    st.set_page_config(page_title="XBRL RDF Visualizer", layout="wide")
    
    st.title("XBRL RDF Graph Visualizer")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload RDF file", type=['ttl', 'xml', 'n3', 'json-ld'])
    
    if uploaded_file is not None:
        try:
            # Load RDF graph
            g = Graph()
            g.parse(uploaded_file)
            print("RDF graph loaded successfully")
            # Create visualizer
            visualizer = RDFVisualizer(g)
            
            # Create visualization
            visualizer.create_streamlit_app()
        except Exception as e:
            st.error(f"Error parsing RDF file: {str(e)}")
            st.info("This error might be due to invalid decimal values in the RDF file. Please check that all decimal values are properly formatted.")
            print(f"Detailed error: {str(e)}")

if __name__ == "__main__":
    main() 