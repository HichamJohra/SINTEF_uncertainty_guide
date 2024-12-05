# -*- coding: utf-8 -*- #######################################################
#                                                                             #
#   Hicham Johra                                                              #
#   SINTEF Community, Norway                                                  #
#   hicham.johra@sintef.no                                                    #
#                                                                             #
#   2024-12-01                                                                #
#                                                                             #
###############################################################################

"#############################################################################"
"#############################################################################"
"####                                                                     ####"
"####                   SINTEF Uncertainty Guide Web App                  ####"
"####                                                                     ####"
"#############################################################################"
"#############################################################################"

"""to do list:
- Add new memory var dcc.Store for explorer flowchart
- modularize classes and common functions at the top of the file
- modularize sub-routines of the callbacks: 1 module per callback
- add popup message if clicking on top and leaf node and there is not "data" for help: display "No documentation is available"
- Find better layout for the management of edge sizes

"""

"#############################################################################"
"###                                                                       ###"
"###                             Documentation                             ###"
"###                                                                       ###"
"#############################################################################"

"""
Type:
    Dash App

Tested with:
    Interpreter: Venv Python 3.12
    Environment: Virtualenv
    IDE: PyCharm
    Web-deployment: SINTEF Gitlab docker

Description:
    This Dash app generates a web-app with all different functionalities, items and widgets from Dash.

Inputs (arguments):
    None

Outputs:
    Web App with multiple pages

Requirements
    Install in venv when creating the project with requirements:
    pip install -r requirements.txt
"""



"#############################################################################"
"##                                                                         ##"
"##                              Begin Process                              ##"
"##                                                                         ##"
"#############################################################################"

print("Begin Process: SINTEF Uncertainty Guide Web App.")



"#############################################################################"
"##                                                                         ##"
"##                       Import External Libraries                         ##"
"##                                                                         ##"
"#############################################################################"

try:
    from typing import List, Dict, Union
    import dash
    from dash import dcc, html, Dash, dash_table, ctx, State
    from dash.dependencies import Input, Output, ALL, State, MATCH, ALLSMALLER
    import dash_bootstrap_components as dbc
    import plotly.express as px  # plotly==5.13.0
    import plotly.graph_objects as go
    import pandas as pd  # pandas==1.3.5
    import base64
    import datetime
    import io
    from rdflib import Graph, URIRef, Literal, Namespace
    import networkx as nx
    from pyvis.network import Network
    import webbrowser
    import os
    import random
    import dash_leaflet as dl
    from dash_leaflet import CircleMarker, Popup
    from pyflowchart import Flowchart
    from graphviz import Digraph
    import json
    import dash_cytoscape as cyto
    import yaml  # pip install PyYAML
    import copy  # Handle deep copy of elements like lists to avoid mutable behavior
    import math

except Exception as e:
    raise ImportError("Error: external libraries could not be imported correctly.") from e

else:
    print("External libraries imported successfully.")



"#############################################################################"
"##                                                                         ##"
"##                       Import Internal Libraries                         ##"
"##                                                                         ##"
"#############################################################################"

try:
    pass  # No local libraries and packages at the moment. Include libraries from modularization of the code

except Exception as e_:
    raise ImportError("Error: internal libraries could not be imported correctly.") from e_

else:
    print("Internal libraries imported successfully.")



"#############################################################################"
"##                                                                         ##"
"##                      Definition of Local Classes                        ##"
"##                                                                         ##"
"#############################################################################"

###############################################################################
###                             AppMemory Class                             ###
###############################################################################

class AppMemory:

    def __init__(
        self,
        memory=None,
    ):
        """
        Initialize the AppMemory class.

        Main parameter
            memory (dict)

        Sub-parameters:
            full_graph_data (dict): Full graph data including all nodes and edges.
            current_graph_data (dict): Current graph data representing a subset or modified version of the full graph.
        """

        full_graph_data = {"nodes": [], "edges": []}
        current_graph_data = {"nodes": [], "edges": []}
        full_graph_roots = []
        current_graph_roots = []
        flowchart_key = 0

        self.memory = memory or {
            "full_graph_data": full_graph_data,
            "current_graph_data": current_graph_data,
            "full_graph_roots": full_graph_roots,
            "current_graph_roots": current_graph_roots,
            "flowchart_key": flowchart_key,
        }


    def load_full_graph_data(
        self,
        file_path,
    ):
        """
        Load the full graph data from a JSON file.

        Inputs:
            file_path (str): Path to the JSON file containing the full graph data.
        """

        try:
            with open(file_path, 'r') as file_:
                full_graph_data = json.load(file_)
                # Set current graph data to full graph data by default
                current_graph_data = full_graph_data

                # Get roots of the graphs
                nodes = full_graph_data["nodes"]
                edges = full_graph_data["edges"]
                # Get all node IDs
                node_ids = {node["id"] for node in nodes}
                # Get all target node IDs from the edges
                target_ids = {edge["target"] for edge in edges}
                # Roots are nodes that are not in the targets
                root_ids = list(node_ids - target_ids)

                self.memory["full_graph_roots"] = root_ids
                self.memory["current_graph_roots"] = root_ids
                self.memory["full_graph_data"] = full_graph_data
                self.memory["current_graph_data"] = current_graph_data

        except Exception as e:
            full_graph_data = {"nodes": [], "edges": []}
            current_graph_data = {"nodes": [], "edges": []}
            self.memory["full_graph_data"] = full_graph_data
            self.memory["current_graph_data"] = current_graph_data
            raise ImportError("Error: Loading full graph data has failed.") from e



"#############################################################################"
"##                                                                         ##"
"##                      Definition of Local Functions                      ##"
"##                                                                         ##"
"#############################################################################"

"#############################################################################"
"###                         Manage Cytoscape Graph                        ###"
"#############################################################################"

###############################################################################
###                        Generate Cytoscape Graph                         ###
###############################################################################

