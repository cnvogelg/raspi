class Simulator:
  STATE_SILENCE = 0
  STATE_INC = 1
  STATE_DEC = 2

  def __init__(self):
    self.state = self.STATE_SILENCE
    self.cnt = 0
    self.max_cnt = 30

  def read_rms(self):
    """return a new rms"""
    self.cnt += 1
    if self.cnt == self.max_cnt:
      self.cnt = 0
      # next state
      s = self.state
      if s == self.STATE_SILENCE:
        self.state = self.STATE_INC
      elif s == self.STATE_INC:
        self.state = self.STATE_DEC
      else:
        self.state = self.STATE_SILENCE
    # get value
    s = self.state
    if s == self.STATE_SILENCE:
      return 0
    elif s == self.STATE_INC:
      return self.cnt
    elif s == self.STATE_DEC:
      return self.max_cnt - self.cnt
