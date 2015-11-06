from __future__ import print_function

class PlayerDummy:
  def play_chime(self, url):
    print("player: chime '%s'" % url)
    return True

  def play(self, url):
    print("player: play '%s'" % url)
    return True

  def stop(self):
    print("player: stop")
    return True