def convert_to_cytoscape_elements(
    nodes: list[dict],
    edges: list[dict],
)-> list[dict]:  # cytoscape_elements
    """
    Convert nodes and edges into Cytoscape-compatible elements.

    Inputs:
        nodes (list(dict)): A list of dictionaries representing the nodes.
        edges (list(dict)): A list of dictionaries representing the edges.

    Outputs:
        cytoscape_elements (list(dict)): A list of dictionaries formatted for Cytoscape elements.
    """

    "deepcopy"
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)

    cytoscape_elements = [
        {
            "data": {
                "id": node["id"],
                "label": node["label"],
                "data": node.get("data", None)  # Use .get to handle missing "data" keys
            },
            "style": node.get("style", {})  # Default to an empty style if not specified
        }
        for node in nodes
    ] + [
        {
            "data": {
                "source": edge["source"],
                "target": edge["target"],
                "label": edge["label"]
            },
            "style": edge.get("style", {})  # Default to an empty style if not specified
        }
        for edge in edges
    ]

    return cytoscape_elements



"#############################################################################"
"###                         Manage Nodes and Edges                        ###"
"#############################################################################"

###############################################################################
###                  Find parent nodes of a specific node                   ###
###############################################################################

def find_parents(
    node_id: str,
    nodes: list[dict],
    edges: list[dict],
)-> tuple[
    list[str],  # parents_id
    list[dict],  # parents_nodes
]:
    """
    Find parent nodes of a specific node from a list of edges.

    Inputs:
        node_id (str): A node id from which to identify targets to it.
        edges (list(dict)): A list of dictionaries representing the edges.
        nodes (list(dict)): A list of dictionaries representing the nodes.

    Outputs:
        parents_id (list(str)): A list of parent nodes id (or empty list if the selected node has no parent).
        parents_nodes (list(dict)): A list of parent nodes (or empty list if the selected node has no parent).
    """

    parents_id = [edge["source"] for edge in edges if edge["target"] == node_id]
    parents_nodes = [node for node in nodes if node["id"] in parents_id]

    return parents_id, parents_nodes



###############################################################################
###                 Find children nodes of a specific node                  ###
###############################################################################

def find_children(
    node_id: str,
    nodes: list[dict],
    edges: list[dict],
)-> tuple[
    list[str],  # child_nodes_id
    list[dict],  # child_nodes
    list[dict],  # child_edges
]:
    """
    Find children nodes of a specific node from a list of edges.

    Inputs:
        node_id (str): A node id from which to identify children from it.
        nodes (list(dict)): A list of dictionaries representing the nodes.
        edges (list(dict)): A list of dictionaries representing the edges.

    Outputs:
        child_nodes_id (list(str)): A list of children nodes id (or empty list if the selected node has no children).
        child_nodes (list(dict)): A list of children nodes (or empty list if the selected node has no children).
        child_edges (list(dict)): A list of edges connecting the target node_id to the child_nodes.
    """

    child_nodes_id = [edge["target"] for edge in edges if edge["source"] == node_id]
    child_nodes = [node for node in nodes if node["id"] in child_nodes_id]
    child_edges = [edge for edge in edges if edge["source"] == node_id]

    return child_nodes_id, child_nodes, child_edges



###############################################################################
###                    Get Subtree from a specific node                     ###
###############################################################################

def get_subtree(
    node_id: str,
        nodes: list[dict],
        edges: list[dict],
)-> tuple[
    list[dict],  # subtree_nodes
    list[dict],  # subtree_edges
]:
    """
    Generate subtree starting from the selected node from a list of edges and nodes.
    Ensures nodes and edges are added recursively.
    Avoids revisiting nodes using a visited set.

    Inputs:
        node_id (str): A node id from which to identify the subtree.
        nodes (list(dict)): A list of dictionaries representing the nodes of the whole tree/graph.
        edges (list(dict)): A list of dictionaries representing the edges of the whole tree/graph.

    Outputs:
        subtree_nodes (list(dict)): A list of children nodes corresponding to the subtree.
        subtree_edges (list(dict)): A list of children edges corresponding to the subtree.
    """

    # Initialize the subtree structures
    subtree_nodes = []
    subtree_edges = []

    # Maintain a set of visited nodes to avoid revisiting
    visited = set()

    # Helper function for recursive traversal
    def traverse(
        current_node_id: str
    ):
        # Check if the node has already been visited
        if current_node_id in visited:
            return None

        visited.add(current_node_id)

        # Add the current node to the subtree
        node = next((n for n in nodes if n["id"] == current_node_id), None)
        if node:
            subtree_nodes.append(node)

        # Find and add outgoing edges from the current node
        outgoing_edges = [edge for edge in edges if edge["source"] == current_node_id]
        for edge in outgoing_edges:
            subtree_edges.append(edge)
            traverse(edge["target"])  # Recursively visit the target node

    # Start traversal from the specified node
    traverse(node_id)

    return subtree_nodes, subtree_edges



###############################################################################
###                    Get Single Node from Nodes and ID                    ###
###############################################################################

def find_single_node_from_id(
    nodes: list[dict],
    target_node_id: str,
)-> dict:  # node
    """
    Get a single node from a list of nodes and an ID of the target node.

    Inputs:
    - nodes (list(dict)): A list of node dictionaries, each with an "id".
    - target_node_id (str): The id of the target node to extract from the list of nodes.

    Outputs:
    - node (dict): A single node.
    """

    for node in nodes:
        if node['id'] == target_node_id:
            return node

    # If no node is found with the given id, return None
    return {}



###############################################################################
###                          Find Roots of a Graph                          ###
###############################################################################

def find_roots_id(
    nodes: list[dict],
    edges: list[dict],
)-> list:  # list_roots_id
    """
    Identifies the id of root nodes of a directed graph.

    Inputs:
    - nodes (list(dict)): A list of node dictionaries, each with an "id".
    - edges (list(dict)): A list of edge dictionaries, each with "source" and "target".

    Outputs:
    - list_roots_id (list(str)): A list of root node IDs.
    """

    # Get all node IDs
    node_ids = {node["id"] for node in nodes}  # Use comprehensive set {}

    # Get all target node IDs from the edges
    target_ids = {edge["target"] for edge in edges}  # Use comprehensive set {}

    # Roots are nodes that are not in the targets
    root_ids = node_ids - target_ids

    return list(root_ids)



