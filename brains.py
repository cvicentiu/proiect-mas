from collisions import Collisions
from world import *
import random
from graphics import Screen
from pprint import pprint as pp
from collections import deque
from sorted_collection import SortedCollection
from operator import itemgetter
import math

class Message(object):
  def __init__(self, sender, receiver, msg):
    self.sender = sender
    self.receiver = receiver
    self.msg = msg

class Brain(object):
  def __init__(self, agent, world):
    self.agent = agent
    self.world = world

    self.inbox  = deque()
    self.outbox = deque()

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


class EvolvedBrain(Brain):

    ExploreGradient, ExploreSpiral, GatherResource = range(0, 3)

    def __init__(self, agent, world):

        super(EvolvedBrain, self).__init__(agent, world)
        self.targets  = []
        self.plan     = []
        self.last_pos   = agent.pos

    def retrieve_collisions(self):
        collisions = Collisions.get_collisions(self.world, self.agent)
        return collisions

    def set_direction(self, goal):
        self.agent.forward = Collisions.set_direction_to_goal(self.agent.pos, goal)

    @staticmethod
    def setup_spiral(bot, base_pos, rotation=1.0, coils=10.0, chord=1.0, radius=40):

        bot["theta_max"] = float(coils * 2 * math.pi)
        bot["chord"]     = chord
        bot["away_step"] = float(radius / bot["theta_max"]) * 10.0
        bot["theta"]     = float(bot["chord"] / bot["away_step"])
        bot["rotation"]  = rotation
        bot["base_x"]    = base_pos[0]
        bot["base_y"]    = base_pos[1]
        bot["last_theta"] = bot["theta"]

        return bot

    @staticmethod
    def pol2cart(rho, phi):
        x = rho * np.cos(phi)
        y = rho * np.sin(phi)
        return x, y

    @staticmethod
    def spiral_exploration(bot):

        if bot["theta"] > bot["theta_max"]:
            print "theta dead, over"
            return False

        bot["last_theta"] = bot["theta"]

        away   = float(bot["away_step"] * bot["theta"])
        around = bot["rotation"] * float(bot["theta"] + 1.0)

        cx, cy = EvolvedBrain.pol2cart(away, around)
        cx, cy = cx + bot["base_x"], cy + bot["base_y"]

        bot["theta"] += float(bot["chord"] / away)
        return cx, cy

    def apply_command(self, cmd):

        goal_type, goal_data = cmd

        self.last_pos = self.agent.pos

        if goal_type == EvolvedBrain.ExploreGradient:
            self.set_direction(goal_data)

        elif goal_type == EvolvedBrain.ExploreSpiral:
            pos = self.spiral_exploration(goal_data)

            if pos:
                self.agent.pos = pos
                self.agent.forward = [0, 0]


class ReactiveMonkey(EvolvedBrain):

    def __init__(self, agent, world):
        super(ReactiveMonkey, self).__init__(agent, world)

    def think(self):

        if len(self.inbox) != 0:
            self.apply_command(self.inbox.pop())
            return

        # no external command
        # roam randomly ?


