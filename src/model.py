import math

import networkx as nx
import mesa
from mesa import Model
from src.agents import State, TikTokAgent, AgentType


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


def number_cons_bots(model):
    return sum(1 for a in model.grid.agents if a.state is State.CONSERVATIVE and a.type is AgentType.BOT)


def number_prog_bots(model):
    return sum(1 for a in model.grid.agents if a.state is State.PROGRESSIVE and a.type is AgentType.BOT)


def number_cluster(model):
    clusters = identify_clusters(model)
    return len(clusters)


def cluster_ratio(model):
    return number_cluster(model) / model.num_nodes if model.num_nodes > 0 else 0


def avg_cluster_size(model):
    # Identify and analyze clusters
    clusters = identify_clusters(model)
    num_clusters = len(clusters)

    avg_size = 0
    if num_clusters > 0:
        total_size = sum(len(cluster) for cluster in clusters)
        avg_size = total_size / num_clusters

    return avg_size


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


def count_cross_cluster_interactions(model):

    cross_interactions = 0
    for edge in model.G.edges():
        u, v = edge
        agent_u = model.grid.get_cell_list_contents([u])[0]
        agent_v = model.grid.get_cell_list_contents([v])[0]

        if agent_u.state != agent_v.state:
            cross_interactions += 1

    return cross_interactions


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
            become_neutral_chance=0.5,
            seed=None,
    ):
        """
        Create a new TikTokEchoChamber model.

        Args:
        :param num_nodes: Initial number of agents
        :param avg_node_degree: Average number of connections between agents
        :param num_bots: Initial number of infected nodes
        :param positive_chance: Probability of an infected agent to have positive interactions with others (0-1)
        :param become_neutral_chance: Probability of a node to become neutral (0-1)
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
        self.become_neutral_chance = become_neutral_chance

        self.datacollector = mesa.DataCollector(
            {
                "Conservative": number_conservative,
                "Progressive": number_progressive,
                "Neutral": number_neutral,
                "Num_Cluster": number_cluster,
                "Avg_Cluster": avg_cluster_size,
            }
        )

        # store number of bots for each political leaning
        self.number_cons_bots = number_cons_bots(self)
        self.number_prog_bots = number_prog_bots(self)

        # keep track of each interaction per step
        self.interactions = ""
        self.pos = nx.spring_layout(self.G, k=0.3, iterations=20, seed=seed)

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
                self.pos = nx.spring_layout(self.G, k=0.3, iterations=50, seed=seed)
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
                self.become_neutral_chance,
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
