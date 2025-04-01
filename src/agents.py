import random
from enum import Enum, IntEnum
from mesa import Agent


# constants for human and bot agent behaviours
BASE_REACH_BOT = 2  # initial number of interactions that bot agents will do per step
BASE_REACH_HUMAN = 1  # initial number of interactions that human agents will do at each step
P_POS = 5/7  # probability to do a positive interaction
P_NEG = 2/7  # probability to do a negative interaction
HIT_REQ = 4  # value of hit before an agent's state is changed
HIT_MID = 2  # value of hit after an agent becomes neutral


class EdgeWeight(Enum):
    VISIBLE = 0.5
    DASHED = 0.3
    INVISIBLE = 0.1


class State(IntEnum):
    PROGRESSIVE = 0
    CONSERVATIVE = 1
    NEUTRAL = 2


class AgentType(IntEnum):
    HUMAN = 0  # self.State can be changed
    BOT = 1  # self.State cannot be changed


class POSInteraction(IntEnum):
    """Weight of each positive interaction"""
    VIEW = 1
    LIKE = 2
    COMMENT = 3
    SHARE = 4
    FOLLOW = 5


class NEGInteraction(IntEnum):
    """Weight of each negative interaction"""
    UNFOLLOW = -5
    DISLIKE = -2


# define list of all positive/negative interaction weights
POSInteraction_LIST = list(map(int, POSInteraction))
NEGInteraction_LIST = list(map(int, NEGInteraction))


def choose_pos_interaction():
    # select a random positive interaction to do
    return random.choice(POSInteraction_LIST)


def choose_neg_interaction():
    # select a random negative interaction to do
    return random.choice(NEGInteraction_LIST)


def increase_reach(agent, amt):
    # Increase agent's reach
    if agent.reach < agent.MAX_REACH:
        agent.reach += amt


def decrease_reach(agent):
    if agent.reach > 1:
        agent.reach -= 1


