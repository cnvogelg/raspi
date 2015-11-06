from __future__ import print_function
import sys

class PlayerDummy:
  def play_chime(self, url):
    print("player: chime '%s'" % url, file=sys.stderr)
    return True

  def play(self, url):
    print("player: play '%s'" % url, file=sys.stderr)
    return True

  def stop(self):
    print("player: stop", file=sys.stderr)
    return True
