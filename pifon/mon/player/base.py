class BasePlayer:

  STATE_IDLE = 0
  STATE_PLAYING = 1

  def __init__(self):
    """setup idle player without chime sounds set"""
    self.state = self.STATE_IDLE
    self.play_url = None
    self.chime_start = None
    self.chime_stop = None
    self.allow_chimes = True

  def set_chimes(self, start, stop):
    """define start/stop chime sounds"""
    self.chime_start = start
    self.chime_stop = stop

  def set_allow_chimes(self, on):
    self.allow_chimes = on

  def get_allow_chimes(self):
    return self.allow_chimes

  def get_state(self):
    """return current player state"""
    return self.state

  def is_playing(self):
    return self.state == self.STATE_PLAYING

  def play(self, url):
    """if state is idle then start playing and enter playing state"""
    # hmm... nothing is playing
    if self.play_url is not None or self.state != self.STATE_IDLE:
      return False
    # start streaming
    if url is None:
      return False
    # start with a chime?
    if self.chime_start is not None and self.allow_chimes:
      ok = self._play_chime(self.chime_start)
      if not ok:
        return False
    # run native player
    ok = self._play(url)
    if not ok:
      return False
    # set play server
    self.play_url = url
    self.state = self.STATE_PLAYING
    return True

  def stop(self):
    """stop playing"""
    if self.play_url is None or self.state != self.STATE_PLAYING:
      return False
    # stop streaming
    ok1 = self._stop()
    # play stop chime
    if self.chime_stop is not None and self.allow_chimes:
      ok2 = self._play_chime(self.chime_stop)
    else:
      ok2 = True
    # set state
    if ok1 and ok2:
      self.play_url = None
      self.state = self.STATE_IDLE
      return True
    else:
      return False

  def _play(self, url):
    return True

  def _stop(self):
    return True

  def _play_chime(self, url):
    return True

# ----- test -----
if __name__ == '__main__':
  bp = BasePlayer()
  print(bp.play("bla"))
  print(bp.get_state())
  print(bp.stop())

