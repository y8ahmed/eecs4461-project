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
    # TODO give these directed edges. need zorder
    return {"color": node_color_dict[agent.state],
            "marker": node_shape_dict[agent.type],
            # "zorder": 1,  # TODO confirm what this does - outward or inward
            "size": 25}


def get_neutral_progressive_ratio(model):
    ratio = model.neutral_progressive_ratio()
    ratio_text = r"$\infty$" if ratio is math.inf else f"{ratio: .2f}"
    infected_text = str(number_conservative(model))
    progressive_text = str(number_progressive(model))
    neutral_text = str(number_neutral(model))

    # TODO mel to add graph output
    return solara.Markdown(
        f"Neutral/Progressive Ratio: {ratio_text}<br>"
        f"Progressive Count: {progressive_text}<br>"
        f"Conservative Count: {infected_text}<br>"
        f"Neutral Count: {neutral_text}"
    )


model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
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
    "initial_outbreak_size": Slider(
        label="Initial Outbreak Size",
        value=1,
        min=1,
        max=10,
        step=1,
    ),
    "virus_spread_chance": Slider(
        label="Virus Spread Chance",
        value=0.4,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "virus_check_frequency": Slider(
        label="Virus Check Frequency",
        value=0.4,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "recovery_chance": Slider(
        label="Recovery Chance",
        value=0.3,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "density": Slider(
        label="Density",
        value=0.8,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "homophily": Slider(
        label="Homophily",
        value=0.4,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
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
        get_neutral_progressive_ratio,
    ],
    model_params=model_params,
    name="TikTok Echo Chamber Model",
)
page  # noqa
