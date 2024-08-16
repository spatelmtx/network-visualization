import os
import pandas as pd
from pyvis.network import Network
import random
from collections import defaultdict
import streamlit as st
import streamlit.components.v1 as components

# Function to generate a random color
def generate_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Streamlit UI
st.title("Network Visualization for Health and Organoleptic Effects")

# Load the CSV file directly
csv_file = "health_effect_details_with_class.csv"
if os.path.exists(csv_file):
    data = pd.read_csv(csv_file)

    # Determine the maximum or minimum correlation based on Correlation_Type
    def get_extreme_correlation(row):
        if row['Correlation_Type'] == 'positive':
            return row[['Control', 'Obesity', 'T2D']].max()
        elif row['Correlation_Type'] == 'negative':
            return row[['Control', 'Obesity', 'T2D']].min()
        else:
            return row[['Control', 'Obesity', 'T2D']].iloc[0]  # Default to control if type is neither positive nor negative

    data['Extreme_Correlation'] = data.apply(get_extreme_correlation, axis=1)
    data['Correlation_Category'] = data.apply(lambda row: ['Control', 'Obesity', 'T2D'][row[['Control', 'Obesity', 'T2D']].tolist().index(row['Extreme_Correlation'])], axis=1)

    # Filter data based on Extreme_Correlation values
    filtered_data = data[(data["Extreme_Correlation"] > 0.6) | 
                         (data["Extreme_Correlation"] < -0.6) | 
                         (data["Extreme_Correlation"] == 0)]

    # Create a Network object for each correlation type
    networks = defaultdict(lambda: Network(notebook=True, height='800px', width='100%', bgcolor='#ffffff', font_color='black'))

    # Define dictionaries for node attributes and information
    health_color_map = {}
    organoleptic_color_map = {}

    # Process each entry to create graphs for each combination
    for _, entry in filtered_data.iterrows():
        genus = entry["Genus"]
        metabolite = entry["Metabolite"]
        correlation_type = entry["Correlation_Type"]
        extreme_correlation = entry["Extreme_Correlation"]
        category = entry["Correlation_Category"]
        health_effect_class = entry["Health effect Class"]
        health_effect_details = entry["Health effect"]
        organoleptic_effect = entry["Organoleptic effect"]

        # Key for network dict
        key = f"{correlation_type}_{health_effect_class}"

        # Add genus node (Circle shape) with no label
        if genus not in [node['id'] for node in networks[key].nodes]:
            networks[key].add_node(
                genus,
                type='genus',
                size=30,
                color='green',
                title=genus,
                shape='circle',
                label=None  # Ensure no label is shown
            )

        # Add or update metabolite node with no label
        if metabolite not in [node['id'] for node in networks[key].nodes]:
            title = f"Metabolite:{metabolite}\nGenus: {genus}\nCorrelation: {extreme_correlation} ({category})"
            networks[key].add_node(
                metabolite,
                type='metabolite',
                size=30,
                color='red',
                title=title,
                shape='box',
                label=None  # Ensure no label is shown
            )
        else:
            # Update existing node with new information only if necessary
            existing_node = next(node for node in networks[key].nodes if node['id'] == metabolite)
            if f"Genus: {genus}" not in existing_node['title']:
                existing_node['title'] += f"\nGenus: {genus}\nCorrelation: {extreme_correlation} ({category})"

        # Add edge between genus and metabolite
        edge_color = 'blue' if correlation_type == 'positive' else 'orange'
        edge_width = max(abs(extreme_correlation) * 10, 1)  # Ensure minimum width is 1
        networks[key].add_edge(genus, metabolite, color=edge_color, width=edge_width)

        # Add 'Health Effect' node (Triangle shape) with no label
        if pd.notna(health_effect_class):
            if health_effect_class not in health_color_map:
                health_color_map[health_effect_class] = generate_random_color()

            if health_effect_class not in [node['id'] for node in networks[key].nodes]:
                networks[key].add_node(
                    health_effect_class,
                    type='health_effect',
                    size=30,
                    color=health_color_map[health_effect_class],
                    title=f"{health_effect_class}\nHealth effect: {health_effect_details}",
                    shape='triangle',
                    label=None  # Ensure no label is shown
                )
            else:
                # Update existing node with new information only if necessary
                existing_node = next(node for node in networks[key].nodes if node['id'] == health_effect_class)
                if f"Health effect: {health_effect_details}" not in existing_node['title']:
                    existing_node['title'] += f"\nHealth effect: {health_effect_details}"

            # Add edge to the health effect class
            if health_effect_class in [node['id'] for node in networks[key].nodes]:
                networks[key].add_edge(metabolite, health_effect_class, color='purple', width=3)

        # Add 'Organoleptic effect' node (Star shape) with no label
        if pd.notna(organoleptic_effect):
            if organoleptic_effect not in organoleptic_color_map:
                organoleptic_color_map[organoleptic_effect] = generate_random_color()

            if organoleptic_effect not in [node['id'] for node in networks[key].nodes]:
                networks[key].add_node(
                    organoleptic_effect,
                    type='organoleptic_effect',
                    size=30,
                    color=organoleptic_color_map[organoleptic_effect],
                    title=organoleptic_effect,
                    shape='star',
                    label=None  # Ensure no label is shown
                )
            if metabolite in [node['id'] for node in networks[key].nodes] and organoleptic_effect in [node['id'] for node in networks[key].nodes]:
                networks[key].add_edge(metabolite, organoleptic_effect, color='red', width=3)

    # Update node labels after adding nodes
    for key, net in networks.items():
        for node in net.nodes:
            node['label'] = None

    # Create a directory to save HTML files if it doesn't exist
    output_dir = "html_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save each network graph as an HTML file
    for key, net in networks.items():
        file_path = os.path.join(output_dir, f"{key}.html")
        net.save_graph(file_path)

    # Sidebar selection for graph display with a placeholder option
    st.sidebar.subheader("Select Graph")
    graph_keys = ['Select Graph'] + list(networks.keys())
    selected_graph = st.sidebar.selectbox("Choose a Graph", graph_keys)

    # Display selected graph
    if selected_graph != 'Select Graph' and selected_graph:
        file_path = os.path.join(output_dir, f"{selected_graph}.html")
        st.write(f"### {selected_graph.replace('_', ' ').title()}")
        with open(file_path, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=800)

else:
    st.write(f"CSV file '{csv_file}' not found. Please ensure it exists in the directory.")
