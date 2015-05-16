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
  AGENT_RADIUS = 5
  def __init__(self, x, y):
    super(Agent, self).__init__()
    self.pos = [x, y]
    self.forward = [1, 1] # agent's forward vector
    self.speed = 0.5
    self.last_pos = self.pos
    self.color = 'green'
    self.radius = Agent.AGENT_RADIUS
    self.food_stored = 0
    self.capacity = 10

  def execute_tick(self):
    self.last_pos = self.pos
    fv = map(lambda x : x * self.speed, self.forward)
    self.pos = map(sum, zip(self.pos, fv))

  def undo_tick(Self):
    self.pos = self.last_pos

  def paint(self, world, canvas):
    norm = np.linalg.norm(self.forward)
    fw_x = self.forward[0] * 2 * self.radius / norm
    fw_y = self.forward[1] * 2 * self.radius / norm
    canvas.create_line(self.pos[0], self.pos[1],
                       self.pos[0] + fw_x, self.pos[1] + fw_y,
                       width=2,
                       fill='#000000')
    canvas.create_oval(self.pos[0] - self.radius,
                       self.pos[1] - self.radius,
                       self.pos[0] + self.radius,
                       self.pos[1] + self.radius,
                       fill=self.color)

class Food(WorldObject):
  FOOD_RADIUS = 2.5
  def __init__(self, x, y):
    super(Food, self).__init__()
    self.pos = [x, y]
    self.color = '#DD0033'
    self.radius = Food.FOOD_RADIUS

  def paint(self, world, canvas):
    canvas.create_oval(self.pos[0] - self.radius,
                       self.pos[1] - self.radius,
                       self.pos[0] + self.radius,
                       self.pos[1] + self.radius,
                       fill=self.color)


class WorkerAgent(Agent):
  CLOSE_RANGE_SENSOR_RADIUS = 10
  CLOSE_RANGE_SENSOR_COLOR = '#777777'
  def __init__(self, x, y):
    super(WorkerAgent, self).__init__(x, y)
    self.color = 'yellow'
    self.sensed_radius = WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS

  def paint(self, world, canvas):
    if self.food_stored == 0:
      self.color = 'green'
    elif self.food_stored < self.capacity:
      self.color = 'yellow'
    else: #Full capacity
      self.color = 'orange'
    super(WorkerAgent, self).paint(world, canvas)
    canvas.create_oval(self.pos[0] - self.sensed_radius,
                       self.pos[1] - self.sensed_radius,
                       self.pos[0] + self.sensed_radius,
                       self.pos[1] + self.sensed_radius)

class Base(WorldObject):
  BASE_COLOR = '#00CCFF'
  BASE_RADIUS = 20
  def __init__(self, x, y):
    super(Base, self).__init__()
    self.pos = [x, y]
    self.radius = Base.BASE_RADIUS

  def paint(self, world, canvas):
    canvas.create_oval(self.pos[0] - self.radius, self.pos[1] - self.radius,
                       self.pos[0] + self.radius, self.pos[1] + self.radius,
                       fill=Base.BASE_COLOR)

class BreadCrumb(WorldObject):
  BREADCRUMB_COLOR = '#669900'
  BREADCRUMB_RADIUS = 1.5
  def __init__(self, x, y, count):
    super(BreadCrumb, self).__init__()
    self.pos = [x, y]
    self.count = count
    self.radius = BreadCrumb.BREADCRUMB_RADIUS

  def paint(self, world, canvas):
    canvas.create_oval(self.pos[0] - self.radius,
                       self.pos[1] - self.radius,
                       self.pos[0] + self.radius,
                       self.pos[1] + self.radius,
                       fill=BreadCrumb.BREADCRUMB_COLOR)

class Obstacle(WorldObject):
  def __init__(self, x, y, radius):
    super(Obstacle, self).__init__()
    self.pos = [x, y]
    self.radius = radius

  def paint(self, world, canvas):
    canvas.create_oval(self.pos[0] - self.radius,
                       self.pos[1] - self.radius,
                       self.pos[0] + self.radius,
                       self.pos[1] + self.radius,
                       fill='#555555')




class World(object):
  def __init__(self, width, height, base_x, base_y):
    self.width = width
    self.height = height
    self.agents = []
    self.food = []
    self.obstacles = []
    self.crumbs = []
    self.base = Base(base_x, base_y)
