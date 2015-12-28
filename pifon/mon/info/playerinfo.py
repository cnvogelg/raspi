
class PlayerInfo:

  FLAG_PLAY_SERVER = 1
  FLAG_MODE = 2

  def __init__(self, name):
    self.name = name
    self.play_server = None
    self.mode = None

  def __repr__(self):
    return "<%s:play:%s:%s>" % (self.name,
      self.play_server, self.mode)
