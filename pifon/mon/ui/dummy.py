from __future__ import print_function

import sys

class UI:
  """mini 'UI' to demonstrate the UI interface"""

  def __init__(self, cfg):
    self.cfg = cfg

  def _p(self, *args, **kwargs):
    a = ["**dummy**"] + list(args)
    print(*a,file=sys.stderr,**kwargs)

  def get_tick_interval(self):
    return 2.0

  def on_tick(self, ts, delta):
    """called every tick interval to do regular stuff like handling events
       doing redraws and so on
    """
    self._p("on_tick", delta)

  # audio calls

  def audio_add(self, a):
    self._p("audio_add", a)

  def audio_del(self, a):
    self._p("audio_del", a)

  def audio_update(self, a, flags):
    self._p("audio_update", a, flags)

  # player calls

  def player_add(self, p):
    self._p("player_add", p)

  def player_del(self, p):
    self._p("player_del", p)

  def player_update(self, p, flags):
    self._p("player_update", p, flags)
