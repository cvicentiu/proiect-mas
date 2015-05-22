from collisions import Collisions
from world import *
import random
from graphics import Screen
from pprint import pprint as pp
from collections import deque
from sorted_collection import SortedCollection
from operator import itemgetter
import math
import itertools

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

    ExploreGradient, ExploreSpiral, GatherResource, ReturnToBase, MeetUp = range(0, 5)

    def __init__(self, agent, world):

        super(EvolvedBrain, self).__init__(agent, world)
        self.targets  = []
        self.plan     = []
        self.last_pos   = agent.pos

        self.base = self.world.base
        self.agent.pos = self.base.pos

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
            self.agent.pos = goal_data
            # self.set_direction(goal_data)

        elif goal_type == EvolvedBrain.ExploreSpiral:
            pos = self.spiral_exploration(goal_data)

            if pos:
                self.agent.pos = pos
                self.agent.forward = [0, 0]

        elif goal_type == EvolvedBrain.GatherResource:

            amount = goal_data["amount"]
            self.agent.food_stored += amount
            # print "Food munched ", amount

        elif goal_type == EvolvedBrain.ReturnToBase:

            amount = goal_data["amount"]
            target = goal_data["target"]

            # print "Dumped ", self.agent.food_stored

            target.food_stored += amount
            self.world.total_resources -= amount
            self.agent.food_stored = 0
            # print "Dumped to collector", amount

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

    Unvisited, Empty, Obstacle, Food, Misc1, Misc2 = range(0, 6)

    Directions = zip((0, 0, 1, -1, 1, -1, -1, 1),
                     (1, -1, 0, 0, 1, 1, -1, -1))

    InfiniteDistance = 9999

    def __init__(self, agent, world, search_agents, carrier_agents):
        super(CognitiveMonkey, self).__init__(agent, world)

        # Exploration map
        self.explore_map = np.zeros((world.height, world.width))
        self.explore_map = self.explore_map.astype(int)

        self.search_agents  = search_agents
        self.carrier_agents = carrier_agents

        self.bot_db = {}

        self.free_resources = {}
        self.assumed_resources = {}

    def setup(self):
        self.setup_bots(self.search_agents)
        self.setup_bots(self.carrier_agents)
        self.setup_coll()

    def setup_bots(self, bots):

        rotation   = 1.0
        radius     = 45
        radius_inc = 10

        for bot in bots:
            self.bot_db[bot] = {"targets": deque(), "plan": deque()}
            EvolvedBrain.setup_spiral(self.bot_db[bot], self.base.pos, rotation=rotation, radius=radius)

            self.bot_db[bot]["food_stored"] = 0
            self.bot_db[bot]["capacity"]    = bot.agent.capacity

            rotation *= -1.0
            if rotation == 1.0:
                radius += radius_inc
                if radius == 120 or radius == 30:
                    radius_inc = -radius_inc

    def setup_coll(self):

        for obstacle in self.world.obstacles:
            self.mark_item_on_map(obstacle.pos, obstacle.radius, CognitiveMonkey.Obstacle)

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

    def compute_path(self, orig, goal):

        orig = map(int, orig)

        goal = tuple(goal)
        queue = SortedCollection(key=itemgetter(0))
        queue.insert((0, orig, 0))

        pred = {}
        pred[tuple(orig)] = None

        while len(queue) > 0:

            score, (px, py), steps = queue[0]
            queue.remove_first()

            if (px, py) == goal:

                # follow trail back greedily
                pos  = (px, py)
                plan = [pos]

                while pred[pos]:
                    plan.append(pred[pos])
                    pos = pred[pos]

                return plan[::-1][1:]

            for dx, dy in CognitiveMonkey.Directions:

                nx, ny = px + dx, py + dy

                if (nx, ny) in pred:
                    continue

                if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
                    continue

                if self.explore_map[nx][ny] == CognitiveMonkey.Obstacle:
                    continue

                pred[(nx, ny)] = (px, py)

                nscore = steps + 1 + Collisions.distance((nx, ny), goal)
                queue.insert((nscore, (nx, ny), steps + 1))

        return []

    def bot_finds_love(self, bot1, bot2):

        """
            Seek a path to join the two bots.
            (Usage: search bot sending resources to a carrier bot)
            :param bot1:
            :param bot2:
            :return:
        """

        aux_map = np.array(self.explore_map, copy=True)

        pos1 = tuple(map(int, bot1.agent.pos))
        pos2 = tuple(map(int, bot2.agent.pos))

        pred = {}
        pred[pos1] = None
        pred[pos2] = None

        if pos1 == pos2:
            return pos1, pos2

        queue_1 = deque([pos1])
        queue_2 = deque([pos2])

        # print pos1, pos2

        aux_map[pos1[0]][pos1[1]] = CognitiveMonkey.Misc1
        aux_map[pos2[0]][pos2[1]] = CognitiveMonkey.Misc2

        step = 1

        while len(queue_1) > 0 and len(queue_2) > 0:

            if step:
                if len(queue_1) == 0:
                    continue

                (px, py)     = queue_1.popleft()
                colour       = CognitiveMonkey.Misc1
                other_colour = CognitiveMonkey.Misc2
            else:
                if len(queue_2) == 0:
                    continue

                (px, py)     = queue_2.popleft()
                colour       = CognitiveMonkey.Misc2
                other_colour = CognitiveMonkey.Misc1

            for dx, dy in CognitiveMonkey.Directions:
                nx, ny = px + dx, py + dy

                if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
                    continue

                if aux_map[nx][ny] == CognitiveMonkey.Obstacle or \
                   aux_map[nx][ny] == colour:
                    continue

                if aux_map[nx][ny] == other_colour:

                    # pos = (px, py)
                    # path_current = [pos]
                    # while pred[pos]:
                    #     path_current.append(pred[pos])
                    #     pos = pred[pos]
                    # path_current = path_current[::-1][1:]
                    #
                    # pos = (nx, ny)
                    # path_other = [pos]
                    # while pred[pos]:
                    #     path_other.append(pred[pos])
                    #     pos = pred[pos]
                    # path_other = path_other[::-1][1:]

                    if step:
                        return (px, py), (nx, ny)
                        # return path_current, path_other
                    else:
                        return (nx, ny), (px, py)
                        # return path_other, path_current

                aux_map[nx][ny] = colour
                pred[(nx, ny)] = (px, py)

                if step:
                    queue_1.append((nx, ny))
                else:
                    queue_2.append((nx, ny))

            step = 1 - step # switch colours

        return None

    def seek_available_tile(self, orig):

        orig = tuple(orig)
        queue = deque([orig])

        pred = {}
        pred[orig] = None

        available = []

        while len(queue) > 0:
            (px, py) = queue.popleft()

            if self.explore_map[px][py] == CognitiveMonkey.Unvisited:

                pos  = (px, py)
                # available.append(pos)
                # continue

                plan = [pos]
                while pred[pos]:
                    plan.append(pred[pos])
                    pos = pred[pos]

                plan = [(CognitiveMonkey.ExploreGradient, pos) for pos in plan[::-1][1:]]
                return (CognitiveMonkey.ExploreGradient, pos), plan

            for dx, dy in CognitiveMonkey.Directions:
                nx, ny = px + dx, py + dy

                if (nx, ny) in pred:
                    continue

                if nx < 0 or ny < 0 or nx >= self.world.height or ny >= self.world.width:
                    continue

                if self.explore_map[nx][ny] == CognitiveMonkey.Obstacle:
                    continue

                pred[(nx, ny)] = (px, py)
                queue.append((nx, ny))

        # available = []
        # for i in xrange(len(self.explore_map)):
        #     for j in xrange(len(self.explore_map[i])):
        #             if self.explore_map[i][j] == CognitiveMonkey.Unvisited:
        #                 available.append((i, j))
        if len(available) == 0:
            return None

        pos = random.choice(available)
        plan = [pos]
        while pred[pos]:
            plan.append(pred[pos])
            pos = pred[pos]

        plan = [(CognitiveMonkey.ExploreGradient, pos) for pos in plan[::-1][1:]]
        return (CognitiveMonkey.ExploreGradient, pos), plan

        # plan = self.compute_path(orig, dest)
        # print "Found something!", dest, plan
        # if len(plan) == 0:
        #     return None
        # for dx, dy in CognitiveMonkey.Directions:
        #     nx, ny = orig[0] + dx, orig[1] + dy
        #     print self.explore_map[nx][ny]
        #
        # for x, y in plan:
        #     print (x, y), self.explore_map[x][y]
        # exit(0)
        # return (CognitiveMonkey.ExploreGradient, dest), plan

    def update_map(self, agent, collisions):

        self.mark_item_on_map(agent.pos, agent.radius, CognitiveMonkey.Empty)

        for food_item in collisions[World.Food]:
            pos = food_item.pos

            if self.check_out_of_bounds(pos):
                continue

            if food_item.quantity == 0:
                continue

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

        # self.check_map_explored()

    def check_map_explored(self):

        for line in self.explore_map:
            for item in line:
                if item == CognitiveMonkey.Unvisited:
                    return

        print "Map succesfully explored!"
        exit(0)

    def check_resources_depleted(self):

        for item in self.world.object_type_matrix[World.Food]:
            if not item.invisible:
                return False
        return True

    def set_random_strategy(self, bot):

        # pp("RANDOM STRATEGY")
        pos    = tuple(map(int, bot.agent.pos))
        data   = self.bot_db[bot]
        result = self.seek_available_tile(pos)

        if not result:
            pp("No tile left to explore!!")
            # exit(0)
        else:
            target, plan = result
            data["targets"] = deque([target])
            data["plan"] = deque(plan)

    def set_exploration_goals(self, bot):

        data = self.bot_db[bot]
        targets = data["targets"]

        if len(targets) == 0:
            # check if not a starting position
            if bot.agent.pos == self.base.pos:
                exploration_goal = (EvolvedBrain.ExploreSpiral, data["theta"])
                targets.append(exploration_goal)
            else:
                self.set_random_strategy(bot)

        goal_type, goal_data = targets[0]

        if goal_type == EvolvedBrain.ExploreSpiral:
            data["plan"] = deque([(EvolvedBrain.ExploreSpiral, data)])

        elif goal_type == EvolvedBrain.ExploreGradient:

            pos = map(int, bot.agent.pos)

            if pos == goal_data:

                # print "Remove exploration target !!"
                targets.popleft()

                if len(targets) == 0:
                    self.set_random_strategy(bot)
                else:
                    goal_type, goal_data = targets[0]
                    if goal_type == EvolvedBrain.ExploreSpiral:
                        data["plan"] = deque([(EvolvedBrain.ExploreSpiral, data)])
                    elif goal_type == EvolvedBrain.ExploreGradient:
                        data["plan"] = deque([(CognitiveMonkey.ExploreGradient, pos)
                                            for pos in self.compute_path(pos, goal_data)])
                    else:
                        print "Untreated exception."
                        print targets
                        print data["plan"]
                        print goal_type
                        exit(0)

            elif len(data["plan"]) == 0:

                plan = self.compute_path(pos, goal_data)

                if len(plan) == 0:
                    self.set_random_strategy(bot)
                else:
                    plan = [(CognitiveMonkey.ExploreGradient, pos) for pos in plan]
                    data["plan"] = deque(plan)

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

        if not (self.check_out_of_bounds(pos) or self.check_invalid_position(pos)):
            return

        # print
        # print "NASPA POZ ", pos

        # out_of_bounds -> go to a random direction

        # was spiraling -> compute the next "safe" position
        #               -> set it as target

        bot_info = self.bot_db[bot]
        goal_type, goal_data = bot_info["targets"][0]

        if goal_type == EvolvedBrain.ExploreSpiral:

            while not self.check_out_of_bounds(pos) and self.check_invalid_position(pos):
                pos = map(int, self.spiral_exploration(bot_info))

            if self.check_out_of_bounds(pos):
                # pp("OUT OF BOUNDS")
                bot.agent.pos = bot.last_pos
                self.set_random_strategy(bot)
                return

            goal = (CognitiveMonkey.ExploreGradient, pos)
            bot_info["targets"].appendleft(goal)
            bot_info["plan"] = deque([]) # Trigger a plan computation
            last_pos = bot.last_pos

        if goal_type == EvolvedBrain.ExploreGradient:
            # print "INVALID ", goal_type, self.explore_map[pos[0]][pos[1]], pos
            # print "@@@ EMPTY !!!!"
            bot.agent.pos = bot.last_pos
            self.set_random_strategy(bot)

        bot.agent.pos = bot.last_pos

    def bumped_walls(self):

        for bot in self.search_agents:
            self.redirected_wall_bumper(bot)

        for bot in self.carrier_agents:
            self.redirected_wall_bumper(bot)

    def assign_command(self):

        for bot in self.bot_db:
            cmd = self.bot_db[bot]["plan"]

            if len(cmd) > 0:
                bot.inbox.append(cmd.popleft())

    def check_bot_interested_in_the_hunt(self, bot):

        data = self.bot_db[bot]

        if data["food_stored"] == data["capacity"]:
            return False

        return True

    @staticmethod
    def rule_to_return_to_exploration_after_the_hunt(targets, bot):

        target = targets[0]
        goal_type, goal_data = target

        if goal_type == CognitiveMonkey.ExploreSpiral or\
           goal_type == CognitiveMonkey.ExploreGradient:

            current_pos = map(int, bot.agent.pos)
            goal = (CognitiveMonkey.ExploreGradient, current_pos)
            targets.appendleft(goal)

            return True

        return False


    def assign_food(self, food_pos, food_quantity, bot):

        data    = self.bot_db[bot]
        targets = data["targets"]

        return_to_base = False

        if len(targets) > 0:
            return_to_base = CognitiveMonkey.rule_to_return_to_exploration_after_the_hunt(targets, bot)

        food_amount = min(data["capacity"] - data["food_stored"], food_quantity)

        # virtual increase in amount of food stored
        data["food_stored"] += food_amount
        finish_move = {"pos": food_pos, "amount": food_amount}
        # print "Food 'stored'", data["food_stored"]

        if return_to_base:
            targets.appendleft((CognitiveMonkey.ReturnToBase, self.world.base))

        targets.appendleft((CognitiveMonkey.GatherResource, finish_move))
        data["plan"] = deque([])

        return food_amount

    def let_the_hunt_begin(self):

        """
            Assign units to the food gathering process.
            Also known as 'the great hunt'.
            :return:
        """

        for bot in self.search_agents:
            data = self.bot_db[bot]

            targets = data["targets"]

            if len(targets) == 0:
                continue

            goal_type, goal_data = targets[0]

            if goal_type == EvolvedBrain.GatherResource:

                if len(data["plan"]) > 0:
                    continue

                pos = tuple(map(int, bot.agent.pos))

                if goal_data["pos"] == pos:
                    # print "Target munched!"
                    targets.popleft()
                    data["plan"] = deque([])

                    food_item = self.world.object_matrix[pos]
                    if food_item.quantity == 0:
                        food_item.invisible = True #TODO

                    if len(targets) > 0:
                        goal_type, goal_data = targets[0]

                        if goal_type == CognitiveMonkey.ReturnToBase:
                            # print "Plan for returning to the base."
                            # TODO: seek closest carrier as well

                            distance_to_carrier = Collisions.distance(bot.agent.pos, self.world.base.pos)
                            carrier = self.world.base

                            for other in self.carrier_agents:

                                targets = self.bot_db[other]["targets"]

                                # check if the carrier is already engaged
                                if len(targets) > 0 and targets[0][0] == CognitiveMonkey.MeetUp:
                                    continue

                                distance = Collisions.distance(bot.agent.pos, other.agent.pos)

                                if distance < distance_to_carrier:
                                    distance_to_carrier = distance
                                    carrier = other

                            if carrier != self.world.base:
                                target_bot, target_carrier = self.bot_finds_love(bot, carrier)

                                targets_carrier = self.bot_db[carrier]["targets"]

                                if len(targets_carrier) > 0:

                                    t = targets_carrier[0]
                                    pos_carrier = tuple(map(int, carrier.agent.pos))
                                    if t[0] == CognitiveMonkey.ExploreSpiral:
                                        targets_carrier.appendleft((CognitiveMonkey.ExploreGradient, pos_carrier))

                                    targets_carrier.appendleft((CognitiveMonkey.ExploreGradient, target_carrier))
                                    self.bot_db[carrier]["plan"] = deque([])

                                    plan = self.compute_path(bot.agent.pos, target_bot)
                                    data["plan"] = deque([(CognitiveMonkey.ExploreGradient, pos) for pos in plan])
                                    info = {"amount": data["food_stored"], "target": carrier.agent}
                                    data["plan"].append((CognitiveMonkey.ReturnToBase, info))
                                    # print "MeetUp"

                            else:
                                plan = self.compute_path(bot.agent.pos, self.world.base.pos)
                                data["plan"] = deque([(CognitiveMonkey.ExploreGradient, pos) for pos in plan])
                                info = {"amount": data["food_stored"], "target": self.world.base}
                                data["plan"].append((CognitiveMonkey.ReturnToBase, info))

            elif goal_type == CognitiveMonkey.ReturnToBase:
                if len(data["plan"]) == 0:
                    targets.popleft()
                    data["food_stored"] = 0
                    # print "Return to base successfully."

        for food_pos in self.free_resources:

            item   = self.free_resources[food_pos]

            if item.quantity == 0:
                continue

            while item.quantity > 0:

                distance    = CognitiveMonkey.InfiniteDistance
                best_choice = None

                willing_robots = [bot for bot in self.search_agents if
                                  self.check_bot_interested_in_the_hunt(bot)]

                for bot in willing_robots:
                    dist = Collisions.distance(bot.agent.pos, food_pos)
                    if distance > dist:
                        best_choice, distance = bot, dist

                # no more interested bots
                if not best_choice:
                    # print "No bot interested"
                    break

                # print "Found interested bot: ", best_choice, distance
                item.quantity -= self.assign_food(food_pos, item.quantity, best_choice)

            if item.quantity == 0:
                self.assumed_resources[food_pos] = item

        for bot in self.search_agents:

            data = self.bot_db[bot]
            targets = data["targets"]

            if len(targets) > 0:
                goal_type, goal_data = targets[0]

                # TODO: sort food by distance
                if goal_type == CognitiveMonkey.GatherResource:

                    if len(data["plan"]) == 0:

                        items = []
                        # attempting an optimum plan

                        items = [item for item in targets if item[0] == CognitiveMonkey.GatherResource]

                        # if len(items) > 1:
                        #     pos = bot.agent.pos
                        #     items = sorted(items, key=lambda (_, v): -Collisions.distance(pos, v["pos"]))
                        #     slice = list(itertools.islice(targets, len(items), len(targets)))
                        #     items += slice
                        #     data["targets"] = deque(items)
                            # print "sorted"

                        goal_type, goal_data = data["targets"][0]

                        # print "Made a new plan!"
                        plan = self.compute_path(bot.agent.pos, goal_data["pos"])
                        data["plan"] = deque([(CognitiveMonkey.ExploreGradient, pos) for pos in plan])
                        data["plan"].append((CognitiveMonkey.GatherResource, goal_data))

                        # print data["plan"]

            # print "Targets", self.bot_db[bot]["targets"]
            # print "Plan", self.bot_db[bot]["plan"]
            # print

    # def unload_resources(self, bot, collisions):

        # data = self.bot_db[bot]
        # food_stored = data["food_stored"]
        #
        # if food_stored == 0:
        #     return
        #
        # for agent in collisions[World.Agents]:
        #     if isinstance(agent, CarrierAgent):
        #         agent.food_stored += food_stored
        #         data["food_stored"] = 0
        #         print "Dumped food in da carrier."
        #         return
        #
        # if collisions[World.Base]:
        #     data["food_stored"] = 0
        #     self.world.base.food_stored += food_stored
        #     print "Dumped food in da base."

    def compute_master_plan(self):

        self.bumped_walls()
        self.acquire_knowledge()
        self.let_the_hunt_begin()
        self.explore()
        self.assign_command()

    def think(self):

        if len(self.inbox) != 0:
            self.apply_command(self.inbox.pop())
            return