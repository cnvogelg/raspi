class PlayerShow(object):
  def __init__(self, p, mapper, play_chars="ps", mode_chars="oxl?"):
    self.player = p
    self.mapper = mapper
    self.play_chars = play_chars
    self.mode_chars = mode_chars
    # text state
    self.play = None
    self.index = None
    self.mode = None
    # initial update
    self.update()

  def update(self):
    self.play = self._get_play()
    self.index = self._get_index()
    self.mode = self._get_mode()

  def _get_play(self):
    ps = self.player.play_server
    if ps is not None:
      return self.play_chars[0]
    else:
      return self.play_chars[1]

  def _get_index(self):
    ps = self.player.play_server
    if ps is not None:
      return self.mapper(ps)
    else:
      return " "

  def _get_mode(self):
    m = self.player.mode
    if m == 'monitor':
      return self.mode_chars[0]
    elif m == 'mute':
      return self.mode_chars[1]
    elif m == 'listen':
      return self.mode_chars[2]
    else:
      return self.mode_chars[3]

  def get_text(self):
    res = []
    if self.play is not None:
      res.append(self.play)
    if self.mode is not None:
      res.append(self.mode)
    if self.index is not None:
      res.append(self.index)
    return "".join(res)
