class Logic(object):
  def __init__(self, world):
    self.world = world

  def is_over(self):
    ''' TODO done logic '''
    return False
  def think(self):
    for agent in self.world.agents:
      agent.execute_tick()

