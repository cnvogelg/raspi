
class PlayerInfo:

  FLAG_PLAY_SERVER = 1
  FLAG_MODE = 2
  FLAG_CHIME = 4

  def __init__(self, name):
    self.name = name
    self.play_server = None
    self.mode = None
    self.chime = None

  def is_ready(self):
    return self.mode is not None and self.chime is not None

  def __repr__(self):
    return "<%s:player[mode=%s,chime=%s],play_server=%s>" % (self.name,
      self.mode, self.chime,
      self.play_server)
