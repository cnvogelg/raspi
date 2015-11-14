from __future__ import print_function
import player

class PlayCtl:
  """control the playback of the audio stream.

     Playback can either be triggered by a state change from the
     audio server or by manually enable listening to a server.

     If playback is started by a state change from an audio server
     then control will play back this source until it leaves an
     active state. If another server gets active while a source
     is already playing then it is ignored.

     Manual listening may override any playing triggered by active
     server states.
  """

  PLAY_CONTROL_OFF = 0
  PLAY_CONTROL_PLAY = 1
  PLAY_CONTROL_LISTEN = 2
  PLAY_CONTROL_MUTE = 3

  def __init__(self, player):
    self.player = player
    self.callback = None
    self.listen_srv = None
    self.play_srv = None
    self.chime_start = None
    self.chime_stop = None
    self.url_map = {}
    self.state_map = {}
    self.active_states = ('attack', 'active', 'sustain')
    self.muted = False

  def set_callback(self, callback):
    self.callback = callback

  def set_chimes(self, start=None, stop=None):
    """set sound files for start/stop chimes.
       set to none to disable chimes"""
    self.chime_start = start
    self.chime_stop = stop

  def exit(self):
    """exit playctl and shutdown listening"""
    if self.is_playing():
      self._stop()

  def get_state(self):
    if self.is_playing():
      return self.PLAY_CONTROL_PLAY
    elif self.is_listening():
      return self.PLAY_CONTROL_LISTEN
    elif self.is_muted():
      return self.PLAY_CONTROL_MUTE
    else:
      return self.PLAY_CONTROL_OFF

  def is_playing(self):
    """return true if someone is playing"""
    return self.play_srv is not None or self.listen_srv is not None

  def is_listening(self):
    """return true if (manual) listening is enabled"""
    return self.listen_srv is not None

  def is_muted(self):
    return self.muted

  def mute(self):
    if self.muted:
      return False
    # stop listening
    if self.listen_srv is not None:
      self.listen_srv = None
    if self.play_srv is not None:
      ok = self._stop()
    else:
      ok = True
    if ok:
      # realize mute
      self.muted = True
      if self.callback is not None:
        self.callback.playctl_mute()
    return ok

  def unmute(self):
    if not self.muted:
      return False
    # realize unmute
    self.muted = False
    if self.callback is not None:
      self.callback.playctl_unmute()
    # auto start if another server is active?
    srv = self._find_active()
    if srv is not None:
      return self._play(srv)
    else:
      return True

  def listen(self, server):
    """enable manual listening"""
    # if was muted disable it
    if self.muted:
      self.muted = False
    # already listening?
    if self.listen_srv is not None:
      return False
    # is anyone playing?
    srv = self.play_srv
    # already playing this source -> do nothing
    if srv == server:
      ok = True
    # another one is playing -> stop it, and start me
    elif srv is not None:
      self._stop()
      ok = self._play(server)
    # no one is playing -> start me
    else:
      ok = self._play(server)
    if ok:
      self.listen_srv = server
      # report
      if self.callback is not None:
        self.callback.playctl_listen(server)
    return ok

  def unlisten(self):
    """disable manual listening"""
    if self.listen_srv is None:
      return False
    # report unlisten
    if self.callback is not None:
      self.callback.playctl_unlisten(self.listen_srv)
    self.listen_srv = None
    # if current server is not active anymore -> stop it
    srv = self.play_srv
    if not self._is_active(srv):
      ok = self._stop()
      if not ok:
        return False
      # is another active?
      srv = self._find_active()
      if srv is not None:
        return self._play(srv)
    return True

  def audio_connect(self, server, server_url):
    """report that a server has connected"""
    # register server url
    self.url_map[server] = server_url

  def audio_disconnect(self, server):
    """report a server that is lost"""
    # unregister server url and state
    del self.url_map[server]
    if server in self.state_map:
      del self.state_map[server]

    # was listening? -> unlisten the server
    if server == self.listen_srv:
      self.listen_srv = None
      # report unlisten
      if self.callback is not None:
        self.callback.playctl_unlisten(server)

    # is server playing? -> stop this one
    if server == self.play_srv:
      self._stop()
    # is another server still active? -> switch to this one
    new_srv = self._find_active()
    if new_srv is not None:
      self._play(new_srv)

  def audio_state(self, server, state):
    """report a new audio state from a server"""
    # keep state
    self.state_map[server] = state
    # if no one is playing then check
    if self.play_srv is None:
      if state in self.active_states:
        self._play(server)
    # if we are playing then check if its still valid
    elif self.play_srv == server:
      if state not in self.active_states:
        if self.listen_srv is None:
          self._stop()

  def _is_active(self, server):
    """has the given server an active state?"""
    if server in self.state_map:
      state = self.state_map[server]
      return state in self.active_states
    else:
      return False

  def _find_active(self):
    """find a server that is still in an active state"""
    for server in self.state_map:
      state = self.state_map[server]
      if state in self.active_states:
        return server
    return None

  def _play(self, server):
    """start playing"""
    if self.play_srv is not None:
      return False
    # start with a chime?
    if self.chime_start is not None:
      ok = self.player.play_chime(self.chime_start)
      if not ok:
        return False
    # start streaming
    url = self.url_map[server]
    ok = self.player.play(url)
    if not ok:
      return False
    # set play server
    self.play_srv = server
    # report play
    if self.callback is not None:
      self.callback.playctl_play(server)
    return True

  def _stop(self):
    """stop playing"""
    if self.play_srv is None:
      return False
    # stop
    srv = self.play_srv
    self.play_srv = None
    # report stop
    if self.callback is not None:
      self.callback.playctl_stop(srv)
    # stop streaming
    ok = self.player.stop()
    if not ok:
      return False
    # play stop chime
    if self.chime_stop is not None:
      ok = self.player.play_chime(self.chime_stop)
      if not ok:
        return False
    return True


# ----- Test -----
if __name__ == '__main__':
  import player

  class Callbacks:
    def playctl_play(self, server):
      print("play", server)
    def playctl_stop(self, server):
      print("stop", server)
    def playctl_listen(self, server):
      print("listen", server)
    def playctl_unlisten(self, server):
      print("unlisten", server)
    def playctl_mute(self):
      print("mute")
    def playctl_unmute(self):
      print("unmute")

  pc = PlayCtl(player.create_player('dummy'))
  pc.set_callback(Callbacks())
  # simul connect
  pc.audio_connect("a", "http://a/play")
  pc.audio_connect("b", "http://b/play")
  # listen/unlisten
  print("----- listen -----")
  pc.listen("a")
  pc.unlisten()
  # mute
  print("----- mute -----")
  pc.mute()
  pc.unmute()
  # trigger state
  print("----- trigger state -----")
  pc.audio_state("a", "attack")
  pc.audio_state("a", "active")
  pc.audio_state("a", "sustain")
  pc.audio_state("a", "respite")
  # shutdown
  print("----- shutdown -----")
  pc.exit()


