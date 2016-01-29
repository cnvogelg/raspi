from widget import Widget

class AudioShow(Widget):
  def __init__(self, pos, idx, a, level_chars="01234567#"):
    Widget.__init__(self, pos, 4)
    self.idx = idx
    self.audio = a
    self.text = None
    self.level_cahrs = level_chars
    # first update
    self.update()

  def update(self):
    """return True if text was changed"""
    # 1. index of source
    idx = chr(ord('0')+self.idx)
    # 2. state
    state = self._get_state()
    # 3. active/ping
    active = self._get_active_and_ping()
    # 4. level
    level = self._get_level()
    self.text = idx + state + active + level
    self.set_dirty()

  def _get_state(self):
    state = self.audio.audio_state
    if state is not None:
      return state[0].upper()
    else:
      return "_"

  def _get_active_and_ping(self):
    ping = self.audio.ping
    if ping == 'requested':
      return "."
    elif ping == 'alive':
      p = self._get_play()
      if p is not None:
        return p
      return "o"
    else: # timeout
      return "?"

  def _get_play(self):
    is_playing = self.audio.is_playing
    active = self.audio.audio_active
    if is_playing:
      return "P"
    elif active:
      return "*"
    else:
      return None

  def _get_level(self):
    level = self.audio.audio_level
    if level is not None:
      l = level[1]
      if l < 8:
        lc = self.level_chars[l]
      else:
        lc = self.level_chars[8]
      return lc
    else:
      return " "

  def get_text(self):
    return self.text
