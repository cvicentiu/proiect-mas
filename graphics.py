from world import *
import Tkinter
class Screen():
  def __init__(self, world, thinker):
    self.root = Tkinter.Tk()
    self.canvas = Tkinter.Canvas(self.root,
                                 width=world.width, height=world.height)
    self.canvas.pack()
    self.thinker = thinker
    self.world = world
    self.tick_count = 0
    self.canvas.after(1, self.tick)
    self.root.mainloop()

  def tick(self):
    if self.thinker.is_over():
      return
    self.thinker.think()
    self.canvas.delete('all')
    for obj in WorldObject.objects:
      obj.paint(self.world, self.canvas)
    self.canvas.create_text(50, 10, text=str(self.tick_count))
    self.tick_count = self.tick_count + 1
    self.canvas.after(1, self.tick)
