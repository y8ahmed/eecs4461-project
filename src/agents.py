from enum import Enum
from mesa import Agent


# constants for human and bot agent behaviours
NO_INTERACTIONS_BOT = 4  # number of interactions that bot agents will do at each step
NO_INTERACTIONS_HUMAN = 1  # number of interactions that human agents will do at each step
P_POS = 5/7  # probability to do a positive interaction
P_NEG = 2/7  # probability to do a negative interaction


class State(Enum):
    PROGRESSIVE = 0  # SUSCEPTIBLE
    CONSERVATIVE = 1  # INFECTED
    NEUTRAL = 2  # RESISTANT


class AgentType(Enum):
    HUMAN = 0  # self.State can be changed
    BOT = 1  # self.State cannot be changed


class InteractionType(Enum):
    POSITIVE = 0
    NEGATIVE = 1


class POSInteraction(Enum):
    FOLLOW = 0
    LIKE = 1
    SHARE = 2
    COMMENT = 3
    VIEW = 4


class NEGInteraction(Enum):
    UNFOLLOW = 5
    DISLIKE = 6


class TikTokAgent(Agent):
    """Individual TikTokEchoChamber Agent definition and its properties/interaction methods."""

    def __init__(
            self,
            id,
            model,
            agent_type,
            initial_state,
            positive_chance,
            politics_change_chance,
            become_neutral_chance,
    ):
        """
        Create a new TikTok agent.

        Args:
        :param id: Agent's unique Identification number
        :param agent_type: Human or Bot agent
        :param initial_state: Whether an agent is Progressive, Conservative or Neutral initially
        :param positive_chance: Probability of an infected agent to have positive interactions with others (0-1)
        :param politics_change_chance: Probability of an infected node to recover (0-1)
        :param become_neutral_chance: Probability of a node that has recovered to become resistant (0-1)
        """
        super().__init__(model)
        self.id = id
        self.state = initial_state
        self.type = agent_type
        self.positive_chance = positive_chance
        self.politics_change_chance = politics_change_chance
        self.become_neutral_chance = become_neutral_chance

    def get_NO_INTERACTIONS_BOT(self):
        return NO_INTERACTIONS_BOT

    def get_NO_INTERACTIONS_HUM(self):
        return NO_INTERACTIONS_HUMAN

    def try_gain_neutrality(self):
        if self.random.random() < self.become_neutral_chance:
            self.state = State.NEUTRAL

    def get_neighbours(self):
        neighbors_nodes = self.model.grid.get_neighborhood(
            self.pos, include_center=False
        )  # get all nearby agents, self not included
        return neighbors_nodes

    def get_dissimilar_neighbours(self):
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
            if (agent.state is self.state) and (agent.type is AgentType.HUMAN)
        ]
        return similar_neighbors

    def do_positive(self, cap):
        """Have a positive interaction with another agent"""
        # Try to pass on self state to neighboring human nodes. Limited to <cap> number of neighbors
        dissimilar_neighbors = self.get_dissimilar_neighbours()

        counter = 0
        for agent in dissimilar_neighbors:
            if self.random.random() < self.positive_chance and counter <= cap:
                agent.state = self.state

                # change edge colours
                self.model.G[self.id][agent.id]['weight'] = 1

                self.model.interactions += f"+Agent {self.id} followed {agent.id}<br>"
            counter += 1  # keep track of number of interactions so far

    def do_negative(self, cap):
        """Have a negative interaction with another agent"""
        # Try to take away self state from neighboring human nodes. Limited to <cap> number of neighbors
        similar_neighbors = self.get_similar_neighbours()

        counter = 0
        for agent in similar_neighbors:
            if counter <= cap:
                self.try_gain_neutrality()

                # remove edges with neighbor
                self.model.G[self.id][agent.id]['weight'] = 0.1

                self.model.interactions += f"-Agent {self.id} UNfollowed {agent.id}<br>"
                counter += 1
            pass

    def do_bot(self):
        # bot strategy for interactions

        # get neighbours
        # do random positive interactions with <NO_INTERACTIONS_BOT> other human agents
        self.do_positive(NO_INTERACTIONS_BOT)

    def do_human(self):
        # human strategy for interactions

        # do random positive/negative interactions with <NO_INTERACTIONS_HUMAN> other human agents
        if self.random.random() < P_NEG:
            self.do_negative(NO_INTERACTIONS_HUMAN)  # if human, tries to become Progressive or Neutral
        else:
            self.do_positive(NO_INTERACTIONS_HUMAN)

    def step(self):
        """Node does pos/neg interactions based on type"""
        if self.type is AgentType.HUMAN:
            self.do_human()
        if self.type is AgentType.BOT:
            self.do_bot()
