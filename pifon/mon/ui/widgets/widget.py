from __future__ import print_function

class Widget(object):
  """the base class for all simple text based widgets we use for the mon"""

  def __init__(self, pos, width):
    """create a widget by giving its pos (x,y) tuple and width"""
    self.pos = pos
    self.width = width
    self.is_dirty = True
    self.is_shown = True

  def show(self, is_shown):
    self.is_shown = is_shown
    # automatically force redraw if widget is shown again
    if is_shown:
      self.is_dirty = True

  def get_pos(self):
    return self.pos

  def get_width(self):
    return self.width

  def set_dirty(self):
    self.is_dirty = True

  def get_text(self, yl):
    """return the text string for the given local y coord starting from 0"""
    pass

  def redraw(self, draw_func, force=False):
    """render the widget (if necessary/dirty) and call draw_func(pos, text)

       return True if something was drawn
    """
    if self.is_shown:
      if self.is_dirty or force:
        self.is_dirty = False
        w = self.width
        t = self.get_text()
        if t is not None:
          n = len(t)
          if n < w: # pad
            t += " " * (n-w)
          elif t > w: # crop
            t = t[0:w]
          draw_func(self.pos, t)
      return True
    return False

  def tick(self, ts, delta):
    """perform updates required on a regular basis. this function is
       called every delta ms and gives the absolute timestamp, too.
       typically the function changes internal state and sets the
       dirty flag for the next redraw"""
    pass
