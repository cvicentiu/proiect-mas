import Tkinter

class Screen():

  tick_count = 0
  def __init__(self, world, thinker):
    self.root = Tkinter.Tk()
    self.canvas = Tkinter.Canvas(self.root,
                                 width=world.width, height=world.height)
    self.canvas.pack()
    self.thinker = thinker
    self.world = world
    self.canvas.after(1, self.tick)
    self.root.mainloop()

  def tick(self):

    if self.thinker.is_over():
      return

    self.thinker.think()
    self.canvas.delete('all')

    for food in self.world.food:
      food.paint(self.world, self.canvas)

    for obstacle in self.world.obstacles:
      obstacle.paint(self.world, self.canvas)

    for crumb in self.world.crumbs:
      crumb.paint(self.world, self.canvas)

    self.world.base.paint(self.world, self.canvas)

    for agent in self.world.agents:
      agent.paint(self.world, self.canvas)



    self.canvas.create_text(50, 10, text=str(Screen.tick_count))
    Screen.tick_count = Screen.tick_count + 1
    self.canvas.after(1, self.tick)