class TikTokAgent(Agent):
    """Individual TikTokEchoChamber Agent definition and its properties/interaction methods."""

    def __init__(
            self,
            id_,
            model,
            agent_type,
            initial_state,
            max_reach,
            positive_chance,
            become_neutral_chance,
    ):
        """
        Create a new TikTok agent.

        Args:
        :param id_: Agent's unique Identification number
        :param agent_type: Human or Bot agent
        :param initial_state: Whether an agent is Progressive, Conservative or Neutral initially
        :param max_reach: The max number of interactions that agents can do per step
        :param positive_chance: Probability of an agent to have positive interactions with others (0-1)
        :param become_neutral_chance: Probability of a node that has recovered to become resistant (0-1)
        """
        super().__init__(model)
        self.id_ = id_
        self.state = initial_state
        self.type = agent_type
        self.MAX_REACH = max_reach
        self.positive_chance = positive_chance
        self.become_neutral_chance = become_neutral_chance

        # keep track of cumulative interaction weights from each state
        self.hit_cons = 0
        self.hit_prog = 0

        # set base number of interactions per step (for bots)
        self.reach = BASE_REACH_BOT if agent_type is AgentType.BOT else BASE_REACH_HUMAN

    def try_gain_neutrality(self):
        if self.random.random() < self.become_neutral_chance:
            self.state = State.NEUTRAL
            self.hit_prog = 0
            self.hit_cons = 0

    def get_neighbours(self):
        neighbors_nodes = self.model.grid.get_neighborhood(
            self.pos, include_center=False
        )  # get all nearby agents, self not included
        return neighbors_nodes

    def get_dissimilar_human_neighbours(self):
        neighbors_nodes = self.get_neighbours()

        dissimilar_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if (agent.state is not self.state) and (agent.type is AgentType.HUMAN)
        ]
        return dissimilar_neighbors

    def get_similar_neighbours(self):
        neighbors_nodes = self.get_neighbours()
        similar_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
        ]
        return similar_neighbors

    def get_similar_human_neighbours(self):
        neighbors_nodes = self.get_neighbours()
        similar_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if (agent.state is self.state) and (agent.type is AgentType.HUMAN)
        ]
        return similar_neighbors

    def get_similar_bot_neighbours(self):
        neighbors_nodes = self.get_neighbours()
        similar_bot_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if (agent.state is self.state) and (agent.type is AgentType.BOT)
        ]
        return similar_bot_neighbors

    def connect(self, agent):
        agent.state = self.state
        agent.hit_cons = 0
        agent.hit_prog = 0

        self.model.G[self.id_][agent.id_]['weight'] = EdgeWeight.VISIBLE
        # print(f"{self.id_} and {agent.id_} connected")

    def disconnect(self, agent):
        agent.hit_cons = 0
        agent.hit_prog = 0

        self.model.G[self.id_][agent.id_]['weight'] = EdgeWeight.INVISIBLE  # remove edges with neighbor
        # print(f"{self.id_} and {agent.id_} disconnected")

    def do_positive(self, cap):
        """Have a positive interaction with dissimilar human agents in neighborhood

            Each interaction's weight is added to the receiving agent's hit_cons or hit_prog,
             depending on the initiating agent's state.
            Once the receiving agent's hit_cons or hit_prog reaches <HIT_REQ>,
             self state can be passed on to the receiving agent
        """
        dissimilar_neighbors = self.get_dissimilar_human_neighbours()

        counter = 0
        for agent in dissimilar_neighbors:
            if self.random.random() < self.positive_chance and counter < cap:
                self.model.G[self.id_][agent.id_]['weight'] = EdgeWeight.DASHED

                # choose what positive interaction to do to neighbor agent
                #   then try to pass on self state to agent if hit satisfied
                if self.state == State.CONSERVATIVE and agent.hit_cons < HIT_REQ + HIT_MID:
                    agent.hit_cons += choose_pos_interaction()
                    if HIT_REQ <= agent.hit_cons <= HIT_REQ + HIT_MID:
                        self.connect(agent)
                elif self.state == State.PROGRESSIVE and agent.hit_cons < HIT_REQ + HIT_MID:
                    agent.hit_prog += choose_pos_interaction()
                    if HIT_REQ <= agent.hit_prog <= HIT_REQ + HIT_MID:
                        self.connect(agent)

                increase_reach(self, 1)  # increase initiating agent's reach
                # self.model.interactions += f"+Agent {self.id_} followed {agent.id_}<br>"
            counter += 1  # keep track of number of interactions so far

    def do_negative(self, cap):
        """Have a negative interaction with another human or bot agent"""
        # Try to reduce relevant self hit based on neighboring nodes. Limited to <cap> number of neighbors.
        similar_neighbors = self.get_similar_neighbours()

        counter = 0
        for agent in similar_neighbors:
            if counter < cap:
                self.model.G[self.id_][agent.id_]['weight'] = EdgeWeight.DASHED

                # choose what negative interaction to do to neighbor agent
                #   then try to become neutral
                if self.state == State.CONSERVATIVE and agent.hit_cons > 0:
                    agent.hit_cons += choose_neg_interaction()
                    if 0 < agent.hit_cons < HIT_MID:
                        self.disconnect(agent)
                elif self.state == State.PROGRESSIVE and agent.hit_cons > 0:
                    agent.hit_prog += choose_neg_interaction()
                    if 0 < agent.hit_prog < HIT_MID:
                        self.disconnect(agent)
                self.try_gain_neutrality()
                decrease_reach(self)  # reduce self reach
                # self.model.interactions += f"-Agent {self.id_} UNfollowed {agent.id_}<br>"
                counter += 1

    def do_bot_to_bot_interaction(self):
        """Do positive interactions with neighboring bots"""
        similar_bot_neighbors = self.get_similar_bot_neighbours()

        cap = 0
        for agent in similar_bot_neighbors:
            if cap < self.reach:
                # Increase reach for initiating bot (up to max of 8)
                increase_reach(self, 3)

                # Update edge weight for visualization
                self.model.G[self.id_][agent.id_]['weight'] = EdgeWeight.VISIBLE
            cap += 1

    def do_bot(self):
        # Bot-to-human interactions strategy
        self.do_positive(self.reach)

        # Bot-to-bot interactions strategy
        self.do_bot_to_bot_interaction()

    def do_human(self):
        # human strategy for interactions

        # do random positive/negative interactions with other human agents
        if self.random.random() < P_NEG:
            self.do_negative(self.reach)
        else:
            self.do_positive(self.reach)

    def step(self):
        """Node does pos/neg interactions based on type"""
        if self.type is AgentType.HUMAN:
            self.do_human()
        if self.type is AgentType.BOT:
            self.do_bot()
