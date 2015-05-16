from collisions import Collisions
from world import *
class Message(object):
  def __init__(self, sender, receiver, msg):
    self.sender = sender
    self.receiver = receiver
    self.msg = msg

class Brain(object):
  def __init__(self, agent, world):
    self.agent = agent
    self.world = world
    self.inbox = []
    self.outbox = []

  def get_sensed(self):
    collisions = Collisions.get_collision_radius(self.world,
                                            self.agent.pos,
                                            self.agent.sensed_radius)
    collisions['agents'] = filter(lambda x : x != self.agent, collisions['agents'])
    return collisions

  def get_collisions(self):
    collisions = Collisions.get_collisions_radius(self.world,
                                                  self.agent.pos,
                                                  self.agent.radius)
    collisions['agents'] = filter(lambda x : x != self.agent, collisions['agents'])
    return collisions

  def think(self):
    pass


class ReactiveBrain(Brain):
  CRUMBS_DROP_INTERVAL = 10
  def __init__(self, agent, world):
    super(ReactiveBrain, self).__init__(agent, world)
    self.last_dropped = 0

  def think(self):
    collisions = self.get_collisions()
    agent = self.agent
    self.last_dropped += 1
    if len(collisions['food']) > 0:
      for food in collisions['food']:
        if agent.food_stored < agent.capacity:
          self.world.food.remove(food)
          agent.food_stored += 1
        else:
          break
    if agent.food_stored > 0:
      if self.last_dropped > ReactiveBrain.CRUMBS_DROP_INTERVAL:
        self.world.crumbs.append(BreadCrumb(agent.pos[0], agent.pos[1], 2))
        self.last_dropped = 0
      agent.forward = np.add(self.world.base.pos, np.negative(agent.pos))
      agent.forward /= np.linalg.norm(agent.forward)



class CognitiveBrain(Brain):
  def __init__(self, agent, world):
    self.agent = agent
    self.world = world
