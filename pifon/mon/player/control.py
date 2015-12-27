from __future__ import print_function

class Control:
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

  # modes set by the user
  MODE_MONITOR = 0
  MODE_MUTE = 1
  MODE_LISTEN = 2

  mode_names = ('monitor', 'mute', 'listen')

  def __init__(self, player, reply=None):
    self.player = player
    self.reply = reply
    self.state = self.MODE_MONITOR
    self.play_srv = None
    self.url_map = {}
    self.active_map = {}

  def exit(self):
    """exit playctl and shutdown listening"""
    if self.player.is_playing():
      self.player.stop()

  def get_mode(self):
    """get current mode the user had set for the player"""
    return self.mode

  def monitor(self):
    return self.set_mode(self.MODE_MONITOR)

  def mute(self):
    return self.set_mode(self.MODE_MUTE)

  def listen(self, listen_srv):
    return self.set_mode(self.MODE_LISTEN, listen_srv)

  def set_mode(self, new_state, listen_srv=None):
    """the user sets a new mode
       return True if mode change was performed
    """
    # nothing to do as its the same state
    if self.state == new_state:
      return False
    # try to prepare state
    if new_state == self.MODE_MONITOR:
      ok = self._enter_monitor()
      listen_srv = None
    elif new_state == self.MODE_MUTE:
      ok = self._enter_mute()
      listen_srv = None
    elif new_state == self.MODE_LISTEN:
      if listen_srv is not None:
        ok = self._enter_listen(listen_srv)
      else:
        ok = False
    # set new state
    if ok:
      self.state = new_state
      self._report_new_state(new_state)
    return ok

  def report_mode(self, to):
    self._report_new_state(self.state, to)

  def _report_new_state(self, state, to=None):
    # report new state
    if self.reply is not None:
      self.reply(['mode',self.mode_names[self.state],self.play_srv],to=None)

  def _play_active(self):
    # is some server active? then play it
    srv = self._find_an_active_server()
    if srv is None:
      return True
    return self._play(srv)

  def _play(self, server):
    if server in self.url_map:
      url = self.url_map[server]
      if url is not None:
        if self.player.play(url):
          self.play_srv = server
          # report
          if self.reply is not None:
            self.reply(['play', server, url])
          return True
    return False

  def _stop(self):
    if self.player.stop():
      if self.reply is not None:
        self.reply(['stop', self.play_srv])
      self.play_srv = None
      return True
    return False

  def _stop_restart(self):
    self._stop()
    # if mode was listening then go to mute
    if self.state == self.MODE_LISTEN:
      self.state = self.MODE_MUTE
      self._report_new_state(self.state)
    # if we monitored this one then update and set a new actuve
    elif self.state == self.MODE_MONITOR:
      self._play_active()
      self._report_new_state(self.state)

  def _enter_monitor(self):
    # stop player
    if self.player.is_playing():
      # if player is still active then kepp it running
      if self._is_server_active(self.play_srv):
        return True
      # service is inactive -> so stop it
      else:
        self._stop()

    return self._play_active()

  def _enter_mute(self):
    # stop player
    if self.player.is_playing():
      self._stop()
    return True

  def _enter_listen(self, listen_srv):
    # already listening to right server
    if self.play_srv == listen_srv:
      return True

    # if another one is playing -> stop it
    if self.player.is_playing():
      self._stop()

    return self._play(listen_srv)

  # ----- events from the audio servers -----

  def audio_connect(self, server):
    """report that a server has connected"""
    # register server url
    self.url_map[server] = None

  def audio_disconnect(self, server):
    """report a server that is lost"""
    # unregister server url and active
    del self.url_map[server]
    if server in self.active_map:
      del self.active_map[server]

    # was this server playing? stop if
    if server == self.play_srv:
      self._stop_restart()

  def audio_src(self, server, listen_url):
    """report the listen url of the server"""
    self.url_map[server] = listen_url

  def audio_active(self, server, active):
    """report a new audio active state from a server"""
    # keep state
    self.active_map[server] = active
    # if no one is playing then check
    if self.play_srv is None and self.state == self.MODE_MONITOR:
      if active:
        self._play(server)
        self._report_new_state(self.state)
    # if we are playing then check if its still valid
    elif self.play_srv == server:
      if not active:
        self._stop_restart()

  # ----- active handling -----

  def _is_server_active(self, server):
    """has the given server an active state?"""
    if server in self.active_map:
      return self.active_map[server]
    else:
      return False

  def _find_an_active_server(self):
    """find a server that is still in an active state"""
    for server in self.active_map:
      active = self.active_map[server]
      url = self.url_map[server]
      if active and url is not None:
        return server
    return None


# ----- Test -----
if __name__ == '__main__':
  import create
  def out(args,to=None):
    print(args)
  pc = Control(create.create_player('dummy'),out)
  # simul connect
  pc.audio_connect("a", "http://a/play")
  pc.audio_connect("b", "http://b/play")
  # listen/unlisten
  print("----- listen -----")
  pc.listen("a")
  pc.monitor()
  # mute
  print("----- mute -----")
  pc.mute()
  pc.monitor()
  # trigger state
  print("----- trigger state -----")
  pc.audio_active("a", True)
  pc.audio_active("a", False)
  # shutdown
  print("----- shutdown -----")
  pc.exit()