class CognitiveMonkey(EvolvedBrain):

    Unvisited, Empty, Obstacle, Food = range(0, 4)

    Directions = zip((0, 0, 1, -1, 1, -1, -1, 1),
                     (1, -1, 0, 0, 1, 1, -1, -1))

    def __init__(self, agent, world, search_agents, carrier_agents):
        super(CognitiveMonkey, self).__init__(agent, world)

        # Exploration map
        self.explore_map = np.zeros((world.height, world.width))
        self.explore_map = self.explore_map.astype(int)

        self.search_agents  = search_agents
        self.carrier_agents = carrier_agents
        self.base = self.world.base

        self.bot_db = {}

        self.free_resources = {}
        self.assumed_resources = {}

    def setup(self):
        self.setup_bots(self.search_agents)
        self.setup_bots(self.carrier_agents)

    def setup_bots(self, bots):

        for bot in bots:
            self.bot_db[bot] = {"targets": deque(), "plan": deque()}
            EvolvedBrain.setup_spiral(self.bot_db[bot], self.base.pos)

    def mark_item_on_map(self, item_pos, item_radius, update_value):

        item_pos = map(int, item_pos)

        queue = deque()
        queue.append(item_pos)

        if self.explore_map[item_pos[0]][item_pos[1]] != CognitiveMonkey.Unvisited and\
           self.explore_map[item_pos[0]][item_pos[1]] != update_value:
            return

        self.explore_map[item_pos[0]][item_pos[1]] = update_value

        while len(queue) > 0:

            px, py = queue.popleft()

            if update_value == CognitiveMonkey.Obstacle:
                pp((px, py))

            for dx, dy in CognitiveMonkey.Directions:

                nx, ny = px + dx, py + dy
                if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
                    continue

                if self.explore_map[nx][ny] == update_value:
                    continue

                if update_value == CognitiveMonkey.Empty:
                    if self.explore_map[nx][ny] != CognitiveMonkey.Unvisited:
                        continue

                # a hypotetical collision between an agent on the neighbouring tile and the current item
                if Collisions.has_collided((nx, ny), item_pos, self.agent.radius, item_radius):
                    self.explore_map[nx][ny] = update_value
                    queue.append((nx, ny))



    def update_map(self, agent, collisions):

        self.mark_item_on_map(agent.pos, agent.radius, CognitiveMonkey.Empty)

        for food_item in collisions[World.Food]:
            pos = food_item.pos
            if pos not in self.assumed_resources:
                self.free_resources[pos] = food_item
                self.explore_map[pos[0]][pos[1]] = CognitiveMonkey.Food

        for obstacle in collisions[World.Obstacles]:
            if self.explore_map[obstacle.pos[0]][obstacle.pos[1]] != CognitiveMonkey.Obstacle:
                self.mark_item_on_map(obstacle.pos, obstacle.radius, CognitiveMonkey.Obstacle)


    def acquire_knowledge(self):

        """
            Acquire knowledge about the environment from sensors
            and serving agents.
        """
        # pp("Acquire Knowledge")

        for bot in self.search_agents:
            collisions = bot.retrieve_collisions()
            self.update_map(bot.agent, collisions)

        for bot in self.carrier_agents:
            collisions = bot.retrieve_collisions()
            self.update_map(bot.agent, collisions)


    def set_exploration_goals(self, bot):

        data = self.bot_db[bot]

        if len(data["targets"]) == 0:
            # check if not a starting position
            exploration_goal = (EvolvedBrain.ExploreSpiral, data["theta"])
            data["targets"].append(exploration_goal)

        goal_type, goal_data = data["targets"][0]

        if goal_type == EvolvedBrain.ExploreSpiral:
            data["plan"] = deque([(EvolvedBrain.ExploreSpiral, data)])

        # print "Exploration goal: ", data["plan"]

    def explore(self):

        for bot in self.search_agents:
            self.set_exploration_goals(bot)

        for bot in self.carrier_agents:
            self.set_exploration_goals(bot)


    def check_out_of_bounds(self, pos):

        px, py = pos
        return px < 0 or py < 0 or \
               px >= self.world.height or \
               py >= self.world.width

    def check_invalid_position(self, pos):
        pos = map(int, pos)
        px, py = pos
        return self.explore_map[px][py] == CognitiveMonkey.Obstacle

    def redirected_wall_bumper(self, bot):

        pos = map(int, bot.agent.pos)

        pp(pos)
        pp(self.explore_map[pos[0]][pos[1]])

        if not (self.check_out_of_bounds(pos) or self.check_invalid_position(pos)):
            return

        # out_of_bounds -> go to a random direction

        # was spiraling -> compute the next "safe" position
        #               -> set it as target

        bot_info = self.bot_db[bot]
        goal_type, goal_data = bot_info["targets"][0]

        if self.check_out_of_bounds(pos):
            # TODO
            # select random target
            return

        if goal_type == EvolvedBrain.ExploreSpiral:

            while not self.check_out_of_bounds(pos) and self.check_invalid_position(pos):
                pos = map(int, self.spiral_exploration(bot_info))

            if self.check_out_of_bounds(pos):
                # TODO
                # select random target
                return

            goal = (CognitiveMonkey.ExploreGradient, pos)
            bot_info["targets"].appendleft(goal)

            pp("Spiral on the other end")
            print self.explore_map[pos[0]][pos[1]]
            pp(bot_info["targets"])
            exit(0)

        bot.agent.pos = bot.last_pos

    def bumped_walls(self):

        for bot in self.search_agents:
            self.redirected_wall_bumper(bot)

        for bot in self.carrier_agents:
            self.redirected_wall_bumper(bot)

    def assign_command(self):

        # pp("assign command")

        for bot in self.bot_db:
            cmd = self.bot_db[bot]["plan"]

            if len(cmd) > 0:
                bot.inbox.append(cmd.popleft())

    def compute_master_plan(self):

        self.acquire_knowledge()
        self.bumped_walls()

        if len(self.free_resources):
            pass

        self.explore()
        self.assign_command()

    def think(self):

        if len(self.inbox) != 0:
            self.apply_command(self.inbox.pop())
            return




