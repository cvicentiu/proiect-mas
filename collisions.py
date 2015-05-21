import math
import collections
import numpy as np

class Collisions(object):

    @staticmethod
    def check_collision(obj_a, obj_b):
        dist = Collisions.distance(obj_a.pos, obj_b.pos)
        r_dist = obj_a.radius + obj_b.radius
        return dist < r_dist

    @staticmethod
    def has_collided(pos_a, pos_b, r_a, r_b):
        dist = Collisions.distance(pos_a, pos_b)
        r_dist = r_a + r_b

        if dist < r_dist:
            return True
        return False


    @staticmethod
    def get_collisions(world, source):

        collisions = {}

        for type in world.object_type_matrix:
            objects = world.object_type_matrix[type]
            collisions[type] = []

            for target in objects:
                if Collisions.check_collision(source, target) and target != source:
                    collisions[type].append(target)

        return collisions


    @staticmethod
    def get_collisions_radius(world, pos, radius):
        collisions = {'agents' : [],
                      'food' : [],
                      'obstacles' : [],
                      'crumbs' : [],
                      'base' : None,
        }

        for agent in world.agents:
          if Collisions.has_collided(pos, agent.pos, radius, agent.radius):
            collisions['agents'].append(agent)

        for food in world.food:
          if Collisions.has_collided(pos, food.pos, radius, food.radius):
            collisions['food'].append(food)

        for obstacle in world.obstacles:
          if Collisions.has_collided(pos, obstacle.pos, radius, obstacle.radius):
            collisions['obstacles'].append(obstacle)

        for crumb in world.crumbs:
          if Collisions.has_collided(pos, crumb.pos, radius, crumb.radius):
            collisions['crumbs'].append(crumb)

        if Collisions.has_collided(pos, world.base.pos, radius, world.base.radius):
            collisions['base'] = world.base

        return collisions

    @staticmethod
    def distance(pos_a, pos_b):
        a_x, a_y, b_x, b_y = pos_a[0], pos_a[1], pos_b[0], pos_b[1]
        dist = math.sqrt((a_x - b_x) ** 2 + (a_y - b_y) ** 2)
        return dist

    @staticmethod
    def set_direction_to_goal(pos, goal):
        forward = np.subtract(pos, goal)
        forward = forward / np.linalg.norm(forward)
        return forward