###############################################################################
###                   Highlight background specific node                    ###
###############################################################################

def change_background_target_node(
    nodes: list[dict],
    target_node_id: str,
    color_hex_code: str,
    echo_in: bool,
)-> list[dict]:  # nodes
    """
    Updates the background color of the target node to red.

    Inputs:
        nodes (list(dict)): List of node elements, where each element is a dictionary with "data" and optionally "style".
        target_node_id (str): The ID of the target node to highlight.
        color_hex_code (str): The hexadecimal code for the background of the target node.
        echo_in (bool): Enables or hidde the echo mode of the function.

    Outputs:
        nodes (list(dict)): Modified list of nodes with the target node's background updated to selected color hexadecimal code.
    """

    "deepcopy"
    nodes = copy.deepcopy(nodes)

    for node in nodes:
        # Check if the current node matches the target ID
        if node["id"] == target_node_id:
            if "style" not in node:
                node["style"] = {}

            # Update the background color in the style attribute
            node["style"]["background-color"] = color_hex_code  # Hexadecimal color code for background
            if echo_in: print(f"The node {node["id"]} had its background color changed to {color_hex_code}.")
            return nodes

    return nodes



###############################################################################
###              Increase Font Label Specific Nodes and Edges               ###
###############################################################################

def increase_font_nodes_edges(
    nodes: list[dict],
    edges: list[dict],
    target_nodes: list[dict],
    target_edges: list[dict],
    magnifying_ratio: int,
    echo_in: bool,
)-> tuple[
    list[dict],  # nodes
    list[dict],  # edges
]:
    """
    Updates the label font size the target nodes and edges.

    Inputs:
        nodes (list(dict)): List of node elements, where each element is a dictionary with "data" and optionally "style".
        edges (list(dict)): List of edge elements, where each element is a dictionary with "data" and optionally "style".
        target_nodes (list(dict)): The list of nodes that the label font size are increased.
        target_edges (list(dict)): The list of edges that the label font size are increased.
        magnifying_ratio (int): The ratio by which the label font size of the target elements is increased: new_size/old_size.
        echo_in (bool): Enables or hidde the echo mode of the function.

    Outputs:
        nodes (list(dict)): Modified list of nodes with the target node's label font size that is updated.
        edges (list(dict)): Modified list of edges with the target edge's label font size that is updated.
    """

    "deepcopy"
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    target_nodes = copy.deepcopy(target_nodes)
    target_edges = copy.deepcopy(target_edges)

    # # Linear magnification with number of nodes
    # k = 1
    # a = magnifying_ratio
    # m = a * (1 + (k * len(nodes)))

    # Log magnification with number of nodes
    k = 1
    a = magnifying_ratio
    m = a * (1 + (k * math.log(len(nodes)+1)))

    # Loop through the nodes and check if the id is in target_nodes
    for node in nodes:
        # Check if the node's "id" is in target_nodes
        if any(node["id"] == target_node["id"] for target_node in target_nodes):
            if "style" not in node:
                node["style"] = {}

            # Update the label font size in the style attribute
            px_str = node["style"]["font-size"]  # Get px str for str label font size
            px_value = int(px_str.replace("px", ""))  # Remove 'px' and convert to integer
            new_px_str = f"{int(round(px_value * m))}px"
            node["style"]["font-size"] = new_px_str
            if echo_in: print(f"The node {node["id"]} had its label font size increased by a ratio of {m} to reach from {px_str} to {new_px_str}")

    # Loop through the edges and check if the id is in target_edges
    for edge in edges:
        # Check if the edge's "id" is in target_edges
        if any(edge["source"] == target_edge["source"] for target_edge in target_edges):
            if "style" not in edge:
                edge["style"] = {}

            # Update the label font size in the style attribute
            px_str = edge["style"]["font-size"]  # Get px str for str label font size
            px_value = int(px_str.replace("px", ""))  # Remove 'px' and convert to integer
            new_px_str = f"{px_value * m}px"
            edge["style"]["font-size"] = new_px_str

    return nodes, edges



###############################################################################
###                       Default Graph Formatting                        ###
###############################################################################

def graph_reformatting(
    nodes_in: list[dict],
    edges_in: list[dict],
    selected_node: dict,
    app_config_in: dict,
)-> tuple[
    list[dict],  # new_nodes
    list[dict],  # new_edges
]:
    """
    Updates the label font size and the label background of the root nodes and its direct children nodes and edges.

    Inputs:
        nodes_in (list(dict)): List of node elements, where each element is a dictionary with "data" and optionally "style".
        edges_in (list(dict)): List of edge elements, where each element is a dictionary with "data" and optionally "style".
        selected_node (dict): Selected node that is on the top of the graph.
        app_config_in (dict): Configuration of the web app


    Outputs:
        new_nodes (list(dict)): Modified list of nodes with the target node's label font size and background color that are updated.
        new_edges (list(dict)): Modified list of edges with the target edge's label font size and background color that are updated.
    """

    "deepcopy"
    nodes_in = copy.deepcopy(nodes_in)
    edges_in = copy.deepcopy(edges_in)
    selected_node = copy.deepcopy(selected_node)

    # Highlight the top target node
    new_nodes = change_background_target_node(
        nodes=nodes_in,
        target_node_id=selected_node["id"],
        color_hex_code=app_config_in["highlighting_color"],
        echo_in=app_config_in["echo"],
    )

    # Get n+1 children nodes and connecting edges of the top node
    child_nodes_id, child_nodes, child_edges = find_children(
        node_id=selected_node["id"],
        nodes=new_nodes,
        edges=edges_in,
    )

    # Increase label font size of top node and its n+1 children nodes and connecting edges
    target_nodes = child_nodes + [selected_node]  # Add target node to list of target nodes
    new_nodes, new_edges = increase_font_nodes_edges(
        nodes=new_nodes,
        edges=edges_in,
        target_nodes=target_nodes,
        target_edges=child_edges,
        magnifying_ratio=app_config_in["magnifying_ratio"],
        echo_in=app_config_in["echo"],
    )

    return new_nodes, new_edges



