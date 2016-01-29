from widget import Widget

class PlayerShow(Widget):
  def __init__(self, pos, mapper):
    Widget.__init__(self, pos, 2)
    self.player = None
    self.mapper = mapper
    self.text = None
    # initial update
    self.update()

  def set_player(self, p):
    self.player = p
    self.update()

  def update(self):
    if self.player is None:
      self.text = "??"
    else:
      mode = self._get_mode()
      idx = self._get_index()
      self.mode = self._get_mode()
      self.text = mode + idx
    self.set_dirty()

  def _get_index(self):
    ps = self.player.play_server
    if ps is not None:
      return self.mapper(ps)
    else:
      return "_"

  def _get_mode(self):
    m = self.player.mode
    if m == 'monitor':
      ps = self.player.play_server
      if ps is not None:
        return "P"
      else:
        return "m"
    elif m == 'mute':
      return "u"
    elif m == 'listen':
      return "L"
    else:
      return "_"

  def get_text(self):
    return self.text

