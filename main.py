from graphics import Screen
from logic import Logic
from world import *
from Tkinter import *
import random

random.seed(42)

NUM_REACTIVE_AGENTS = 30
NUM_FOOD_CLUSTERS = 10
NUM_FOOD_UNITS_PER_CLUSTER = 20
FOOD_CLUSTER_RADIUS = 10

WORLD_WIDTH = 400
WORLD_HEIGHT = 400

BASE_X = 200
BASE_Y = 200

world = World(400, 400, 200, 200)
world.agents.append(WorkerAgent(10, 10))


cluster = []
for _ in range(NUM_FOOD_CLUSTERS):
  c_x = random.randint(FOOD_CLUSTER_RADIUS, WORLD_WIDTH - FOOD_CLUSTER_RADIUS)
  c_y = random.randint(FOOD_CLUSTER_RADIUS, WORLD_HEIGHT - FOOD_CLUSTER_RADIUS)
  for _ in range(NUM_FOOD_UNITS_PER_CLUSTER):
    f_x = random.randint(c_x - FOOD_CLUSTER_RADIUS, c_x + FOOD_CLUSTER_RADIUS)
    f_y = random.randint(c_y - FOOD_CLUSTER_RADIUS, c_y + FOOD_CLUSTER_RADIUS)
    world.food.append(Food(f_x, f_y))

thinker = Logic(world)
Screen(world, thinker)