"#############################################################################"
"###                          Manage HTML Elements                         ###"
"#############################################################################"

###############################################################################
###                        Create Navigation Sidebar                        ###
###############################################################################

def create_navigation_sidebar(
)-> html.Div:  # navigation_sidebar
    """
    Create an html navigation sidebar for the web app with clickable buttons that change the url of the app to access
    the different pages of the web app.

    Outputs:
        navigation_sidebar (html.Div): an html navigation sidebar for the web app.
    """

    "the style arguments for the sidebar (vertical nav)"
    sidebar_style = {
        "position": "fixed",  # The size (width) of the nav bar does not change with resizing of window
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "17rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    "Generate the html items for the side bar (nav)"
    navigation_sidebar = html.Div(
        [
            html.H2("SINTEF", className="display-3.5", style={'textAlign': 'center'}),  # display-X changes the size of the font
            html.H2("Uncertainty", className="display-3.5", style={'textAlign': 'center'}),
            html.H2("Guide", className="display-3.5", style={'textAlign': 'center'}),
            html.Hr(),  # Add horizontal line
            html.Br(),
            html.Div([
                html.P("Comprehensive"),
                html.P("Selection of"),
                html.P("Uncertainty"),
                html.P("Assessment Methods")
                ], className="lead", style={'textAlign': 'center', 'line-height': '20px'}
            ),
            html.Br(),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="/", active="exact", style={'textAlign': 'center'}),
                    dbc.NavLink("Flowchart Explorer", href="/flowchart_explorer", active="exact", style={'textAlign': 'center'}),
                    dbc.NavLink("Guided Selection Flowchart", href="/guided_selection_flowchart", active="exact", style={'textAlign': 'center'}),
                ],
                vertical=True,  # Orientation of the nav bar
                pills=True,  # The active page is highlighted
            ),
        ],
        style=sidebar_style,
    )

    return navigation_sidebar



###############################################################################
###                           Create Main Page Frame                        ###
###############################################################################

def create_main_page_frame(
)-> html.Div:  # main_page_content
    """
    Create the base html main page of the web app.
    This main page is initialized empty with just basic formatting to ensure size of all elements of the different pages
    of the web app that are generated dynamically and display inside that base main page.

    Outputs:
        main_page_content (html.Div): an html base main page the web app.
    """

    "the styles for the main content position it to the right of the sidebar and add some padding"
    content_style = {
        "margin-left": "18rem",
        "margin-right": "1rem",
        "padding": "0rem 0rem",
    }

    "The html item for the content of the main page"
    main_page_content = html.Div(
        id="page-content",
        children=[],  # Empty children in content that will be updated dynamically
        style=content_style,
    )

    return main_page_content



###############################################################################
###                        Render Content Home Page                         ###
###############################################################################

def render_content_home(
    app_config_in: dict
)-> html.Div:  # content
    """
    Generates content for the "Home" page.

    Outputs:
        content (html.Div): the html content to be displayed in the content window of the web-app home page
    """

    "Url video"
    video_url = html.A(  # Create hyperlink to webpage
        "Link to the Web App presentation video",  # Text hosting the link
        href="https://youtu.be/lcf45_EB9uM?si=Fg24fbc0F4P8xA8P",  # Link, url
        target="_blank"  # Option to open url in new tab
    )

    "Generate content"
    content = html.Div([
        html.H1("Interactive flowchart to select uncertainty assessment methods", style={'textAlign': 'center'}),
        html.Hr(),  # Add horizontal line
        html.Br(),  # Return carriage
        html.Div([
            dcc.Markdown("""
            This web-app is intended to help navigating and selecting the appropriate uncertainty assessment method among the many ones that exist.

            This web-app is developed and maintained led by SINTEF Community: https://www.sintef.no/en/community/

            A short presentation video of this guide can be found at the following link:
            """)]),
        html.Div(children=[video_url], style={'textAlign': 'center', 'margin-top': '-5px'}),
        # Use html.Div element to render a centered html. A url link in a text with new tab opening option
        html.Br(),
        dcc.Markdown("""       
                    For more information and/or help, please contact Hicham Johra by email: hicham.johra@sintef.no.
                    """),
        html.Br(),
        html.Br(),
        html.Hr(),
        html.Div([
            html.Img(src='assets/SINTEF_logo.png', style={'width': '300px', 'display': 'inline-block'}),  # Add image
        ], style={'text-align': 'center', 'width': '100%'}),
    ], style={"margin-left": "2rem"})

    if app_config_in["echo"]: print("Render front page")

    return content



###############################################################################
###               Render Content Guided Selection Flowchart                 ###
###############################################################################

