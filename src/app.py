import math
from matplotlib.figure import Figure
import solara
import networkx as nx

from model import (
    State,
    TikTokEchoChamber,
    number_conservative, number_progressive, number_neutral,
)
from mesa.visualization import (
    Slider,
    SolaraViz,
    make_plot_component,
    make_space_component,
)

from agents import AgentType


def agent_portrayal(agent):
    node_color_dict = {
        State.CONSERVATIVE: "tab:red",
        State.PROGRESSIVE: "tab:blue",
        State.NEUTRAL: "tab:gray",
    }
    node_shape_dict = {
        AgentType.HUMAN: "o",
        AgentType.BOT: "x",
    }
    return {"color": node_color_dict[agent.state],
            "marker": node_shape_dict[agent.type],
            "size": 25}


def get_cons_progressive_ratio(model):
    ratio = model.cons_progressive_ratio()
    ratio_text = r"$\infty$" if ratio is math.inf else f"{ratio: .2f}"
    infected_text = str(number_conservative(model))
    progressive_text = str(number_progressive(model))
    neutral_text = str(number_neutral(model))

    return solara.Markdown(
        f"Conservate/Progressive Ratio: {ratio_text}<br>"
        f"Progressive Count: {progressive_text}<br>"
        f"Conservative Count: {infected_text}<br>"
        f"Neutral Count: {neutral_text}<br>"
    )


def get_interactions(model):
    # TODO plot interactions
    ratio = model.cons_progressive_ratio()
    ratio_text = r"$\infty$" if ratio is math.inf else f"{ratio: .2f}"
    infected_text = str(number_conservative(model))
    progressive_text = str(number_progressive(model))

    return solara.Markdown(
        f"Conservative/Progressive Ratio: {ratio_text}<br>"
        f"Progressive Count: {progressive_text}<br>"
        f"Conservative Count: {infected_text}"
    )


def identify_clusters(model):

    conservative_graph = nx.Graph()
    progressive_graph = nx.Graph()
    neutral_graph = nx.Graph()

    for node in model.G.nodes():
        agent = model.grid.get_cell_list_contents([node])[0]
        if agent.state == State.CONSERVATIVE:
            conservative_graph.add_node(node)
        elif agent.state == State.PROGRESSIVE:
            progressive_graph.add_node(node)
        elif agent.state == State.NEUTRAL:
            neutral_graph.add_node(node)

    for edge in model.G.edges():
        u, v = edge
        agent_u = model.grid.get_cell_list_contents([u])[0]
        agent_v = model.grid.get_cell_list_contents([v])[0]

        if agent_u.state == agent_v.state:
            if agent_u.state == State.CONSERVATIVE:
                conservative_graph.add_edge(u, v)
            elif agent_u.state == State.PROGRESSIVE:
                progressive_graph.add_edge(u, v)
            elif agent_u.state == State.NEUTRAL:
                neutral_graph.add_edge(u, v)

    conservative_clusters = list(nx.connected_components(conservative_graph))
    progressive_clusters = list(nx.connected_components(progressive_graph))
    neutral_clusters = list(nx.connected_components(neutral_graph))

    all_clusters = conservative_clusters + progressive_clusters + neutral_clusters

    return all_clusters


def get_graphs(model):

    conservative_graph = nx.Graph()
    progressive_graph = nx.Graph()
    neutral_graph = nx.Graph()

    for node in model.G.nodes():
        agent = model.grid.get_cell_list_contents([node])[0]
        if agent.state == State.CONSERVATIVE:
            conservative_graph.add_node(node)
        elif agent.state == State.PROGRESSIVE:
            progressive_graph.add_node(node)
        elif agent.state == State.NEUTRAL:
            neutral_graph.add_node(node)

    for edge in model.G.edges():
        u, v = edge
        agent_u = model.grid.get_cell_list_contents([u])[0]
        agent_v = model.grid.get_cell_list_contents([v])[0]

        if agent_u.state == agent_v.state:
            if agent_u.state == State.CONSERVATIVE:
                conservative_graph.add_edge(u, v)
            elif agent_u.state == State.PROGRESSIVE:
                progressive_graph.add_edge(u, v)
            elif agent_u.state == State.NEUTRAL:
                neutral_graph.add_edge(u, v)

    conservative_clusters = list(nx.connected_components(conservative_graph))
    progressive_clusters = list(nx.connected_components(progressive_graph))
    neutral_clusters = list(nx.connected_components(neutral_graph))

    all_clusters = conservative_clusters + progressive_clusters + neutral_clusters

    return conservative_graph


def count_cross_cluster_interactions(model):

    cross_interactions = 0
    for edge in model.G.edges():
        u, v = edge
        agent_u = model.grid.get_cell_list_contents([u])[0]
        agent_v = model.grid.get_cell_list_contents([v])[0]

        if agent_u.state != agent_v.state:
            cross_interactions += 1

    return cross_interactions


