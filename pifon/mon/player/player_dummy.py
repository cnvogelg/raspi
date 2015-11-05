from __future__ import print_function

class PlayerDummy:
  def play_chime(self, url):
    print("player: chime '%s'" % url)

  def play(self, url):
    print("player: play '%s'" % url)

  def stop(self, url):
    print("player: stop")
