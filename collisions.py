import math
class Collisions(object):
  @staticmethod
  def has_collided(pos_a, pos_b, r_a, r_b):
    a_x = pos_a[0]
    a_y = pos_a[1]
    b_x = pos_b[0]
    b_y = pos_b[1]
    dist = math.sqrt((a_x - b_x) ** 2 + (a_y - b_y) ** 2)
    r_dist = r_a + r_b
    if dist < r_dist:
      return True
    return False


  @staticmethod
  def get_collisions_radius(world, pos, radius):
    collisions = {
        'agents' : [],
        'food' : [],
        'obstacles' : [],
        'base' : None,
        'crumbs' : [],
    }

    for agent in world.agents:
      if Collisions.has_collided(pos, agent.pos, radius, agent.radius):
        collisions['agents'].append(agent)

    for food in world.food:
      if Collisions.has_collided(pos, food.pos, radius, food.radius):
        collisions['food'].append(food)

    for obstacle in world.obstacles:
      if Collisions.has_collided(pos, obstacle.pos, radius, obstacle.radius):
        collisions['obstacle'].append(obstacle)

    for crumb in world.crumbs:
      if Collisions.has_collided(pos, crumb.pos, radius, crumb.radius):
        collisions['crumbs'].append(crumb)

    if Collisions.has_collided(pos, world.base.pos, radius, world.base.radius):
      collisions['base'] = world.base

    return collisions

