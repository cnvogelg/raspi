from __future__ import print_function
import sys

from base import BasePlayer

class PlayerDummy(BasePlayer):
  def _play_chime(self, url):
    print("player: chime '%s'" % url, file=sys.stderr)
    return True

  def _play(self, url):
    print("player: play '%s'" % url, file=sys.stderr)
    return True

  def _stop(self):
    print("player: stop", file=sys.stderr)
    return True
