import numpy as np
from guid import GUID
class WorldObject(object):
  objects = set()
  def __init__(self):
    '''
      Any visible object has a guid attached for eq operations.
    '''
    self.guid = GUID.next_guid()
    WorldObject.objects.add(self)

  def __hash__(self):
    return hash(self.guid)

  def __eq__(self, other):
    return self.guid == other.guid

  def execute_tick(self):
    '''
      Any object should know how to move to the next position, given its
      internal parameters, eg. speed, direction.
    '''
    pass

  def undo_tick(self):
    '''
      Any object should be able to undo an execute_tick call.
    '''
    pass

  def paint(self, world, canvas):
    '''
      Any object should know how to paint itself, given the world and a canvas.
    '''
    print 'self'
    return

class Agent(WorldObject):
  AGENT_SIZE = 10
  def __init__(self, x, y):
    super(Agent, self).__init__()
    self.pos = [x, y]
    self.forward = [1, 1] # agent's forward vector
    self.speed = 0.5
    self.last_pos = self.pos
    self.color = 'green'

  def execute_tick(self):
    self.last_pos = self.pos
    fv = map(lambda x : x * self.speed, self.forward)
    self.pos = map(sum, zip(self.pos, fv))

  def undo_tick(Self):
    self.pos = self.last_pos

  def paint(self, world, canvas):
    norm = np.linalg.norm(self.forward)
    fw_x = self.forward[0] * Agent.AGENT_SIZE / norm
    fw_y = self.forward[1] * Agent.AGENT_SIZE / norm
    canvas.create_line(self.pos[0], self.pos[1],
                       self.pos[0] + fw_x, self.pos[1] + fw_y,
                       width=2,
                       fill=self.color)
    canvas.create_oval(self.pos[0] - Agent.AGENT_SIZE / 2,
                       self.pos[1] - Agent.AGENT_SIZE / 2,
                       self.pos[0] + Agent.AGENT_SIZE / 2,
                       self.pos[1] + Agent.AGENT_SIZE / 2,
                       fill=self.color)

class Food(WorldObject):
  FOOD_SIZE = 5
  def __init__(self, x, y):
    super(Food, self).__init__()
    self.pos = [x, y]
    self.color = '#DD0033'

  def paint(self, world, canvas):
    canvas.create_oval(self.pos[0] - Food.FOOD_SIZE / 2,
                       self.pos[1] - Food.FOOD_SIZE / 2,
                       self.pos[0] + Food.FOOD_SIZE / 2,
                       self.pos[1] + Food.FOOD_SIZE / 2,
                       fill=self.color)


class WorkerAgent(Agent):
  CLOSE_RANGE_SENSOR_RADIUS = 20
  CLOSE_RANGE_SENSOR_COLOR = '#777777'
  def __init__(self, x, y):
    super(WorkerAgent, self).__init__(x, y)
    self.has_food = False
    self.color = 'yellow'

  def paint(self, world, canvas):
    if self.has_food:
      self.color = 'orange'
    else:
      self.color = 'yellow'
    super(WorkerAgent, self).paint(world, canvas)
    canvas.create_oval(self.pos[0] - WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS / 2,
                       self.pos[1] - WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS / 2,
                       self.pos[0] + WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS / 2,
                       self.pos[1] + WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS / 2)

class Base(WorldObject):
  def __init__(self, x, y):
    super(Base, self).__init__()
    self.pos = [x, y]

  def paint(self, world, canvas):
    canvas.create_oval(self.pos[0] - 10, self.pos[1] - 10,
                       self.pos[0] + 10, self.pos[1] + 10,
                       fill='red')

class World(object):
  def __init__(self, width, height, base_x, base_y):
    self.width = width
    self.height = height
    self.agents = []
    self.food = []
    self.obstacles = []
    self.crumbs = []
    self.base = Base(base_x, base_y)
