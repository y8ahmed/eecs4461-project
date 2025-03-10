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
            model,
            agent_type,
            initial_state,
            virus_spread_chance,
            virus_check_frequency,
            recovery_chance,
            gain_resistance_chance,
    ):
        """
        Create a new TikTok agent.

        Args:
        :param agent_type: Human or Bot agent
        :param initial_state: Whether an agent is Progressive, Conservative or Neutral initially
        :param virus_spread_chance: Probability of an infected agent to have positive interactions with others (0-1)
        :param virus_check_frequency: How often agents check whether they are infected (0-1)
        :param recovery_chance: Probability of an infected node to recover (0-1)
        :param gain_resistance_chance: Probability of a node that has recovered to become resistant (0-1)
        """
        super().__init__(model)
        self.state = initial_state
        self.type = agent_type
        self.virus_spread_chance = virus_spread_chance
        self.virus_check_frequency = virus_check_frequency
        self.recovery_chance = recovery_chance
        self.gain_resistance_chance = gain_resistance_chance

    def try_gain_neutrality(self):
        if self.random.random() < self.gain_resistance_chance:
            self.state = State.NEUTRAL

    def try_to_infect_neighbors(self):
        """Try to pass on self state to neighboring human nodes"""
        neighbors_nodes = self.model.grid.get_neighborhood(
            self.pos, include_center=False
        )  # get all nearby agents, self not included

        dissimilar_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if (agent.state is not self.state) and (agent.type is AgentType.HUMAN)
        ]
        for agent in dissimilar_neighbors:
            if self.random.random() < self.virus_spread_chance:
                agent.state = self.state

                print("agent 1 followed agent 2")

    def try_remove_infection(self):
        # Try to change politics from conservative to other
        if self.random.random() < self.recovery_chance:
            # Success
            self.state = State.PROGRESSIVE
            self.try_gain_neutrality()
        else:
            # Failed
            self.state = State.CONSERVATIVE

    def try_check_situation(self):
        if (self.random.random() < self.virus_check_frequency) \
                and (self.state is State.CONSERVATIVE):
            self.try_remove_infection()

    # TODO greatlove was working below to make interactions
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
            if self.random.random() < self.virus_spread_chance and counter <= cap:
                agent.state = self.state
            counter += 1  # keep track of number of interactions so far

    def do_negative(self, cap):
        """Have a negative interaction with another agent"""
        # Try to take away self state from neighboring human nodes. Limited to <cap> number of neighbors
        similar_neighbors = self.get_similar_neighbours()

        counter = 0
        for agent in similar_neighbors:
            if counter <= cap:
                # TODO remove edges from neighbors
                counter += 1
            pass

    def do_bot(self):
        # bot strategy for interactions

        # get neighbours
        # do random positive interactions with <NO_INTERACTIONS_BOT> other agents
        self.do_positive(NO_INTERACTIONS_BOT)

    def do_human(self):
        # human strategy for interactions

        # do random positive/negative interactions with <NO_INTERACTIONS_HUMAN> other agents
        if self.random.random() < P_NEG:
            self.do_negative(NO_INTERACTIONS_HUMAN)
        else:
            self.do_positive(NO_INTERACTIONS_HUMAN)

    def step(self):

        """Conservative node tries to infect others and if human, tries to become Progressive or Neutral"""
        if self.state is State.CONSERVATIVE or self.state is State.PROGRESSIVE:
            self.try_to_infect_neighbors()
        # if agent is human, try to check then change state
        if self.type is AgentType.HUMAN:
            self.try_check_situation()

        # TODO complete this for human and bot-specific interactions
        # if self.type is AgentType.HUMAN:
        #     self.do_human()
        # if self.type is AgentType.BOT:
        #     self.do_bot()
