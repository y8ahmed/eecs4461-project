import math

import networkx as nx
import mesa
from mesa import Model
from agents import State, TikTokAgent, AgentType


def number_state(model, state):
    return sum(1 for a in model.grid.get_all_cell_contents() if a.state is state)


def number_type(model, type):
    return sum(1 for a in model.grid.get_all_cell_contents() if a.type is type)


def number_human(model):
    return number_type(model, AgentType.HUMAN)


def number_bot(model):
    return number_type(model, AgentType.BOT)


def number_conservative(model):
    return number_state(model, State.CONSERVATIVE)


def number_progressive(model):
    return number_state(model, State.PROGRESSIVE)


def number_neutral(model):
    return number_state(model, State.NEUTRAL)


def get_interactions(model):
    return number_state(model, State.NEUTRAL)


class TikTokEchoChamber(Model):
    """A virus model with some number of agents.
    Based off of the Virus on a Network and Schelling Aggregation Models"""

    def __init__(
            self,
            num_nodes=10,
            avg_node_degree=3,
            num_bots=1,
            positive_chance=0.4,
            self_check_frequency=0.4,
            politics_change_chance=0.3,
            gain_resistance_chance=0.5,
            seed=None,
    ):
        """
        Create a new TikTokEchoChamber model.

        Args:
        :param num_nodes: Initial number of agents
        :param avg_node_degree: Average number of connections between agents
        :param num_bots: Initial number of infected nodes
        :param positive_chance: Probability of an infected agent to have positive interactions with others (0-1)
        :param self_check_frequency: How often agents check whether they are infected (0-1)
        :param politics_change_chance: Probability of an infected node to recover (0-1)
        :param gain_resistance_chance: Probability of a node that has recovered to become resistant (0-1)
        :param seed: Seed for reproducibility
        """
        super().__init__(seed=seed)
        self.num_nodes = num_nodes
        prob = avg_node_degree / self.num_nodes # this is for the probability for an edge to be connected
        self.G = nx.erdos_renyi_graph(n=self.num_nodes, p=prob)
        self.grid = mesa.space.NetworkGrid(self.G)

        self.num_bots = (
            num_bots if num_bots <= num_nodes else num_nodes
        )
        self.positive_chance = positive_chance
        self.self_check_frequency = self_check_frequency
        self.politics_change_chance = politics_change_chance
        self.gain_resistance_chance = gain_resistance_chance

        self.datacollector = mesa.DataCollector(
            {
                "Conservative": number_conservative,
                "Progressive": number_progressive,
                "Neutral": number_neutral,
                "Interactions": get_interactions
            }
        )

        # Create agents as human and neutral first
        idCounter = 0
        for node in self.G.nodes():
            a = TikTokAgent(
                idCounter,
                self,
                AgentType.HUMAN,
                State.NEUTRAL,
                self.positive_chance,
                self.self_check_frequency,
                self.politics_change_chance,
                self.gain_resistance_chance,
            )
            idCounter += 1
            # Attach the agent to the node
            self.grid.place_agent(a, node)

        # Make equal count conservative and progressive bot nodes.
        infected_nodes = self.random.sample(list(self.G), self.num_bots)
        for a in self.grid.get_cell_list_contents(infected_nodes):
            a.type = AgentType.BOT
            a.state = State.CONSERVATIVE
        progressive_nodes = self.random.sample(list(self.G), self.num_bots)
        for a in self.grid.get_cell_list_contents(progressive_nodes):
            a.type = AgentType.BOT
            a.state = State.PROGRESSIVE

        self.running = True
        self.datacollector.collect(self)

    def cons_progressive_ratio(self):
        try:
            return number_state(self, State.CONSERVATIVE) / number_state(self, State.PROGRESSIVE)
        except ZeroDivisionError:
            return math.inf

    def step(self):
        self.agents.shuffle_do("step")
        # collect data
        self.datacollector.collect(self)
        if number_neutral(self) == 0:
            self.running = False
