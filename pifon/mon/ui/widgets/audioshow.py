from __future__ import print_function
import sys

class AudioShow(object):
  def __init__(self, a, hb_chars="?!o.", play_chars=">|!", level_chars="01234567#"):
    self.audio = a
    # config chars
    self.hb_chars = hb_chars
    self.play_chars = play_chars
    self.level_chars = level_chars
    # text state
    self.hb = None
    self.play = None
    self.level = None
    self.state = None
    # first update
    self.update()

  def update(self):
    """return True if text was changed"""
    self.hb = self._get_heartbeat()
    self.play = self._get_play()
    self.level = self._get_level()
    self.state = self._get_state()

  def _get_heartbeat(self):
    ping = self.audio.ping
    if ping is None:
      return self.hb_chars[0]
    elif ping == 'requested':
      return self.hb_chars[2]
    elif ping == 'alive':
      return self.hb_chars[3]
    else:
      return self.hb_chars[1]

  def _get_play(self):
    is_playing = self.audio.is_playing
    active = self.audio.audio_active
    if is_playing:
      return self.play_chars[0]
    elif active:
      return self.play_chars[1]
    else:
      return self.play_chars[2]

  def _get_level(self):
    level = self.audio.audio_level
    if level is not None:
      l = level[1]
      t = level[2]
      if l < 8:
        lc = self.level_chars[l]
      else:
        lc = self.level_chars[8]
      if t < 100:
        tc = "%02d" % t
      else:
        tc = "^^"
      return lc + "+" + tc
    else:
      return "_+__"

  def _get_state(self):
    state = self.audio.audio_state
    if state is not None:
      char = state[0].upper()
      if char == 'I': # idle
        char = "_"
      return char
    else:
      return "_"

  def get_text(self):
    res = []
    # heartbeat
    if self.hb is not None:
      res.append(self.hb)
    # play state
    if self.play is not None:
      res.append(self.play)
    # state
    if self.state is not None:
      res.append(self.state)
    # level
    if self.level is not None:
      res.append(self.level)
    txt = "".join(res)
    return txt
