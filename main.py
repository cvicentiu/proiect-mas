from graphics import Screen
from logic import Logic, AugumentedLogic
from collisions import Collisions
from world import *
from Tkinter import *
import random

random.seed(42)

class WorldGenerator():

    WORLD_WIDTH  = 400
    WORLD_HEIGHT = 400

    BASE_X = 200
    BASE_Y = 200

    NUM_REACTIVE_AGENTS = 10
    NUM_COGNITIVE_AGENTS = 1

    NUM_FOOD_CLUSTERS          = 10
    NUM_FOOD_UNITS_PER_CLUSTER = 20
    FOOD_CLUSTER_RADIUS        = 10

    NUM_OBSTACLES = 10
    OBSTACLE_RADIUS_MIN = 10
    OBSTACLE_RADIUS_MAX = 20

    @staticmethod
    def generate_world(world_width=WORLD_WIDTH,
                       world_height=WORLD_HEIGHT,
                       base_x=BASE_X,
                       base_y=BASE_Y,
                       num_reactive_agents=NUM_REACTIVE_AGENTS,
                       num_cognitive_agents=NUM_COGNITIVE_AGENTS,
                       num_food_clusters=NUM_FOOD_CLUSTERS,
                       num_food_units_per_cluster=NUM_FOOD_UNITS_PER_CLUSTER,
                       food_cluster_radius=FOOD_CLUSTER_RADIUS,
                       num_obstacles=NUM_OBSTACLES,
                       obstacle_radius_min=OBSTACLE_RADIUS_MIN,
                       obstacle_radius_max=OBSTACLE_RADIUS_MAX,
                       reactive_agent=WorkerAgent):

        world = World(world_width, world_height, base_x, base_y)

        # spawn agents
        for _ in xrange(num_reactive_agents):
            c_x = random.randint(base_x + 20, base_x + 30)
            c_y = random.randint(base_y + 20, base_y + 30)
            agent = reactive_agent(c_x, c_y)
            world.register_resource(agent, World.Agents)

        for _ in xrange(num_cognitive_agents):
            c_x = random.randint(base_x + 20, base_x + 30)
            c_y = random.randint(base_y + 20, base_y + 30)
            agent = CarrierAgent(c_x, c_y)
            world.register_resource(agent, World.Agents)


        # spawn food clusters
        for _ in range(num_food_clusters):
            c_x = random.randint(food_cluster_radius, world_width - food_cluster_radius)
            c_y = random.randint(food_cluster_radius, world_height - food_cluster_radius)

            for _ in range(num_food_units_per_cluster):
                f_x = random.randint(c_x - food_cluster_radius, c_x + food_cluster_radius)
                f_y = random.randint(c_y - food_cluster_radius, c_y + food_cluster_radius)

                # while f_x < 0 or f_y < 0 or f_x >= world_height or f_y >= world_height:
                #     f_x = random.randint(c_x - food_cluster_radius, c_x + food_cluster_radius)
                #     f_y = random.randint(c_y - food_cluster_radius, c_y + food_cluster_radius)

                food_unit = Food(f_x, f_y)
                world.register_resource(food_unit, World.Food)

        # spawn obstacles
        for _ in range(num_obstacles):

            o_x = random.randint(obstacle_radius_max, world_width - obstacle_radius_max)
            o_y = random.randint(obstacle_radius_min, world_height - obstacle_radius_max)
            r_o = random.randint(obstacle_radius_min, obstacle_radius_max)

            obstacle  = Obstacle(o_x, o_y, r_o)
            collision = False

            for key in world.object_matrix:

                resource = world.object_matrix[key]

                if Collisions.check_collision(resource, obstacle):
                    collision = True
                    break

            if not collision:
                world.register_resource(obstacle, World.Obstacles)

        return world

    @staticmethod
    def random_test():
        world = WorldGenerator.generate_world(num_cognitive_agents=0)
        thinker = Logic(world)
        Screen(world, thinker)

    @staticmethod
    def cognitive_test_0():
        world = WorldGenerator.generate_world(num_cognitive_agents=10, num_reactive_agents=0)
        thinker = AugumentedLogic(world)
        Screen(world, thinker)



WorldGenerator.cognitive_test_0()
