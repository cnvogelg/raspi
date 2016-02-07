import time

from widget import Widget

class Clock(Widget):

  days = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

  def __init__(self, pos):
    Widget.__init__(self, pos, 16)
    self.last_ts = 0
    self.txt = "--:--:--        "

  def tick(self, ts, delta):
    delta = ts - self.last_ts
    # one second passed -> update
    if delta >= 1:
      self.last_ts = ts
      # time is shown always
      lt = time.localtime(ts)
      self.txt = time.strftime("%H:%M:%S ",lt)
      # show addons in different time slots
      secs = lt[5]
      mode = secs / 10
      if mode in (0,3):
        self.txt += time.strftime("%W_%Y ",lt)
      elif mode in (1,4):
        self.txt += time.strftime("%a %Z",lt)
      else:
        self.txt += time.strftime("%d.%m. ",lt)
      # update request
      self.set_dirty()
      return True
    else:
      return False

  def get_text(self):
    return self.txt


# test
if __name__ == '__main__':
  import time
  c = Clock((0,0))
  for i in range(10):
    c.tick(time.time(),1)
    print(c.get_text())
    time.sleep(1)