def render_content_flowchart_explorer(
    app_memory_in: dict,
    app_config_in: dict,
)-> tuple[
    html.Div,  # content
    dict,  # new_app_memory
]:
    """
    Generates content for the "Flowchart" page.

    Outputs:
        content (html.Div): the html content to be displayed in the content window of the web-app
        new_app_memory (dict): the updated app_memory
    """

    "deepcopy of memory"
    new_app_memory = copy.deepcopy(app_memory_in)

    "update flowchart key into app_memory"
    new_app_memory["flowchart_key"] = new_app_memory["flowchart_key"] + 1

    "Build the graph to display"
    graph_data = copy.deepcopy(new_app_memory["current_graph_data"])
    cytoscape_graph = []
    cytoscape_elements = convert_to_cytoscape_elements(
        graph_data["nodes"],
        graph_data["edges"]
    )
    cytoscape_graph = copy.deepcopy(cytoscape_graph)

    "build graph layout"
    graph_layout = app_config_in["base_graph_layout"]
    graph_layout["roots"] = app_memory_in["current_graph_roots"]

    "Generate content"
    content = html.Div(
        [
            html.H1("Interactive flowchart to select uncertainty assessment methods",
                    style={'textAlign': 'center'}),
            html.Hr(),  # Add horizontal line
            #html.Br(),  # Return carriage

            dbc.Row(  # Use dbc.Row and dbc.Col to align the button to the right
                [
                    dbc.Col(
                        dbc.Button(
                            "Reset Exploration Graph",
                            id="reset-button",
                            n_clicks=0,
                            style={
                                "margin-left": "auto",  # Pushes the button to the right
                                "margin-top": "5px",  # Adds small padding on top
                                "margin-bottom": "5px",  # Adds small padding on bottom
                                "padding-right": "10px"  # Adds padding on the right
                            }
                        ),
                        width="auto",  # Ensures the button only takes as much width as needed
                        style={"textAlign": "right"}  # Align button to the right within the column
                    )
                ],
                justify="end",  # Align content of the row to the right
            ),

            cyto.Cytoscape(  # Tree graph
                id="cytoscape-graph",
                layout=graph_layout,
                style={"width": "100%", "height": "calc(100vh - 150px)"},  # Adjust height dynamically
                elements=cytoscape_elements,
                stylesheet=[
                    {
                        "selector": "node",
                        "style": {
                            "background-color": "data(style.background-color)",  # This should bind the style dynamically
                            "content": "data(label)",
                            "text-valign": "center",
                            "text-halign": "center",
                            "text-wrap": "wrap",  # Enable text wrapping
                            "shape": "rectangle",
                            "width": "label",
                            "height": "label",
                            "padding": "10px",
                            "color": "black",
                            "font-size": "data(style.font-size)",  # Dynamically bind the font size
                            "font-family": "Arial",
                        },
                    },
                    {
                        "selector": "edge",
                        "style": {
                            "curve-style": "bezier",
                            "target-arrow-shape": "triangle",
                            "arrow-scale": 2,
                            "label": "data(label)",
                            "text-wrap": "wrap",  # Enable text wrapping
                            "text-background-opacity": 1,
                            "text-background-color": "white",
                            "text-background-padding": "2px",
                            "color": "black",
                            "font-size": "data(style.font-size)",  # Dynamically bind the font size
                            "font-family": "Arial",
                        },
                    },
                ],
            ),
        ]
    )

    "echo"
    if app_config_in["echo"]:
        print("Render content flowchart")
        print(f"The number of nodes in the current graph is: {len(graph_data["nodes"])}")
        print(f"The number of edges in the current graph is: {len(graph_data["edges"])}")
        print(f"The flowchart key is: {new_app_memory["flowchart_key"]}")

    return content, new_app_memory



###############################################################################
###               Render Content Guided Selection Flowchart                 ###
###############################################################################

def render_content_guided_selection_flowchart(
    app_memory_in: dict,
    app_config_in: dict,
)-> tuple[
    html.Div,  # content
    dict,  # new_app_memory
]:
    """
    Generates content for the "Flowchart" page.

    Outputs:
        content (html.Div): the html content to be displayed in the content window of the web-app
        new_app_memory (dict): the updated app_memory
    """

    "deepcopy of memory"
    new_app_memory = copy.deepcopy(app_memory_in)

    "update flowchart key into app_memory"
    new_app_memory["flowchart_key"] = new_app_memory["flowchart_key"] + 1

    "Build the graph to display"
    graph_data = copy.deepcopy(new_app_memory["current_graph_data"])
    cytoscape_graph = []
    cytoscape_elements = convert_to_cytoscape_elements(
        graph_data["nodes"],
        graph_data["edges"]
    )
    cytoscape_graph = copy.deepcopy(cytoscape_graph)

    "build graph layout"
    graph_layout = app_config_in["base_graph_layout"]
    graph_layout["roots"] = app_memory_in["current_graph_roots"]

    "Generate content"
    content = html.Div(
        [
            html.H1("Interactive flowchart to select uncertainty assessment methods",
                    style={'textAlign': 'center'}),
            html.Hr(),  # Add horizontal line
            #html.Br(),  # Return carriage

            dbc.Row(  # Use dbc.Row and dbc.Col to align the button to the right
                [
                    dbc.Col(
                        dbc.Button(
                            "Reset Exploration Graph",
                            id="reset-button",
                            n_clicks=0,
                            style={
                                "margin-left": "auto",  # Pushes the button to the right
                                "margin-top": "5px",  # Adds small padding on top
                                "margin-bottom": "5px",  # Adds small padding on bottom
                                "padding-right": "10px"  # Adds padding on the right
                            }
                        ),
                        width="auto",  # Ensures the button only takes as much width as needed
                        style={"textAlign": "right"}  # Align button to the right within the column
                    )
                ],
                justify="end",  # Align content of the row to the right
            ),

            cyto.Cytoscape(  # Tree graph
                id="cytoscape-graph",
                layout=graph_layout,
                style={"width": "100%", "height": "calc(100vh - 150px)"},  # Adjust height dynamically
                elements=cytoscape_elements,
                stylesheet=[
                    {
                        "selector": "node",
                        "style": {
                            "background-color": "data(style.background-color)",  # This should bind the style dynamically
                            "content": "data(label)",
                            "text-valign": "center",
                            "text-halign": "center",
                            "text-wrap": "wrap",  # Enable text wrapping
                            "shape": "rectangle",
                            "width": "label",
                            "height": "label",
                            "padding": "10px",
                            "color": "black",
                            "font-size": "data(style.font-size)",  # Dynamically bind the font size
                            "font-family": "Arial",
                        },
                    },
                    {
                        "selector": "edge",
                        "style": {
                            "curve-style": "bezier",
                            "target-arrow-shape": "triangle",
                            "arrow-scale": 2,
                            "label": "data(label)",
                            "text-wrap": "wrap",  # Enable text wrapping
                            "text-background-opacity": 1,
                            "text-background-color": "white",
                            "text-background-padding": "2px",
                            "color": "black",
                            "font-size": "data(style.font-size)",  # Dynamically bind the font size
                            "font-family": "Arial",
                        },
                    },
                ],
            ),
        ]
    )

    "echo"
    if app_config_in["echo"]:
        print("Render content flowchart")
        print(f"The number of nodes in the current graph is: {len(graph_data["nodes"])}")
        print(f"The number of edges in the current graph is: {len(graph_data["edges"])}")
        print(f"The flowchart key is: {new_app_memory["flowchart_key"]}")

    return content, new_app_memory



