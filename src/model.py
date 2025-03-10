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


class TikTokEchoChamber(Model):
    """A virus model with some number of agents.
    Based off of the Virus on a Network and Schelling Aggregation Models"""

    def __init__(
            self,
            num_nodes=10,
            avg_node_degree=3,
            initial_outbreak_size=1,
            virus_spread_chance=0.4,
            virus_check_frequency=0.4,
            recovery_chance=0.3,
            gain_resistance_chance=0.5,
            density=0.8,
            homophily=0.4,
            seed=None,
    ):
        """
        Create a new TikTokEchoChamber model.

        Args:
        :param num_nodes: Initial number of agents
        :param avg_node_degree: Average number of connections between agents
        :param initial_outbreak_size: Initial number of infected nodes
        :param virus_spread_chance: Probability of an infected agent to have positive interactions with others (0-1)
        :param virus_check_frequency: How often agents check whether they are infected (0-1)
        :param recovery_chance: Probability of an infected node to recover (0-1)
        :param gain_resistance_chance: Probability of a node that has recovered to become resistant (0-1)
        :param density: Initial chance for a cell to be populated (0-1)
        :param homophily: Minimum number of similar neighbors needed for echo chamber
        :param seed: Seed for reproducibility
        """
        super().__init__(seed=seed)
        self.num_nodes = num_nodes
        prob = avg_node_degree / self.num_nodes # this is for the probability for an edge to be connected
        # TODO give these directed edges. need zorder. directed=True causes error. Don't think it's possible.
        self.G = nx.erdos_renyi_graph(n=self.num_nodes, p=prob)
        self.grid = mesa.space.NetworkGrid(self.G)

        self.initial_outbreak_size = (
            initial_outbreak_size if initial_outbreak_size <= num_nodes else num_nodes
        )
        self.virus_spread_chance = virus_spread_chance
        self.virus_check_frequency = virus_check_frequency
        self.recovery_chance = recovery_chance
        self.gain_resistance_chance = gain_resistance_chance

        self.datacollector = mesa.DataCollector(
            {
                "Conservative": number_conservative,
                "Progressive": number_progressive,
                "Neutral": number_neutral,
                "N over P": self.neutral_progressive_ratio,
            }
        )

        # Create agents as human and neutral first
        for node in self.G.nodes():
            a = TikTokAgent(
                self,
                AgentType.HUMAN,
                State.NEUTRAL,
                self.virus_spread_chance,
                self.virus_check_frequency,
                self.recovery_chance,
                self.gain_resistance_chance,
            )

            # Add the agent to the node
            self.grid.place_agent(a, node)

        # Make some conservative bot nodes.
        infected_nodes = self.random.sample(list(self.G), self.initial_outbreak_size)
        for a in self.grid.get_cell_list_contents(infected_nodes):
            a.type = AgentType.BOT
            a.state = State.CONSERVATIVE

        # Make some progressive bot nodes.
        progressive_nodes = self.random.sample(list(self.G), self.initial_outbreak_size)
        for a in self.grid.get_cell_list_contents(progressive_nodes):
            a.type = AgentType.BOT
            a.state = State.PROGRESSIVE

        self.running = True
        self.datacollector.collect(self)

    def neutral_progressive_ratio(self):
        try:
            return number_state(self, State.NEUTRAL) / number_state(self, State.PROGRESSIVE)
        except ZeroDivisionError:
            return math.inf

    def step(self):
        self.agents.shuffle_do("step")
        # collect data
        self.datacollector.collect(self)
        if number_neutral(self) == 0:
            self.running = False
