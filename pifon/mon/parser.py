from __future__ import print_function
import sys

class Parser:

  def __init__(self, state):
    self.state = state

  def _warn(self, msg):
    print("parser?:",msg,file=sys.stderr)

  # pifon/audio calls

  def audio_state(self, msg):
    args = msg.args
    if len(args) == 2:
      state = args[1]
      self.state.report_audio_state(state)
    else:
      self._warn(args);

  def audio_level(self, msg):
    args = msg.args
    if len(args) == 3:
      try:
        max_level = int(args[1])
        cur_level = int(args[2])
        self.state.report_audio_level(max_level, cur_level)
      except ValueError:
        self._warn(args)
    else:
      self._warn(args)

  def audio_pong(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.report_audio_pong()
    else:
      self._warn(args)

  # external commands

  def mute(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_audio_mute(True,True)
    else:
      self._warn(args)

  def unmute(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_audio_mute(False,True)
    else:
      self._warn(args)

  def listen(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_audio_listen(True,True)
    else:
      self._warn(args)

  def unlisten(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_audio_listen(False,True)
    else:
      self._warn(args)

  def chime(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_audio_chime(True,True)
    else:
      self._warn(args)

  def nochime(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_audio_chime(False,True)
    else:
      self._warn(args)

  def blank(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_blank(True,True)
    else:
      self._warn(args)

  def noblank(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.execute_blank(False,True)
    else:
      self._warn(args)

  # xmppbot callbacks

  def connected(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.connected()
    else:
      self._warn(args)

  def disconnected(self, msg):
    args = msg.args
    if len(args) == 1:
      self.state.disconnected()
    else:
      self._warn(args)

  # dispatcher

  valid_commands = {
    'audio_state' : audio_state,
    'audio_level' : audio_level,
    'audio_pong' : audio_pong,
    'mute' : mute,
    'unmute' : unmute,
    'listen' : listen,
    'unlisten' : unlisten,
    'connected' : connected,
    'disconnected' : disconnected,
    'chime' : chime,
    'nochime' : nochime,
    'blank' : blank,
    'noblank' : noblank
  }

  def dispatch(self, msg):
    if len(msg.args) == 0:
      return False
    cmd = msg.args[0]
    for a in self.valid_commands:
      if a == cmd:
        f = self.valid_commands[a]
        return f(self, msg)
    print("huh? ",msg,file=sys.stderr)
    return False