def get_agent_stats(model):

    # Get basic state counts
    conservative_count = number_conservative(model)
    progressive_count = number_progressive(model)
    neutral_count = number_neutral(model)

    try:
        np_ratio = neutral_count / progressive_count
        np_ratio_text = f"{np_ratio:.2f}"
    except ZeroDivisionError:
        np_ratio_text = "∞"

    steps = model.steps

    markdown_text = f"""
    ## Agent Statistics

    - Conservative: {conservative_count}
    - Progressive: {progressive_count}
    - Neutral: {neutral_count}
    - Neutral/Progressive Ratio: {np_ratio_text}
    - Simulation Steps: {steps}
    """

    return solara.Markdown(markdown_text)


def get_cluster_stats(model):

    # Identify and analyze clusters
    clusters = identify_clusters(model)
    num_clusters = len(clusters)
    total_agents = model.num_nodes

    cluster_ratio = num_clusters / total_agents if total_agents > 0 else 0

    if num_clusters > 0:
        total_size = sum(len(cluster) for cluster in clusters)
        avg_cluster_size = total_size / num_clusters
    else:
        avg_cluster_size = 0

    cross_interactions = count_cross_cluster_interactions(model)

    markdown_text = f"""
    ## Cluster Analysis

    - Number of Clusters: {num_clusters}
    - Clusters/Agents Ratio: {cluster_ratio:.3f}
    - Average Cluster Size: {avg_cluster_size:.2f}
    - Cross-Cluster Interactions: {cross_interactions}
    """

    return solara.Markdown(markdown_text)


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Number Generator Seed",
    },
    "num_nodes": Slider(
        label="Number of agents",
        value=10,
        min=10,
        max=100,
        step=1,
    ),
    "avg_node_degree": Slider(
        label="Avg Node Degree",
        value=3,
        min=3,
        max=8,
        step=1,
    ),
    "num_bots": Slider(
        label="Number of Bots",
        value=1,
        min=1,
        max=10,
        step=1,
    ),
    "positive_chance": Slider(
        label="Probability to Follow",
        value=0.4,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "self_check_frequency": Slider(
        label="Self Check Frequency",
        value=0.4,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "politics_change_chance": Slider(
        label="Politics Change Chance",
        value=0.3,
        min=0.0,
        max=1.0,
        step=0.1,
    )
}

def post_process_lineplot(ax):
    ax.set_ylim(ymin=0)
    ax.set_ylabel("# people")
    ax.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")

def add_edges_plot(ax):
    # change edge color to black
    for edge in ax.collections:
        edge.set_edgecolor("red")


def SpacePlot(model):
    fig = Figure()
    ax = fig.add_subplot()

    # For larger networks, sample a subset of nodes to visualize
    G = model.G
    if len(G.nodes()) > 50:
        # Sample 50 nodes for visualization
        nodes_to_visualize = sorted(list(G.nodes()))[:50]
        G = G.subgraph(nodes_to_visualize)

    # Try to use a more efficient layout algorithm
    try:
        # Use kamada_kawai for smaller networks (more aesthetically pleasing)
        if len(G.nodes()) <= 30:
            pos = nx.kamada_kawai_layout(G)
        else:
            # Use spring layout with limited iterations for larger networks
            pos = nx.spring_layout(G, k=0.3, iterations=50, seed=42)
    except:
        # Fallback to basic spring layout with few iterations
        pos = nx.spring_layout(G, k=0.3, iterations=20, seed=42)

    # Extract node colors based on agent state
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        agents = model.grid.get_cell_list_contents([node])
        if agents:
            agent = agents[0]
            if agent.state == State.PROGRESSIVE:
                node_colors.append("blue")
            elif agent.state == State.CONSERVATIVE:
                node_colors.append("red")
            else:
                node_colors.append("gray")

            if agent.type == AgentType.BOT:
                node_sizes.append(150)  # Bigger size for bots
            else:
                node_sizes.append(100)  # Regular size for humans
        else:
            node_colors.append("gray")
            node_sizes.append(100)

    # Extract edge colors based on political similarity
    edge_colors = []
    for u, v in G.edges():
        weight = G[u][v].get('weight', 0.5)
        if weight > 0.7:
            edge_colors.append("green")
        elif weight > 0.3:
            edge_colors.append("yellow")
        else:
            edge_colors.append("red")

    # Draw the network
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=1.5, alpha=0.7, ax=ax)

    # Show a note if we're only displaying a subset
    if len(model.G.nodes()) > 50:
        ax.set_title(f"TikTok Echo Chamber Network (showing 50/{len(model.G.nodes())} nodes)")
    else:
        ax.set_title("TikTok Echo Chamber Network")

    ax.set_axis_off()

    return solara.FigureMatplotlib(fig)

def StatsRow(model):
    return solara.Row(children=[
        solara.Column(children=[get_agent_stats(model)], style={"width": "50%"}),
        solara.Column(children=[get_cluster_stats(model)], style={"width": "50%"})
    ], style={"width": "200%"})


SpacePlot = make_space_component(agent_portrayal)
StatePlot = make_plot_component(
    {"Conservative": "tab:red", "Progressive": "tab:blue", "Neutral": "tab:gray"},
    post_process=post_process_lineplot,
)

model1 = TikTokEchoChamber()

page = SolaraViz(
    model1,
    components=[
        SpacePlot,
        StatePlot,
        StatsRow,
    ],
    model_params=model_params,
    name="TikTok Echo Chamber Model",
)
page  # noqa