###############################################################################
###                  Render Content Error Page Not Found                    ###
###############################################################################

def render_content_error_404(
    pathname_in: str,
)-> html.Div:  # content
    """
    Generates content for the "Error 404" page.

    Inputs:
        pathname_in (str): the url string

    Outputs:
        content (html.Div): the html content to be displayed in the content window of the web-app
    """

    content = html.Div(
        [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname_in} was not recognised..."),
        ],
    className="p-3 bg-light rounded-3",
    )

    return content



"#############################################################################"
"##                                                                         ##"
"##                              Initialization                             ##"
"##                                                                         ##"
"#############################################################################"

"#############################################################################"
"##                            Load Configuration                           ##"
"#############################################################################"

# Load the configuration from the YAML file
config_file_path = './config/config.yaml'  # Assumed to be in the config folder of the app

try:
    with open(config_file_path, 'r') as file:
        app_config = yaml.safe_load(file)  # Load YAML data into a Python dictionary # Global Variable with config file information: not dcc.Store cash memory

except Exception as e:
    raise ImportError("Error: yaml config file could not be loaded correctly.") from e

else:  # Load the configuration variables directly as global variables: change to implicit app_config if too many items
    # Access configuration variables
    #full_graph_layout = app_config["full_graph_layout"]
    echo = app_config["echo"]  # Set echo mode"

    if echo: print("The config file has been loaded successfully.")



"#############################################################################"
"##                         Initialization Feedback                         ##"
"#############################################################################"

if echo:
    print("Echo mode activated.\nInitialization of SINTEF Uncertainty Guide Web App.")
else:
    print("Echo mode inactive.")

"#############################################################################"
"##                        Initialization App Memory                        ##"
"#############################################################################"

try:
    # Initialize the AppData instance
    app_memory = AppMemory()

    # Load the full graph data from a JSON file
    app_memory.load_full_graph_data(app_config["graph_data_file_path"])

except Exception as e:
    raise ImportError("Error: yaml config file could not be loaded correctly.") from e

else:
    if echo: print("The app_memory has been successfully initialized.")



"#############################################################################"
"##                                                                         ##"
"##                                  Web App                                ##"
"##                                                                         ##"
"#############################################################################"

"#############################################################################"
"##                  Generate Main Front End App Structure                  ##"
"#############################################################################"

###############################################################################
###                             Create Dash App                             ###
###############################################################################

"Page style"
external_stylesheets = [dbc.themes.BOOTSTRAP]

"Start Dash app"
try:
    dash_app = dash.Dash(
        __name__,
        external_stylesheets=external_stylesheets,  # Layout style of the app
        suppress_callback_exceptions=True  # True when callbacks use inputs from components created by other callbacks
    )

    server = dash_app.server

    # Title of the Dash app on top of the page
    dash_app.title = "SINTEF Uncertainty Guide Web App"

    # Change the favicon of the app
    dash_app._favicon = 'SINTEF_favicon.ico'  # Need to place your favicon .ico directly in a folder \assets

except Exception as e:
    raise Exception("Error: the Dash App could not be created.") from e

else:
    if echo: print("The Dash App has been successfully created.")



###############################################################################
###                             Launch Dash App                             ###
###############################################################################

try:
    dash_app.layout = html.Div([
        dcc.Location(id="url"),

        create_navigation_sidebar(),  # Create the sidebar

        #content,  # Content display version without the hourglass icon
        dcc.Loading(children=[create_main_page_frame()],  # Create the base main page
                    color="#119DFF",
                    type="dot",
                    fullscreen=True
                    ),  # Use dcc.Loading to add hourglass icon when updating the web-app

        dcc.Store(id="app_memory",  # Store the app_memory data inside the user's current browser session
                  data=app_memory.memory,
                  storage_type="memory",  # "local" for data long-storage in cookies; "session" for data medium-storage for the whole session; "memory" for data short-storage in page
                  ),

        dcc.Store(id="app_config",  # Store the app_config data inside the user's current browser session
                  data=app_config,
                  storage_type="memory",  # "local" for data long-storage in cookies; "session" for data medium-storage for the whole session; "memory" for data short-storage in page
                  ),
    ])

except Exception as e:
    raise Exception("Error: the Dash App Layout could not be created.") from e

else:
    if echo: print("The Dash App Layout has been successfully created.")



"#############################################################################"
"##                                                                         ##"
"##                           Web App Callbacks                             ##"
"##                                                                         ##"
"#############################################################################"

"#############################################################################"
"##                       Callbacks Navigation Sidebar                       ##"
"#############################################################################"

###############################################################################
###                         Navigation Sidebar Main                         ###
###############################################################################

