import math

import networkx as nx
import mesa
from mesa import Model
from src.agents import State, TikTokAgent, AgentType, EdgeWeight


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


def num_cons_clusters(model):
    # get the average reach of all conservative bots
    reach = 0
    count = 0

    for agent in model.grid.agents:
        if agent.type == AgentType.BOT and agent.state == State.CONSERVATIVE:
            reach += agent.reach
            count += 1
    return reach/count


def avg_cons_bot_reach(model):
    # get the average reach of all conservative bots
    reach = 0
    count = 0
    reaches = []

    for agent in model.grid.agents:
        if agent.type == AgentType.BOT and agent.state == State.CONSERVATIVE:
            reaches.append(agent.reach)
            reach += agent.reach
            count += 1
    return reach/count


def avg_prog_bot_reach(model):
    # get the average reach of all progressive bots
    reach = 0
    count = 0
    for agent in model.grid.agents:
        if agent.type == AgentType.BOT and agent.state == State.PROGRESSIVE:
            reach += agent.reach
            count += 1
    return reach/count


def get_unique_edge_list(edges):
    unique_edge_list = []
    for u, v in edges:
        if (u, v) not in unique_edge_list and (v, u) not in unique_edge_list:
            unique_edge_list.append((u, v))

    return unique_edge_list


