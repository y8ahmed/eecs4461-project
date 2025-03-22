import math

import networkx as nx
import mesa
from mesa import Model
from agents import State, TikTokAgent, AgentType, EdgeWeight


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


def get_unique_edge_list(edges):
    unique_edge_list = []
    for u, v in edges:
        if (u, v) not in unique_edge_list and (v, u) not in unique_edge_list:
            unique_edge_list.append((u, v))

    return unique_edge_list


def identify_clusters(model) -> tuple[list, int, float, float, int]:
    """Group nodes by similarity and connectedness. Returns a list of:
        [0]: list of cluster ids for each node. 0-indexed.
        [1]: number of clusters
        [2]: avg_cluster_size
        [3]: cluster_ratio
        [4]: cross_interactions
    """

    # Cluster Definition: a group of nodes:
    # - with similar leaning
    # - that are connected
    # ie: there exists a path from each node to every other node without going through a dissimilar node

    # the cluster id for each node is initialized to the node's id
    clusters = [node for node in model.G.nodes()]
    cross_interactions = 0

    '''if an edge is visible either way then they are connected'''
    all_visible_edges = [(u, v) for u, v in model.G.edges()
                         if model.G[u][v]['weight'] != EdgeWeight.INVISIBLE or
                         model.G[v][u]['weight'] != EdgeWeight.INVISIBLE]
    visible_edges = get_unique_edge_list(all_visible_edges)  # get unique pairs since edges may be dupes eg.(1,3), (3,1)

    # try to find connected similar nodes and update their cluster id. note that edges are ordered.
    # do it twice to ensure earlier nodes are updated
    for _ in [1, 2]:
        for u, v in visible_edges:
            # print(f"(u {u} v {v}) ids start (clusters[u] {clusters[u]} clusters[v] {clusters[v]}")
            agent_u = model.grid.get_cell_list_contents([u])[0]
            agent_v = model.grid.get_cell_list_contents([v])[0]
            min_id = min(clusters[u], clusters[v])

            # check similarity of agents
            if agent_u.state == agent_v.state:
                # make cluster ids the same
                clusters[u] = min_id
                clusters[v] = min_id
                # print(f"(u {u} v {v}) are same and ids updated. clusters[u] {clusters[u]}, clusters[v] {clusters[v]}")
            else:
                # make new cluster for the dissimilar node and update cluster id
                node_to_change = u if clusters[u] != min_id else v
                # clusters[node_to_change] = min_id + 1
                cross_interactions += 1  # keep count of cross-cluster interactions
                # print(f"(u {u} v {v}) node_to_change {node_to_change} clusters[node_to_change] {clusters[node_to_change]}  cross_interactions {cross_interactions}")

    # prep return values
    unique_clusters = set(clusters)
    number_cluster = len(unique_clusters)
    cluster_ratio = number_cluster / model.num_nodes if model.num_nodes > 0 else 0

    sum_size = sum(clusters.count(c) for c in unique_clusters)
    avg_cluster_size = sum_size / number_cluster

    # print(f"clusters {clusters} number_cluster {number_cluster} avg_cluster_size {avg_cluster_size} cluster_ratio {cluster_ratio} cross_interactions {cross_interactions}")
    return clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions


def cons_progressive_ratio(self):
    try:
        return number_state(self, State.CONSERVATIVE) / number_state(self, State.PROGRESSIVE)
    except ZeroDivisionError:
        return math.inf


def step_interactions(model):
    return model.interactions


class TikTokEchoChamber(Model):
    """A TikTok Echo Chamber model with some number of bots and human agents.
    Based off of the Virus on a Network and Schelling Aggregation Models"""

    def __init__(
            self,
            num_nodes=10,
            avg_node_degree=3,
            num_cons_bots=1,
            num_prog_bots=1,
            positive_chance=0.4,
            become_neutral_chance=0.5,
            seed=None,
    ):
        """
        Create a new TikTokEchoChamber model.

        Args:
        :param num_nodes: Number of agents
        :param avg_node_degree: Average number of edges between agents. Determines how many agents one can reach during the simulation.
        :param num_cons_bots: Number of conservative bot agents
        :param num_prog_bots: Number of progressive bot agents
        :param positive_chance: Probability of an agent to have positive interactions with others (0-1)
        :param become_neutral_chance: Probability of an agent to become neutral (0-1)
        :param seed: Seed for reproducibility
        """
        super().__init__(seed=seed)
        self.num_nodes = num_nodes
        prob = avg_node_degree / self.num_nodes # this is for the probability for an edge to be connected
        self.G = nx.powerlaw_cluster_graph(n=num_nodes, m=avg_node_degree, p=prob, seed=seed)  # to increase likelihood that all nodes are connected
        self.grid = mesa.space.NetworkGrid(self.G)
        self.G = self.G.to_directed()

        # determine number of bots for each political leaning
        num_bots = num_cons_bots + num_prog_bots
        if num_bots <= num_nodes:
            self.num_cons_bots = num_cons_bots
            self.num_prog_bots = num_prog_bots
        else:
            # try to evenly split dist
            half = num_nodes // 2
            self.num_cons_bots = half
            self.num_prog_bots = half

        self.positive_chance = positive_chance
        self.become_neutral_chance = become_neutral_chance

        # keep track of each interaction per step
        self.interactions = ""
        self.pos = nx.spring_layout(self.G, k=0.3, iterations=20, seed=seed)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Conservative": number_conservative,
                "Progressive": number_progressive,
                "Neutral": number_neutral
            },
            tables={
                "CA": ["Clusters", "Num_Clusters", "Avg_Cluster_Size", "Clstr_Agent_Ratio", "Cross_Interactions"]
            }
        )

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
        cons_nodes = self.random.sample(list(self.G), self.num_cons_bots)
        for a in self.grid.get_cell_list_contents(cons_nodes):
            a.type = AgentType.BOT
            a.state = State.CONSERVATIVE
        no_cons_list = list(set(list(self.G)) - set(cons_nodes))  # ensure no overlap between cons and prog nodes
        prog_nodes = self.random.sample(no_cons_list, self.num_prog_bots)
        for a in self.grid.get_cell_list_contents(prog_nodes):
            a.type = AgentType.BOT
            a.state = State.PROGRESSIVE

        # Add edge weights based on political similarity such that the graph looks disconnected at the start
        for u, v in self.G.edges():
            self.G[u][v]['weight'] = EdgeWeight.INVISIBLE

        self.running = True
        self.datacollector.collect(self)
        clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions = identify_clusters(self)
        self.datacollector.add_table_row(
            table_name="CA",
            row={
                "Clusters": clusters,
                "Num_Clusters": number_cluster,
                "Avg_Cluster_Size": avg_cluster_size,
                "Clstr_Agent_Ratio": cluster_ratio,
                "Cross_Interactions": cross_interactions
            }
        )

    def step(self):
        self.agents.shuffle_do("step")

        # collect data
        self.datacollector.collect(self)
        clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions = identify_clusters(self)
        self.datacollector.add_table_row(
            table_name="CA",
            row={
                "Clusters": clusters,
                "Num_Clusters": number_cluster,
                "Avg_Cluster_Size": avg_cluster_size,
                "Clstr_Agent_Ratio": cluster_ratio,
                "Cross_Interactions": cross_interactions
            }
        )
        if number_neutral(self) == 0:
            self.running = False
