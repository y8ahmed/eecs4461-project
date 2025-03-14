import math
import solara

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


def get_cons_progressive_ratio(model):
    ratio = model.cons_progressive_ratio()
    ratio_text = r"$\infty$" if ratio is math.inf else f"{ratio: .2f}"
    infected_text = str(number_conservative(model))
    progressive_text = str(number_progressive(model))
    neutral_text = str(number_neutral(model))

    # TODO mel to add graph output
    return solara.Markdown(
        f"Conservate/Progressive Ratio: {ratio_text}<br>"
        f"Progressive Count: {progressive_text}<br>"
        f"Conservative Count: {infected_text}<br>"
        f"Neutral Count: {neutral_text}<br>"
    )


def get_interactions(model):
    ratio = model.cons_progressive_ratio()
    ratio_text = r"$\infty$" if ratio is math.inf else f"{ratio: .2f}"
    infected_text = str(number_conservative(model))
    progressive_text = str(number_progressive(model))

    # TODO mel to add graph output
    return solara.Markdown(
        f"Neutral/Progressive Ratio: {ratio_text}<br>"
        f"Progressive Count: {progressive_text}<br>"
        f"Conservative Count: {infected_text}"
    )


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
    ax.set_ylabel("# agents")
    ax.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")


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
        get_cons_progressive_ratio,
    ],
    model_params=model_params,
    name="TikTok Echo Chamber Model",
)
page  # noqa
