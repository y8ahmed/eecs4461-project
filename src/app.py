from matplotlib.figure import Figure
import solara
import networkx as nx

from agents import AgentType, EdgeWeight
from model import (
    State,
    TikTokEchoChamber,
    number_conservative, number_progressive, number_neutral, cons_progressive_ratio, step_interactions,
    identify_clusters
)
from mesa.visualization import (
    Slider,
    SolaraViz,
    make_plot_component
)


def get_agent_stats(model):
    # Get basic state counts
    conservative_count = number_conservative(model)
    progressive_count = number_progressive(model)
    neutral_count = number_neutral(model)

    try:
        np_ratio = cons_progressive_ratio(model)
        np_ratio_text = f"{np_ratio:.2f}"
    except ZeroDivisionError:
        np_ratio_text = "∞"

    markdown_text = f"""
    ## Agent Statistics

    - Conservative: {conservative_count}
    - Progressive: {progressive_count}
    - Neutral: {neutral_count}
    - Conservative/Progressive Ratio: {np_ratio_text}
    """

    return solara.Markdown(markdown_text)


def get_cluster_stats(model):
    # Get and display cluster stats from model
    clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions = identify_clusters(model)

    # Transform clusters list into dictionary format
    cluster_dict = {}
    for node_idx, cluster_id in enumerate(clusters):
        if cluster_id not in cluster_dict:
            cluster_dict[cluster_id] = []
        cluster_dict[cluster_id].append(node_idx + 1)  # Add 1 to convert to 1-indexed

    # Format cluster dictionary for display
    cluster_display = "<br />".join(f"{cluster_id}: {node_list}" for cluster_id, node_list in sorted(cluster_dict.items()))

    markdown_text = f"""
    ## Cluster Analysis

    - Number of Clusters: {number_cluster}
    - Clusters/Agents Ratio: {cluster_ratio:.2f}
    - Average Cluster Size: {avg_cluster_size:.0f}
    - Cross-Cluster Interactions: {cross_interactions}
    
    ### Cluster Assignments
    {cluster_display}
    """

    return solara.Markdown(markdown_text)


def get_interactions(model):
    text = step_interactions(model)
    markdown_text = f"""
    Agent Actions

    {text}
    """
    return solara.Markdown(markdown_text)


model_params = {
    "seed": {
        "type": "SliderInt",
        "value": 42,
        "label": "Random Number Generator Seed",
    },
    "num_nodes": Slider(
        label="Number of agents",
        value=10,
        min=10,
        max=50,
        step=1,
    ),
    "avg_node_degree": Slider(
        label="Avg Node Degree",
        value=3,
        min=1,
        max=5,
        step=1,
    ),
    "num_cons_bots": Slider(
        label="Num of Conservative Bots",
        value=1,
        min=1,
        max=10,
        step=1,
    ),
    "num_prog_bots": Slider(
        label="Num of Progressive Bots",
        value=1,
        min=1,
        max=10,
        step=1,
    ),
    "positive_chance": Slider(
        label="Probability to Follow",
        value=0.5,
        min=0.0,
        max=1.0,
        step=0.1,
    ),
    "become_neutral_chance": Slider(
        label="Become Neutral Chance",
        value=0.2,
        min=0.0,
        max=1.0,
        step=0.1,
    )
}


def post_process_lineplot(ax):
    ax.set_ylim(ymin=0)
    ax.set_ylabel("# agents")
    ax.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")


def SpacePlot(model):
    fig = Figure()
    ax = fig.add_subplot()

    # Extract node colors based on agent state
    bot_nodes = []
    hum_nodes = []
    all_nodes = []
    bot_colors = []
    hum_colors = []
    for agent in model.grid.agents:
        node = agent.id_
        all_nodes.append(node)
        if agent.type == AgentType.BOT:
            if agent.state == State.PROGRESSIVE:
                bot_nodes.append(node)
                bot_colors.append("blue")
            if agent.state == State.CONSERVATIVE:
                bot_nodes.append(node)
                bot_colors.append("red")
        if agent.type == AgentType.HUMAN:
            if agent.state == State.PROGRESSIVE:
                hum_nodes.append(node)
                hum_colors.append("blue")
            if agent.state == State.CONSERVATIVE:
                hum_nodes.append(node)
                hum_colors.append("red")
            if agent.state == State.NEUTRAL:
                hum_nodes.append(node)
                hum_colors.append("gray")

    # Set edge transparency based on political similarity; style based on interaction weight
    edge_alphas = []
    edge_styles = []
    for u, v in model.G.edges():
        edge_alphas.append(0 if model.G[u][v].get('weight') == EdgeWeight.INVISIBLE else 0.5)
        edge_styles.append('dashed' if model.G[u][v].get('weight') == EdgeWeight.DASHED else 'solid')

    # Create pos for bot nodes and human nodes
    botpos = {k: v for k, v in model.pos.items() if k in bot_nodes}
    humpos = {k: v for k, v in model.pos.items() if k in hum_nodes}
    allpos = botpos | humpos

    # Draw the networks
    nx.draw_networkx_nodes(model.G, humpos, nodelist=hum_nodes, node_color=hum_colors, node_shape="o", node_size=100, ax=ax, label="Human")
    nx.draw_networkx_nodes(model.G, botpos, nodelist=bot_nodes, node_color=bot_colors, node_shape="x", node_size=100, ax=ax, label="Bot")
    nx.draw_networkx_edges(model.G, model.pos, edge_color="gray", width=1, alpha=edge_alphas, style=edge_styles, ax=ax)
    label_options = {"fc": "white", "alpha": 0.6, "boxstyle": "circle", "linestyle": ""}
    nx.draw_networkx_labels(model.G, allpos, font_size=8, bbox=label_options, ax=ax)

    # Show a note if we're only displaying a subset
    if len(model.G.nodes()) > 50:
        ax.set_title(f"TikTok Echo Chamber Network (showing 50/{len(model.G.nodes())} nodes)")
    else:
        ax.set_title("TikTok Echo Chamber Network")

    ax.legend(loc="best")
    ax.set_axis_off()

    return solara.FigureMatplotlib(fig)

def StatsRow(model):
    return solara.Row(children=[
        solara.Column(children=[get_agent_stats(model)], style={"width": "30%"}),
        solara.Column(children=[get_cluster_stats(model)], style={"width": "30%"}),
        # solara.Column(children=[get_interactions(model)], style={"width": "40%"})
    ], style={"width": "200%"})


StatePlot = make_plot_component(
    {"Conservative": "tab:red", "Progressive": "tab:blue", "Neutral": "tab:gray"},
    post_process=post_process_lineplot,
)

model1  = TikTokEchoChamber()

page = SolaraViz(
    model1,
    components=[
        SpacePlot,
        StatePlot,
        StatsRow
    ],
    model_params=model_params,
    name="TikTok Echo Chamber Model",
)

page  # noqa
