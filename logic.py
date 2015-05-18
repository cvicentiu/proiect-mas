from world import *
from brains import *
import math

class Logic(object):

    def __init__(self, world):

        self.world = world
        self.tick = 0
        self.food_needed = len(self.world.food)
        self.reactive_brains = []
        self.cognitive_brains = []
        self.all_brains = {}

        for agent in self.world.agents:
            if isinstance(agent, WorkerAgent):
                AI = ReactiveBrain(agent, world)
                self.reactive_brains.append(AI)
            else:
                AI = CognitiveBrain(agent, world,
                                    self.reactive_brains,
                                    self.cognitive_brains)
                self.cognitive_brains.append(AI)

    def is_over(self):
        return self.world.base.food_stored == self.food_needed

    def think(self):

        self.tick += 1

        for carrier_agent in self.cognitive_brains:
            carrier_agent.think()

        for search_agent in self.reactive_brains:
            search_agent.think()

        # outbox = carrier_agent.outbox
        # for msg in outbox:
        #     msg.target.inbox.append(msg.content)
        # carrier_agent.outbox = [] # empty the outbox since all messages are sent

        # Have all agents execute movement.
        for agent in self.world.agents:
          agent.execute_tick()

    def mainLoop(self):

        self.tick += 1

        for carrier_agent in self.cognitive_brains:
            carrier_agent.think()

        for search_agent in self.reactive_brains:
            search_agent.think()

        # move agents
        for agent in self.world.agents:
            agent.execute_tick()









