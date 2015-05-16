from graphics import Screen
from logic import Logic
from collisions import Collisions
from world import *
from Tkinter import *
import random

random.seed(42)

NUM_REACTIVE_AGENTS = 30

NUM_FOOD_CLUSTERS = 10
NUM_FOOD_UNITS_PER_CLUSTER = 20
FOOD_CLUSTER_RADIUS = 10

NUM_OBSTACLES = 20
OBSTACLE_RADIUS_MIN=10
OBSTACLE_RADIUS_MAX=20

WORLD_WIDTH = 400
WORLD_HEIGHT = 400

BASE_X = 200
BASE_Y = 200

world = World(400, 400, 200, 200)
world.agents.append(WorkerAgent(10, 30))


cluster = []
for _ in range(NUM_FOOD_CLUSTERS):
  c_x = random.randint(FOOD_CLUSTER_RADIUS, WORLD_WIDTH - FOOD_CLUSTER_RADIUS)
  c_y = random.randint(FOOD_CLUSTER_RADIUS, WORLD_HEIGHT - FOOD_CLUSTER_RADIUS)
  for _ in range(NUM_FOOD_UNITS_PER_CLUSTER):
    f_x = random.randint(c_x - FOOD_CLUSTER_RADIUS, c_x + FOOD_CLUSTER_RADIUS)
    f_y = random.randint(c_y - FOOD_CLUSTER_RADIUS, c_y + FOOD_CLUSTER_RADIUS)
    world.food.append(Food(f_x, f_y))

for _ in range(NUM_OBSTACLES):
  o_x = random.randint(OBSTACLE_RADIUS_MAX, WORLD_WIDTH - OBSTACLE_RADIUS_MAX)
  o_y = random.randint(OBSTACLE_RADIUS_MAX, WORLD_HEIGHT - OBSTACLE_RADIUS_MAX)
  r_o = random.randint(OBSTACLE_RADIUS_MIN, OBSTACLE_RADIUS_MAX)
  collision = False
  for food in world.food:
    if Collisions.has_collided(food.pos, [o_x, o_y], Food.FOOD_RADIUS, r_o):
      collision = True
      break
  for obstacle in world.obstacles:
    if Collisions.has_collided(obstacle.pos, [o_x, o_y], obstacle.radius, r_o):
      collision = True
      break
  if Collisions.has_collided(world.base.pos, [o_x, o_y], Base.BASE_RADIUS, r_o):
    collision = True

  if not collision:
    world.obstacles.append(Obstacle(o_x, o_y, r_o))



thinker = Logic(world)
Screen(world, thinker)
