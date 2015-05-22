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
        self.all_brains = set()

        self.spawn_agents(world)

    def spawn_agents(self, world):

        print "spawn dummy"

        for agent in self.world.agents:
            if isinstance(agent, WorkerAgent):
                ai = ReactiveBrain(agent, world)
                self.reactive_brains.append(ai)

    def is_over(self):
        return self.world.base.food_stored == self.food_needed

    def think(self):

        self.tick += 1

        for search_agent in self.reactive_brains:
            search_agent.think()

        # outbox = carrier_agent.outbox
        # for msg in outbox:
        #     msg.target.inbox.append(msg.content)
        # carrier_agent.outbox = [] # empty the outbox since all messages are sent

        # Have all agents execute movement.
        for agent in self.world.agents:
          agent.execute_tick()


class AugumentedLogic(Logic):

    def __init__(self, world):
        super(AugumentedLogic, self).__init__(world)

        if len(self.cognitive_brains) == 0:
            print "Augumented logic framework requires at least one intelligent agent."
            exit(1)

        self.maestro = self.cognitive_brains[0]
        self.maestro.setup()

    def spawn_agents(self, world):

        for agent in self.world.agents:

            if isinstance(agent, WorkerAgent):
                ai = ReactiveMonkey(agent, world)
                self.reactive_brains.append(ai)
            else:
                ai = CognitiveMonkey(agent, world,
                                     self.reactive_brains,
                                     self.cognitive_brains)
                self.cognitive_brains.append(ai)

            self.all_brains.add(ai)

    def is_over(self):
        return self.maestro.world.total_resources == 0

    def think(self):

        self.tick += 1

        # pp("Compute master plan!")
        self.maestro.compute_master_plan()

        # pp("Think, bot, think!")
        for bot in self.all_brains:
            bot.think()

        # for agent in self.world.agents:
        #     agent.execute_tick()



