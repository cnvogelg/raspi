from widget import Widget

class Label(Widget):

  ALIGN_LEFT = 0
  ALIGN_CENTER = 1
  ALIGN_RIGHT = 2

  def __init__(self, pos, width, text="", align=ALIGN_LEFT, stay_delay=1):
    Widget.__init__(self, pos, width)
    self.width = width
    self.text = text
    self.align = align
    self.stay_delay = stay_delay
    self.scroll = 0
    self.stay = 0
    self.fwd = False

  def tick(self, ts, delta):
    if self.text is None:
      return
    n = len(self.text)
    if n > self.width:
      dirty = True
      # do scrolling
      if self.fwd:
        if self.scroll == n - self.width:
          if self.stay == self.stay_delay:
            self.fwd = False
            self.scroll -= 1
            self.stay = 0
          else:
            self.stay += 1
            dirty = False
        else:
          self.scroll += 1
      else:
        if self.scroll == 0:
          if self.stay == self.stay_delay:
            self.fwd = True
            self.scroll += 1
            self.stay = 0
          else:
            self.stay +=1
            dirty = False
        else:
          self.scroll -= 1
      if dirty:
        self.set_dirty()

  def set_text(self, text):
    if self.text != text:
      self.text = str(text)
      self.scroll = 0
      self.fwd = True
      self.set_dirty()

  def get_text(self):
    t = self.text
    w = self.width
    if t is None:
      return " " * w
    else:
      n = len(t)
      if n < w:
        # text is shorter than label
        pad = w - n
        # align short text
        if self.align == self.ALIGN_LEFT:
          return t + " " * pad
        elif self.align == self.ALIGN_RIGHT:
          return " " * pad + t
        else:
          # center
          p1 = int(pad / 2)
          p2 = int((pad + 1) / 2)
          return " " * p1 + t + " " * p2
      elif n > w:
        # text is longer than label
        p = self.scroll
        return t[p:p+w]
      else:
        return t


# test
if __name__ == '__main__':
  l = Label((0,0),4,"Maja+Willi!")
  for i in range(10):
    print(l.get_text(), l.scroll, l.stay, l.fwd)
    l.tick(1,2)

  l = Label((0,0),5,"jo")
  print("'%s'" % l.get_text())
  l = Label((0,0),5,"jo", Label.ALIGN_RIGHT)
  print("'%s'" % l.get_text())
  l = Label((0,0),5,"jo", Label.ALIGN_CENTER)
  print("'%s'" % l.get_text())
