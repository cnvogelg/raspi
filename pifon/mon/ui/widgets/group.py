from __future__ import print_function

from widget import Widget

class Group(Widget):
  """group widgets"""

  def __init__(self, pos, width):
    Widget.__init__(self, pos, width)
    self.widgets = []

  def add_widget(self, w):
    self.widgets.append(w)

  def show(self, is_shown):
    Widget.show(self, is_shown)
    for w in self.widgets:
      w.show(is_shown)

  def set_dirty(self):
    Widget.set_dirty(self)
    for w in self.widgets:
      w.set_dirty()

  def get_text(self):
    return None

  def redraw(self, draw_func, force=False):
    for w in self.widgets:
      w.redraw(draw_func, force)

  def tick(self, ts, delta):
    for w in self.widgets:
      w.tick(ts, delta)
