import numpy as np
from graphics import Screen
from guid import GUID

class WorldObject(object):

    objects = set()

    def __init__(self, pos, color, radius):
        '''
        Any visible object has a guid attached for eq operations.
        '''

        self.guid   = GUID.next_guid()
        self.pos    = pos
        self.color  = color
        self.radius = radius

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

    def paint_own_sphere(self, canvas):
        canvas.create_oval(self.pos[0] - self.radius,
                           self.pos[1] - self.radius,
                           self.pos[0] + self.radius,
                           self.pos[1] + self.radius,
                           fill=self.color)

class Agent(WorldObject):

    AGENT_RADIUS = 5
    DIRECTION_COLOR = '#000000'

    def __init__(self, x, y, color="green"):
        super(Agent, self).__init__((x, y), color, Agent.AGENT_RADIUS)

        self.forward     = [1, 1] # agent's forward vector
        self.speed       = 0.5
        self.food_stored = 0

    def execute_tick(self):
        self.last_pos = self.pos
        fv = map(lambda x: x * self.speed, self.forward)
        self.pos = map(sum, zip(self.pos, fv))

    def undo_tick(self):
        self.pos = self.last_pos

    def paint(self, world, canvas):

        norm = np.linalg.norm(self.forward)

        if norm != 0.0:
            fw_x = self.forward[0] * 2 * self.radius / norm
            fw_y = self.forward[1] * 2 * self.radius / norm
            canvas.create_line(self.pos[0], self.pos[1],
                               self.pos[0] + fw_x, self.pos[1] + fw_y,
                               width=2,
                               fill=Agent.DIRECTION_COLOR)

        self.paint_own_sphere(canvas)


class Food(WorldObject):
    FOOD_RADIUS = 2.5
    FOOD_COLOR  = '#DD0033'

    def __init__(self, x, y):
        super(Food, self).__init__((x, y), Food.FOOD_COLOR, Food.FOOD_RADIUS)
        self.quantity = 1
        self.invisible = False

    def paint(self, world, canvas):

        if not self.invisible:
            self.paint_own_sphere(canvas)


class WorkerAgent(Agent):
    CLOSE_RANGE_SENSOR_RADIUS = 15
    CLOSE_RANGE_SENSOR_COLOR = '#777777'

    def __init__(self, x, y):
        super(WorkerAgent, self).__init__(x, y, 'yellow')
        self.sensed_radius = WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS

        self.last_pos    = self.pos
        self.capacity    = 10

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


class CarrierAgent(Agent):

    CLOSE_RANGE_SENSOR_RADIUS = 15
    CLOSE_RANGE_SENSOR_COLOR = '#777777'

    def __init__(self, x, y):
        super(CarrierAgent, self).__init__(x, y, 'orange red')
        self.sensed_radius = WorkerAgent.CLOSE_RANGE_SENSOR_RADIUS
        self.capacity      = 9999

    def paint(self, world, canvas):

        if self.food_stored == 0:
            self.color = 'orange red'
        elif self.food_stored > 0:
            self.color = 'red'

        super(CarrierAgent, self).paint(world, canvas)
        canvas.create_oval(self.pos[0] - self.sensed_radius,
                           self.pos[1] - self.sensed_radius,
                           self.pos[0] + self.sensed_radius,
                           self.pos[1] + self.sensed_radius)

        # from random import randint
        # if randint(0, 40) < 3:
        #     for x in xrange(0, 400):
        #        for y in xrange(0, 400):
        #            if self.map[x][y] != 9999 and \
        #               self.map[x][y] != -1:
        #                 canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="blue")


    def execute_tick(self):
        fv = map(lambda x: x * self.speed, self.forward)
        self.pos = map(sum, zip(self.pos, fv))


class Base(WorldObject):
    BASE_COLOR = '#00CCFF'
    BASE_RADIUS = 20

    def __init__(self, x, y):
        super(Base, self).__init__((x, y), Base.BASE_COLOR, Base.BASE_RADIUS)
        self.food_stored = 0

    def paint(self, world, canvas):
        self.paint_own_sphere(canvas)

class BreadCrumb(WorldObject):

    BREADCRUMB_COLOR_DARK = '#669900'
    BREADCRUMB_COLOR_LIGHT = 'yellow'
    BREADCRUMB_RADIUS = 1.5

    def __init__(self, x, y, count):
        super(BreadCrumb, self).__init__((x, y),
                                         BreadCrumb.BREADCRUMB_COLOR_DARK,
                                         BreadCrumb.BREADCRUMB_RADIUS)
        self.count = count
        self.created = Screen.tick_count

    def paint(self, world, canvas):

        if self.count == 2:
          self.color = BreadCrumb.BREADCRUMB_COLOR_DARK
        else:
          self.color = BreadCrumb.BREADCRUMB_COLOR_LIGHT

        self.paint_own_sphere(canvas)

    def __repr__(self):
        return str(self.pos)

class Obstacle(WorldObject):

    COLOUR = '#555555'

    def __init__(self, x, y, radius):
        super(Obstacle, self).__init__((x, y),
                                       Obstacle.COLOUR,
                                       radius)

    def paint(self, world, canvas):
        self.paint_own_sphere(canvas)

class World(object):

    Food, Obstacles, Crumbs, Agents, Base = range(0, 5)

    def __init__(self, width, height, base_x, base_y):

        self.width  = width
        self.height = height
        self.base   = Base(base_x, base_y)

        # self.world_matrix = np.zeros((height, width))
        # self.world_matrix = self.world_matrix.astype(int)
        self.object_matrix = {(base_x, base_y): self.base}

        self.object_type_matrix = {
            World.Food: [],
            World.Obstacles: [],
            World.Crumbs: [],
            World.Agents: [],
            World.Base: [self.base]
        }

        self.food      = self.object_type_matrix[World.Food]
        self.agents    = self.object_type_matrix[World.Agents]
        self.crumbs    = self.object_type_matrix[World.Crumbs]
        self.obstacles = self.object_type_matrix[World.Obstacles]

        self.tiles_explored = 0
        self.tile_count     = width * height

        self.total_resources = 0

    def check_location_available(self, pos):
        if pos in self.object_matrix:
            return False
        return True

    def register_resource(self, resource, type):

        if type == World.Agents:
            self.object_type_matrix[type].append(resource)
            return

        if type == World.Food:
            self.total_resources += 1

        if type == World.Food and resource.pos in self.object_matrix:
            self.object_matrix[resource.pos].quantity += 1
        else:
            if resource.pos in self.object_matrix:
                print "Duplicate resource at position ", resource.pos
                exit(1)

            self.object_matrix[resource.pos] = resource
            self.object_type_matrix[type].append(resource)