def identify_clusters(model) -> tuple[list, int, float, float, int, int, int, int, int]:
    """Group nodes by similarity and connectedness. Returns a list of:
        [0]: list of cluster ids for each node. 0-indexed.
        [1]: number of clusters
        [2]: avg_cluster_size
        [3]: cluster_ratio
        [4]: cross_interactions
        [5]: average size of cons. cluster
        [6]: average size of prog. cluster
        [7]: number of conservative clusters
        [8]: number of progressive clusters
    """

    # Cluster Definition: a group of nodes:
    # - with similar leaning
    # - that are connected
    # ie: there exists a path from each node to every other node without going through a dissimilar node

    # the cluster id for each node is initialized to the node's id
    clusters = [node for node in model.G.nodes()]

    '''if an edge is not invisible either way then they are connected'''
    all_visible_edges = [(u, v) for u, v in model.G.edges()
                         if model.G[u][v]['weight'] != EdgeWeight.INVISIBLE or
                         model.G[v][u]['weight'] != EdgeWeight.INVISIBLE]
    visible_edges = get_unique_edge_list(all_visible_edges)  # get unique pairs since edges may be dupes eg.(1,3), (3,1)

    # try to find connected similar nodes and update their cluster id. note that edges are ordered.
    #   do it twice to ensure earlier nodes are updated
    for _ in [1, 2]:
        cross_interactions = 0
        for u, v in visible_edges:
            agent_u = model.grid.get_cell_list_contents([u])[0]
            agent_v = model.grid.get_cell_list_contents([v])[0]
            min_id = min(clusters[u], clusters[v])

            # check similarity of agents
            if agent_u.state == agent_v.state:
                # make cluster ids the same
                clusters[u] = min_id
                clusters[v] = min_id
            else:
                cross_interactions += 1  # update cross-cluster interactions

    # prep return values
    unique_clusters = set(clusters)
    number_cluster = len(unique_clusters)
    cluster_ratio = number_cluster / model.num_nodes if model.num_nodes > 0 else 0

    sum_size = sum(clusters.count(c) for c in unique_clusters)
    avg_cluster_size = round(sum_size / number_cluster)

    # get each cluster and the nodes in it
    cluster_dict = {}
    for node, cluster_id in enumerate(clusters):
        if cluster_id not in cluster_dict:
            cluster_dict[cluster_id] = []
        cluster_dict[cluster_id].append(node)

    # find avg cluster size for each leaning
    cons_clstr_size = 0
    cons_count = 0
    prog_clstr_size = 0
    prog_count = 0
    for cluster_id, node_list in cluster_dict.items():
        if model.grid.get_cell_list_contents([node_list[0]])[0].state == State.CONSERVATIVE:
            cons_clstr_size += len(node_list)
            cons_count += 1
        if model.grid.get_cell_list_contents([node_list[0]])[0].state == State.PROGRESSIVE:
            prog_clstr_size += len(node_list)
            prog_count += 1

    cons_clstr_avg_size = cons_clstr_size // cons_count
    prog_clstr_avg_size = prog_clstr_size // prog_count

    # print(f"cons_clstr_size {cons_clstr_size} ")
    # print(f"prog_clstr_size {prog_clstr_size} ")
    # print(f"cons_clstr_avg_size {cons_clstr_avg_size} ")
    # print(f"prog_clstr_avg_size {prog_clstr_avg_size} ")

    return clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions, \
        cons_clstr_avg_size, prog_clstr_avg_size, cons_count, prog_count


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
            avg_node_degree=5,
            num_cons_bots=2,
            num_prog_bots=3,
            positive_chance=0.8,
            become_neutral_chance=0.2,
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
                "Neutral": number_neutral,
                "Avg_Cons_Bot_Reach": avg_cons_bot_reach,
                "Avg_Prog_Bot_Reach": avg_prog_bot_reach
            },
            agent_reporters={
                "Reach": "reach"
            },
            tables={
                "CA": ["Clusters", "Num_Clusters", "Num_Cons_Clusters", "Num_Prog_Clusters", "Avg_Cluster_Size",
                       "Clstr_Agent_Ratio", "Cross_Interactions",
                       "Cons_Avg_Cluster_Size", "Prog_Avg_Cluster_Size"]
            }
        )

        # Initialize the grid

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
                id_=idCounter,
                model=self,
                agent_type=AgentType.HUMAN,
                initial_state=State.NEUTRAL,
                max_reach=avg_node_degree,
                positive_chance=self.positive_chance,
                become_neutral_chance=self.become_neutral_chance,
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
        clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions, \
            cons_clstr_avg_size, prog_clstr_avg_size, cons_count, prog_count = identify_clusters(self)
        self.datacollector.add_table_row(
            table_name="CA",
            row={
                "Clusters": clusters,
                "Num_Clusters": number_cluster,
                "Num_Cons_Clusters": cons_count,
                "Num_Prog_Clusters": prog_count,
                "Avg_Cluster_Size": avg_cluster_size,
                "Clstr_Agent_Ratio": cluster_ratio,
                "Cross_Interactions": cross_interactions,
                "Cons_Avg_Cluster_Size": cons_clstr_avg_size,
                "Prog_Avg_Cluster_Size": prog_clstr_avg_size,
            }
        )
        self.datacollector.collect(self)

    def step(self):
        self.agents.shuffle_do("step")

        # collect data
        clusters, number_cluster, avg_cluster_size, cluster_ratio, cross_interactions, \
            cons_clstr_avg_size, prog_clstr_avg_size, cons_count, prog_count = identify_clusters(self)
        self.datacollector.add_table_row(
            table_name="CA",
            row={
                "Clusters": clusters,
                "Num_Clusters": number_cluster,
                "Num_Cons_Clusters": cons_count,
                "Num_Prog_Clusters": prog_count,
                "Avg_Cluster_Size": avg_cluster_size,
                "Clstr_Agent_Ratio": cluster_ratio,
                "Cross_Interactions": cross_interactions,
                "Cons_Avg_Cluster_Size": cons_clstr_avg_size,
                "Prog_Avg_Cluster_Size": prog_clstr_avg_size
            }
        )
        self.datacollector.collect(self)
        # print(clusters)
        # print(self.datacollector.get_table_dataframe("CA"))

        if number_neutral(self) == 0:
            self.running = False
            self.datacollector.get_table_dataframe("CA").to_csv("CA.csv")
            self.datacollector.get_model_vars_dataframe().to_csv("model.csv")
