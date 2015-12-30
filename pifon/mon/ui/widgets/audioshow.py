from __future__ import print_function
import sys

class AudioShow(object):
  def __init__(self, a, hb_chars="?!o.", play_chars=">|!"):
    self.audio = a
    # config chars
    self.hb_chars = hb_chars
    self.play_chars = play_chars
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
      return "%d/%d+%d" % (level[1], level[0], level[2])
    else:
      return ""

  def _get_state(self):
    state = self.audio.audio_state
    if state is not None:
      char = state[0].upper()
      if char == 'I': # idle
        char = " "
      return char
    else:
      return " "

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