# class CognitiveMaster(Brain):
#
#     def __init__(self, agent, world, search_agents, carrier_agents):
#
#         self.agent = agent
#         self.world = world
#
#         self.search_agents  = search_agents
#         self.carrier_agents = carrier_agents
#
#         self.explore_map = np.zeros((world.height, world.width))
#         self.explore_map = self.explore_map.astype(int)
#         self.resources = {}
#         self.targeted_resources = {}
#
#         # set every position on the map as unvisited
#         self.explore_map += 9999
#
#         self.base = self.world.base
#         base_x, base_y = self.base.pos
#         self.explore_map[base_x][base_y] = 0
#         self.mark_item_on_map((base_x, base_y), self.base.radius, 0)
#
#         self.available_bots = []
#         self.tick = 0
#
#         self.targets = []
#         self.agent.targets = self.targets # dirty
#
#         self.plan    = []
#         self.done = False
#         self.agent.map = self.explore_map
#
#         self.agent.theta = None
#         self.agent.rotation     = 1.0
#
#
#
#     def mark_item_on_map(self, item_pos, item_radius, update_value):
#
#         item_pos = map(int, item_pos)
#
#         queue = deque()
#         queue.append(item_pos)
#
#         dx = (0, 0, 1, -1, 1, -1, -1, 1)
#         dy = (1, -1, 0, 0, 1, 1, -1, -1)
#
#         self.explore_map[item_pos[0]][item_pos[1]] = update_value
#
#         while len(queue) > 0:
#             px, py = queue.popleft()
#
#             for idx in xrange(0, 8):
#                 nx = px + dx[idx]
#                 ny = py + dy[idx]
#
#                 if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
#                     continue
#
#                 if self.explore_map[nx][ny] == -1 or \
#                    self.explore_map[nx][ny] == update_value:
#                     continue
#
#                 if Collisions.has_collided((nx, ny), item_pos, self.agent.radius, item_radius):
#                     self.explore_map[nx][ny] = update_value
#                     queue.append((nx, ny))
#
#     def update_map(self, agent_pos, agent_radius, collisions):
#
#         for food_item in collisions[World.Food]:
#             pos = food_item.pos
#             if pos not in self.targeted_resources:
#                 self.resources[food_item.pos] = food_item
#
#         for obstacle in collisions[World.Obstacles]:
#             if self.explore_map[obstacle.pos] != -1:
#                 self.mark_item_on_map(obstacle.pos, obstacle.radius, -1)
#
#         # self.mark_item_on_map(agent_pos, agent_radius, self.tick)
#
#     def acquire_knowledge(self):
#
#         """
#             Acquire knowledge about the environment from sensors
#             and serving agents.
#         """
#
#         self.available_bots = []
#
#         for bot in self.search_agents:
#             agent_collisions, available = bot.enquire_status()
#             self.update_map(bot.agent.pos, bot.agent.radius, agent_collisions)
#
#             if available:
#                 self.available_bots.append(bot.agent)
#
#         collisions = Collisions.get_collisions(self.world, self.agent)
#         self.update_map(self.agent.pos, self.agent.sensed_radius, collisions)
#
#         # cognitive agents may do some exploring on their own
#         if len(self.targets) == 0:
#             self.available_bots.append(self.agent)
#
#     def explore_for_bot(self, bot, bots):
#
#         pos = map(int, bot.pos)
#         visited = np.zeros((self.world.height, self.world.width), dtype=bool)
#
#         dx = (0, 0, 1, -1, 1, -1, -1, 1)
#         dy = (1, -1, 0, 0, 1, 1, -1, -1)
#
#         queue = deque()
#         queue.append((pos, 0))
#
#         visited[pos[0]][pos[1]] = True
#
#         result = []
#
#         while len(queue) > 0:
#
#             (px, py), steps = queue.popleft()
#
#             # print (px, py), self.explore_map[px][py]
#
#             if self.explore_map[px][py] == 9999:
#
#                 # Heuristic: score = steps from bot + direct distance from every other bot
#                 score = steps
#                 for other in bots:
#                     if other != bot:
#                         score += Collisions.distance((px, py), other.pos)
#
#                 result.append((score, (px, py)))
#                 continue
#
#             for idx in xrange(0, 8):
#                 nx = px + dx[idx]
#                 ny = py + dy[idx]
#
#                 if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
#                     continue
#
#                 if visited[nx][ny]:
#                     continue
#
#                 if self.explore_map[nx][ny] == -1:
#                     continue
#
#                 visited[nx][ny] = True
#                 queue.append(((nx, ny), steps + 1))
#
#         return result
#
#     def setup_exploration_goals(self):
#
#         targets = []
#         target_set = set()
#         bot_set = set()
#
#         for bot in self.available_bots:
#             bot_targets = self.explore_for_bot(bot, self.available_bots)
#             targets += [(t[0], t[1], bot) for t in bot_targets]
#
#         targets.sort(key=itemgetter(0))
#
#         from pprint import pprint
#         pprint(targets[:20])
#
#         for target in targets:
#             (score, pos, bot) = target
#
#             if pos not in target_set and\
#                bot not in bot_set:
#
#                 target_set.add(pos)
#                 bot_set.add(bot)
#                 bot.targets.append(pos)
#                 print "targets ", bot.targets
#
#         exit(0)
#
#     def seek_path(self, orig, goal):
#
#         queue = SortedCollection(key=itemgetter(0))
#
#         # print "Seek_path ", orig, goal
#         # print self.explore_map[goal[0]][goal[1]]
#
#         pred = {}
#         pred[(orig[0], orig[1])] = None
#
#         queue.insert((0, orig, 0))
#
#         dx = (0, 0, 1, -1, 1, -1, -1, 1)
#         dy = (1, -1, 0, 0, 1, 1, -1, -1)
#
#         while len(queue) > 0:
#
#             score, (px, py), steps = queue[0]
#             queue.remove_first()
#
#             if (px, py) == goal:
#
#                 # follow trail greedily
#                 plan = [goal]
#                 while pred[goal]:
#                     plan.append(pred[goal])
#                     goal = pred[goal]
#
#                 return plan[::-1][1:]
#
#             for idx in xrange(0, 8):
#                 nx = px + dx[idx]
#                 ny = py + dy[idx]
#
#                 if (nx, ny) in pred:
#                     continue
#
#                 if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
#                     continue
#
#                 if self.explore_map[nx][ny] == -1:
#                     continue
#
#                 pred[(nx, ny)] = (px, py)
#
#                 nscore = steps + 1 + Collisions.distance((nx, ny), goal)
#                 queue.insert((nscore, (nx, ny), steps))
#
#         return []
#
#     def check_blocked(self, pos):
#         return self.explore_map[pos[0]][pos[1]] == -1
#
#     def route_bot_to_target(self, bot):
#
#         if len(bot.targets) > 0:
#             pos = map(int, bot.pos)
#
#             if len(bot.plan) == 0 or self.check_blocked(bot.plan[0]):
#                 self.plan = self.seek_path(pos, bot.targets[0])
#
#             if len(bot.plan) > 0:
#                 target = bot.plan[0]
#                 print "Planned target ", target
#                 bot.agent.forward = Collisions.set_direction_to_goal(target, pos)
#
#     def route_agents(self):
#
#         self.route_bot_to_target(self)
#
#         for bot in self.search_agents:
#             self.route_bot_to_target(bot)
#
#         for bot in self.carrier_agents:
#             self.route_bot_to_target(bot)
#
#
#     # def cart2pol(x, y):
#     #     rho = np.sqrt(x ** 2 + y ** 2)
#     #     phi = np.arctan2(y, x)
#     #     return rho, phi
#
#
#     def default_routing(self, agent):
#
#         pp = agent.prev_pos
#         pt = agent.prev_theta
#
#         agent.prev_pos   = agent.pos
#         agent.prev_theta = agent.theta
#
#         collisions = Collisions.get_collisions(self.world, agent)
#         if len(collisions[World.Obstacles]) > 0:
#             print "Bad foot", agent.rotation
#         else:
#             print "Ok!", agent.pos, agent.rotation
#
#         step = self.spiral_exploration(agent)
#         collisions = Collisions.get_collisions(self.world, agent)
#
#         if len(collisions[World.Obstacles]) > 0:
#             print "Blocked!"
#
#             while len(collisions[World.Obstacles]) > 0:
#
#                 step = self.spiral_exploration(agent)
#                 agent.theta += step
#
#                 # agent.rotation *= -1.0
#                 # agent.pos   = pp
#                 # agent.theta += 1.0
#
#                 # print "Back, back ", agent.pos, agent.rotation
#
#                 # exit(0)
#                 # print agent.pos, agent.rotation
#
#                 collisions = Collisions.get_collisions(self.world, agent)
#                 # if len(collisions[World.Obstacles]) > 0:
#                 #     exit(0)
#
#             agent.targets = [map(int, agent.pos)]
#             agent.pos = agent.prev_pos
#
#             print agent.targets
#
#         else:
#             agent.theta += step
#
#
#
#
#
#
#
#     def think(self):
#
#         cpos = map(int, self.agent.pos)
#         self.acquire_knowledge()
#
#         # Instinct : Exploration
#
#         # if self.targets
#         # self.default_routing(self.agent)
#
#         # self.route_bot_to_target(self.agent)
#         # self.available_bots = []
#         # self.resources      = {}
#         # # check if target has been reached
#         #
#         # # print "Pos", cpos, self.explore_map[cpos[0]][cpos[1]]
#         #
#         #
#         # while len(self.targets) > 0 and self.check_blocked(self.targets[0]):
#         #     del self.targets[0]
#         #     self.plan = []
#         #
#         # self.setup_exploration_goals()

