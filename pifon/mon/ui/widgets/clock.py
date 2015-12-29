
import time

class Clock(object):
  def __init__(self):
    self.last_ts = 0
    self.txt = "--:--:--"

  def tick(self):
    t = time.time()
    delta = t - self.last_ts
    if delta >= 1:
      self.last_ts = t
      # one second passed -> update
      lt = time.localtime(t)
      hours = lt[3]
      mins = lt[4]
      secs = lt[5]
      self.txt = "%02d:%02d:%02d" % (hours, mins, secs)
      return True
    else:
      return False

  def get_length(self):
    return 8

  def get_text(self):
    return self.txt
