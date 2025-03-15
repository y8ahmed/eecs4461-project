import math

import networkx as nx
import mesa
from mesa import Model
from agents import State, TikTokAgent, AgentType


def number_state(model, state):
    return sum(1 for a in model.grid.get_all_cell_contents() if a.state is state)


def number_type(model, type):
    return sum(1 for a in model.grid.get_all_cell_contents() if a.type is type)


def number_conservative(model):
    return number_state(model, State.CONSERVATIVE)


def number_progressive(model):
    return number_state(model, State.PROGRESSIVE)


def number_neutral(model):
    return number_state(model, State.NEUTRAL)


def cons_progressive_ratio(self):
    try:
        return number_state(self, State.CONSERVATIVE) / number_state(self, State.PROGRESSIVE)
    except ZeroDivisionError:
        return math.inf


def step_interactions(model):
    return model.interactions


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
        self.G = nx.powerlaw_cluster_graph(n=num_nodes, m=avg_node_degree, p=prob, seed=seed)  # to increase likelihood that all nodes are connected
        self.grid = mesa.space.NetworkGrid(self.G)
        self.G = self.G.to_directed()

        self.num_bots = num_bots if num_bots <= num_nodes else num_nodes
        self.positive_chance = positive_chance
        self.self_check_frequency = self_check_frequency
        self.politics_change_chance = politics_change_chance
        self.gain_resistance_chance = gain_resistance_chance

        self.datacollector = mesa.DataCollector(
            {
                "Conservative": number_conservative,
                "Progressive": number_progressive,
                "Neutral": number_neutral,
            }
        )
        self.interactions = ""  # keep track of each interaction per step
        self.pos = nx.spring_layout(self.G, k=0.3, iterations=20)

        # Initialize the grid

        # For larger networks, sample a subset of nodes to visualize
        if len(self.G.nodes()) > 50:
            # Sample 50 nodes for visualization
            nodes_to_visualize = sorted(list(self.G.nodes()))[:50]
            self.G = self.G.subgraph(nodes_to_visualize)

        # Try to use a more efficient layout algorithm
        try:
            # Use kamada_kawai for smaller networks (more aesthetically pleasing)
            if len(self.G.nodes()) <= 30:
                self.pos = nx.kamada_kawai_layout(self.G)
            else:
                # Use spring layout with limited iterations for larger networks
                self.pos = nx.spring_layout(self.G, k=0.3, iterations=50)
        except:
            # Fallback to basic spring layout with few iterations
            pass

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

        # Add edge weights based on political similarity - 0.1 so the graph looks disconnected at the start
        for u, v in self.G.edges():
            self.G[u][v]['weight'] = 0.1

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")
        # collect data
        self.datacollector.collect(self)
        if number_neutral(self) == 0:
            self.running = False
