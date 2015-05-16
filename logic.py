from world import *
from brains import *
import math
class Logic(object):
  def __init__(self, world):
    self.world = world
    self.tick = 0
    self.food_needed = len(self.world.food)
    self.food_gathered = 0
    self.reactive_brains = []
    self.cognitive_brains = []
    self.all_brains = {}
    for agent in self.world.agents:
      brain_list = self.cognitive_brains
      brain = None
      if isinstance(agent, WorkerAgent):
        brain_list = self.reactive_brains
        brain = ReactiveBrain(agent, world)
      else:
        brain = CognitiveBrain(agent, world)
      brain_list.append(brain)
      self.all_brains[agent] = brain

  def is_over(self):
    if self.food_gathered == self.food_needed:
      return True
    return False

  def think(self):
    self.tick += 1
    for brain in self.all_brains.values():
      brain.think()

    for brain in self.all_brains.values():
      outbox = brain.outbox
      for msg in outbox:
        brain_receiver = self.all_brains[msg.receiver]
        brain_receiver.inbox.append(msg)
      brain.outbox = [] # empty the outbox since all messages are sent.

    # Have all agents execute movement.
    for agent in self.world.agents:
      agent.execute_tick()


