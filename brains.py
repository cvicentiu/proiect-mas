from collisions import Collisions
from world import *
import random
from graphics import Screen
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
    collisions = Collisions.get_collisions_radius(self.world,
                                                 self.agent.pos,
                                                 self.agent.sensed_radius)
    collisions['agents'] = filter(lambda x: x != self.agent, collisions['agents'])
    return collisions

  def get_collisions(self):
    collisions = Collisions.get_collisions_radius(self.world,
                                                  self.agent.pos,
                                                  self.agent.radius)
    collisions['agents'] = filter(lambda x: x != self.agent, collisions['agents'])
    return collisions

  def think(self):
    pass


class ReactiveBrain(Brain):
  CRUMBS_PICK_UP_INTERVAL = 25
  CRUMBS_DROP_INTERVAL = 20
  RANDOM_CHANGE_INTERVAL = 500
  def __init__(self, agent, world):
    super(ReactiveBrain, self).__init__(agent, world)
    self.last_dropped = 0
    self.last_changed = 2 ** 32
    self.last_picked = {}
    self.goal = [random.randint(0, world.width), random.randint(0, world.height)]
    RCI = ReactiveBrain.RANDOM_CHANGE_INTERVAL
    self.change_interval = RCI + random.randint(-RCI / 2, RCI / 2)

  def set_new_goal(self):
    RCI = ReactiveBrain.RANDOM_CHANGE_INTERVAL
    self.change_interval = RCI + random.randint(-RCI / 2, RCI / 2)
    g_x = random.randint(0, self.world.width)
    g_y = random.randint(0, self.world.height)
    self.goal = [g_x, g_y]
    self.last_changed = 0

  def set_direction_to_goal(self):
    agent = self.agent
    agent.forward = np.add(self.goal, np.negative(agent.pos))
    agent.forward = agent.forward / np.linalg.norm(agent.forward)

  def set_direction_to(self, dest):
    agent = self.agent
    new_f = np.add(dest, np.negative(agent.pos))
    norm = np.linalg.norm(new_f)
    if (norm > 0):
      agent.forward = new_f / norm


  def drop_crumbs(self):
    agent = self.agent
    if agent.food_stored > 0:
      if self.last_dropped > ReactiveBrain.CRUMBS_DROP_INTERVAL:
        self.world.crumbs.add(BreadCrumb(agent.pos[0], agent.pos[1], 2))
        self.last_dropped = 0


  def pick_up_crumbs(self, collisions):
    for crumb in collisions['crumbs']:
      if crumb not in self.last_picked:
        self.last_picked[crumb] = Screen.tick_count
        continue

      tick = self.last_picked[crumb]
      if tick + ReactiveBrain.CRUMBS_PICK_UP_INTERVAL < Screen.tick_count:
        crumb.count -= 1
        self.last_picked[crumb] = Screen.tick_count
        if crumb.count <= 0:
          self.world.crumbs.remove(crumb)


  def pick_up_food(self, collisions):
    agent = self.agent
    if len(collisions['food']) > 0:

      for food in collisions['food']:

        max_quantity = min(food.quantity, agent.capacity - agent.food_stored)
        agent.food_stored += max_quantity
        if agent.food_stored == agent.capacity:
            return True

    return False


  def think(self):
    collisions = self.get_collisions()
    sensed = self.get_sensed()
    agent = self.agent

    self.last_dropped += 1
    self.last_changed += 1

    self.pick_up_food(collisions)
    if agent.food_stored == 0:
      self.pick_up_crumbs(collisions)
    if agent.food_stored > 0:
      self.goal = self.world.base.pos
      self.drop_crumbs()
    else:
      # Set a random goal, if the food stored is 0 or we've reached our goal
      if self.last_changed > self.change_interval or \
         abs(np.sum(np.add(agent.pos, np.negative(self.goal)))) < 2:
        self.set_new_goal()

    self.set_direction_to_goal()

    # Hooks that change the general direction to a local goal
    if agent.food_stored == 0:
      # Go towards the highest crumb.
      if len(sensed['crumbs']) > 0:
        greatest_crumb = sensed['crumbs'][0]
        for c in sensed['crumbs']:
          if c.count > greatest_crumb.count:
            greatest_crumb = c
            continue
          if c.count == greatest_crumb.count:
            if c.created < greatest_crumb.created:
              greatest_crumb = c
        self.set_direction_to(greatest_crumb.pos)

    # Hooks that change the general direction to a local goal
    if agent.food_stored < agent.capacity:
      # We change direction straight to food, if we sense it.
      if len(sensed['food']) > 0:
        self.set_direction_to(sensed['food'][0].pos)


    if collisions['base'] != None:
      self.set_direction_to(self.world.base.pos)
      agent.forward = np.negative(agent.forward)
      self.world.base.food_stored += agent.food_stored
      agent.food_stored = 0
      # Once the food is deposited, create a new goal and clear the last_picked
      # dictionary.
      self.set_new_goal()
      to_pop = []
      for k in self.last_picked:
        if k not in self.world.crumbs:
          to_pop.append(k)
      for k in to_pop:
        self.last_picked.pop(k)

    # Collision avoidance comes last.
    if len(collisions['obstacles']) > 0:
      self.set_direction_to(collisions['obstacles'][0].pos)
      agent.forward = np.negative(agent.forward)



class CognitiveBrain(Brain):

    def __init__(self, agent, world, search_agents, carrier_agents):

        self.agent = agent
        self.world = world

        self.search_agents  = search_agents
        self.carrier_agents = carrier_agents