"""
Control and render the content (main) of the Dash App based on side bar 
actions and dcc.Store data updates"
"""
@dash_app.callback(
    [Output("page-content", "children"),
     Output("app_memory", "data", allow_duplicate=True)],
    Input("url", "pathname"),
    State('app_memory', 'data'),  # Get change of dcc.Store app_memory data for that page
    State('app_config', 'data'),  # Get change of dcc.Store app_config data for that page
    prevent_initial_call=True  # Allow initial first occurrence of the callback
)
def main_page_content_control(
    pathname_in: str,
    app_memory_in: dict,
    app_config_in: dict,
)-> tuple[
    html.Div,  # main_page_content
    dict,  # new_app_memory
]:
    new_app_memory = app_memory_in

    if app_config_in["echo"]: print(f"Activation navigation sidebar callback")

    if pathname_in == "/":
        if app_config_in["echo"]: print(f"Main page render control: Home page")
        main_page_content = render_content_home(app_config_in)
    elif pathname_in == "/flowchart_explorer":
        if app_config_in["echo"]: print(f"Main page render control: {pathname_in}")
        main_page_content, new_app_memory = render_content_flowchart_explorer(app_memory_in, app_config_in)
    elif pathname_in == "/guided_selection_flowchart":
        if app_config_in["echo"]: print(f"Main page render control: {pathname_in}")
        main_page_content, new_app_memory = render_content_guided_selection_flowchart(app_memory_in, app_config_in)
    else:
        if app_config_in["echo"]: print(f"Main page render control: {pathname_in}")
        main_page_content = render_content_error_404(pathname_in)
        if app_config_in["echo"]: print(f"Error 404 (Page not found) from main page render control")

    return main_page_content, new_app_memory



"#############################################################################"
"##                           Callbacks Home Page                           ##"
"#############################################################################"

#  None

"#############################################################################"
"##                            Callbacks Flowchart                          ##"
"#############################################################################"

###############################################################################
###                             Flowchart Main                              ###
###############################################################################

