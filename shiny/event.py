class Event(object):

  BUTTON_DOWN = 1
  BUTTON_UP = 2
  MOUSE_MOVE = 3

  def __init__(self, event_type, pos):
    self.type = event_type
    self.pos = pos

  def __str__(self):
    return "[type=%s, pos=%s]" % (self.type, self.pos)

  def is_in_rect(self, rect):
    x = self.pos[0]
    y = self.pos[1]

    x1 = rect[0]
    y1 = rect[1]
    if (x < x1) or (y < y1):
      return False

    x2 = rect[0] + rect[2]
    y2 = rect[1] + rect[3]
    if (x >= x2) or (y >= y2):
      return False

    return True