"""
Callback to handle reset and node click events
"""
@dash_app.callback(
    [Output("cytoscape-graph", "key"),
     Output("cytoscape-graph", "elements"),
     Output("cytoscape-graph", "layout"),
     Output("app_memory", "data", allow_duplicate=True)],
    Input("cytoscape-graph", "tapNodeData"),
    Input("reset-button", "n_clicks"),
    State('app_memory', 'data'),  # Get change of dcc.Store app_memory data for that page
    State('app_config', 'data'),  # Get change of dcc.Store app_config data for that page
    prevent_initial_call=True,
)
def handle_node_click_or_reset(
    selected_node: dict,
    reset_clicks: int,
    app_memory_in: dict,
    app_config_in: dict,
)-> tuple[
    str,  # cytoscape-graph key
    list,  # cytoscape-graph elements
    dict,  # cytoscape-graph layout
    dict,  # new_app_memory
]:

    "deepcopy"
    new_app_memory = copy.deepcopy(app_memory_in)
    graph_layout = copy.deepcopy(app_config_in["base_graph_layout"])

    "build graph layout"
    graph_layout["roots"] = new_app_memory["current_graph_roots"]

    "Identify input trigger ID"
    ctx_ = dash.callback_context
    if not ctx_.triggered:
        if app_config_in["echo"]: print("No user interaction with the page: do nothing")
        return dash.no_update, dash.no_update, graph_layout, new_app_memory

    triggered_id = ctx_.triggered[0]["prop_id"]  # get the input trigger ID

    if app_config_in["echo"]: print(f"ctx trigger ID: {triggered_id}")

    # Reset the graph if reset button is clicked
    if triggered_id == "reset-button.n_clicks" and reset_clicks > 0:  # Add > 0 condition on reset_clicks to avoid initial reset when loading page
        new_app_memory["flowchart_key"] = new_app_memory["flowchart_key"] + 1  # update flowchart key into app_memory
        new_app_memory["current_graph_data"] = copy.deepcopy(new_app_memory["full_graph_data"])
        new_app_memory["current_graph_roots"] = copy.deepcopy(new_app_memory["full_graph_roots"])

        # Reformat graph before display
        selected_node = find_single_node_from_id(
            nodes=new_app_memory["current_graph_data"]["nodes"],
            target_node_id=new_app_memory["current_graph_roots"][0],
        )
        if app_config_in["echo"]: print(f"Reset graph: The selected node is set as root of current graph: {selected_node}")

        nodes_temp, edges_temp = graph_reformatting(
            nodes_in=new_app_memory["current_graph_data"]["nodes"],
            edges_in=new_app_memory["current_graph_data"]["edges"],
            selected_node=selected_node,
            app_config_in=app_config_in,
        )

        cytoscape_graph = []
        cytoscape_graph = convert_to_cytoscape_elements(
            nodes=nodes_temp,
            edges=edges_temp,
        )
        cytoscape_graph = copy.deepcopy(cytoscape_graph)

        "build graph layout"
        graph_layout = copy.deepcopy(app_config_in["base_graph_layout"])
        graph_layout["roots"] = new_app_memory["current_graph_roots"]

        "echo"
        if app_config_in["echo"]:
            print("Update content flowchart: Reset graph")
            print(f"reset n click count: {reset_clicks}")
            print("nodes to be saved")
            print(new_app_memory["current_graph_data"]["nodes"])
            print("edges to be saved")
            print(new_app_memory["current_graph_data"]["edges"])
            print("List of roots to be saved")
            print(new_app_memory["current_graph_roots"])
            print(f"The number of nodes in the current graph is: {len(new_app_memory["current_graph_data"]["nodes"])}")
            print(f"The number of edges in the current graph is: {len(new_app_memory["current_graph_data"]["edges"])}")
            print(f"The flowchart key is: {new_app_memory["flowchart_key"]}")

        return str(new_app_memory["flowchart_key"]), cytoscape_graph, graph_layout, new_app_memory

    # If a node is clicked
    if selected_node and "id" in selected_node:
        new_app_memory["flowchart_key"] = int(new_app_memory["flowchart_key"] + 1)  # update flowchart key into app_memory
        node_id = str(selected_node["id"])
        node_data = next((node for node in new_app_memory["current_graph_data"]["nodes"] if node["id"] == node_id), None)

        # Get list of children and parents, if any
        child_nodes_id, child_nodes, child_edges = find_children(  # Find all children of selected node
            node_id=node_id,
            nodes=new_app_memory["current_graph_data"]["nodes"],
            edges=new_app_memory["current_graph_data"]["edges"]
        )

        parents_id, parents_nodes = find_parents(  # Find all parents of the selection node
            node_id=node_id,
            nodes=new_app_memory["current_graph_data"]["nodes"],
            edges=new_app_memory["current_graph_data"]["edges"]
        )

        # If the node is a leaf node (no children) or it has no visible parents, open the URL stored in the "data" element of the node
        if not child_nodes or not parents_id:  # If no children (leaf node) or no parents
            new_app_memory["flowchart_key"] = new_app_memory["flowchart_key"] + 1  # update flowchart key into app_memory

            if node_data and node_data["data"]:
                webbrowser.open_new_tab(node_data["data"])
                if app_config_in["echo"]: print("Update content flowchart: Open documentation")
            else:
                if app_config_in["echo"]: print("Update content flowchart: No available documentation to open")

            "echo"
            if app_config_in["echo"]:
                print(f"The number of nodes in the current graph is: {len(new_app_memory["current_graph_data"]["nodes"])}")
                print(f"The number of edges in the current graph is: {len(new_app_memory["current_graph_data"]["edges"])}")
                print("List of roots to be saved")
                print(new_app_memory["current_graph_roots"])
                print(f"The flowchart key is: {new_app_memory["flowchart_key"]}")

            return str(new_app_memory["flowchart_key"]), dash.no_update, graph_layout, new_app_memory

        # If the selected node has one or several visible parents in current graph, hide all parents and show only the subgraph below the selected node
        if parents_id:
            new_app_memory["flowchart_key"] = new_app_memory["flowchart_key"] + 1  # update flowchart key into app_memory

            # Start building the subtree from the selected node
            subtree_nodes, subtree_edges = get_subtree(
                node_id=node_id,
                nodes=new_app_memory["current_graph_data"]["nodes"],
                edges=new_app_memory["current_graph_data"]["edges"],
            )

            list_roots = find_roots_id(nodes=subtree_nodes, edges=subtree_edges)

            # Update the current graph in app_memory with new subgraph
            new_app_memory["current_graph_data"]["nodes"] = copy.deepcopy(subtree_nodes)
            new_app_memory["current_graph_data"]["edges"] = copy.deepcopy(subtree_edges)
            new_app_memory["current_graph_roots"] = copy.deepcopy(list_roots)

            "build graph layout"
            graph_layout = copy.deepcopy(app_config_in["base_graph_layout"])
            graph_layout["roots"] = new_app_memory["current_graph_roots"]

            # Graph reformatting before display on web page
            subtree_nodes_temp, subtree_edges_temp = graph_reformatting(
                nodes_in=subtree_nodes,
                edges_in=subtree_edges,
                selected_node=selected_node,
                app_config_in=app_config_in,
            )

            # Generate the cytoscape graph to display
            cytoscape_graph = []
            cytoscape_graph = convert_to_cytoscape_elements(
                nodes=subtree_nodes_temp,  # Use the temporary nodes to update with locally-increased font size
                edges=subtree_edges_temp,  # Use the temporary edges to update with locally-increased font size
            )
            cytoscape_graph = copy.deepcopy(cytoscape_graph)

            "echo"
            if app_config_in["echo"]:
                print("Update content flowchart: New sub-graph")
                print("nodes to be saved")
                print(subtree_nodes)
                print("edges to be saved")
                print(subtree_edges)
                print("List of roots to be saved")
                print(list_roots)
                print(f"The graph root should fit the selected node: {selected_node["id"]}")
                print(f"The number of nodes in the current graph is: {len(new_app_memory["current_graph_data"]["nodes"])}")
                print(f"The number of edges in the current graph is: {len(new_app_memory["current_graph_data"]["edges"])}")
                print(f"The flowchart key is: {new_app_memory["flowchart_key"]}")

            return str(new_app_memory["flowchart_key"]), cytoscape_graph, graph_layout, new_app_memory

    # Default behavior: return current graph with default graph formatting: triggered when loading Flowchart page
    if not selected_node:  # If no selected node (e.g., reset page without click), then use first root graph as selected node
        selected_node = find_single_node_from_id(
            nodes=new_app_memory["current_graph_data"]["nodes"],
            target_node_id=new_app_memory["current_graph_roots"][0],
        )
        if app_config_in["echo"]: print(f"No selected node. Selected node allocated to root of the graph: {selected_node}")
    else:
        if app_config_in["echo"]: print(f"The selected node is: {selected_node}")

    nodes_temp, edges_temp = graph_reformatting(
        nodes_in=new_app_memory["current_graph_data"]["nodes"],
        edges_in=new_app_memory["current_graph_data"]["edges"],
        selected_node=selected_node,
        app_config_in=app_config_in,
    )

    # Generate the cytoscape graph to display
    cytoscape_graph = []
    cytoscape_graph = convert_to_cytoscape_elements(
        nodes=nodes_temp,  # Use the temporary nodes to update with locally-increased font size
        edges=edges_temp,  # Use the temporary edges to update with locally-increased font size
    )
    cytoscape_graph = copy.deepcopy(cytoscape_graph)

    "echo"
    if app_config_in["echo"]:
        print("Default flowchart page formatting and rendering from current graph data")
        print(f"The number of nodes in the current graph is: {len(new_app_memory["current_graph_data"]["nodes"])}")
        print(f"The number of edges in the current graph is: {len(new_app_memory["current_graph_data"]["edges"])}")
        print(f"The flowchart key is: {new_app_memory["flowchart_key"]}")

    return str(new_app_memory["flowchart_key"]), cytoscape_graph, graph_layout, new_app_memory



"#############################################################################"
"##                                                                         ##"
"##                        Run Main: Local Server Mode                      ##"
"##                                                                         ##"
"#############################################################################"

if __name__ == "__main__":
    dash_app.run_server(host='127.0.0.1', port=5001, debug=True)  # Local mode for development