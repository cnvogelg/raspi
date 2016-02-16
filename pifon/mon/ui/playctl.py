

class PlayerControl:

  def __init__(self, send_command, log):
    self.send_command = send_command
    self.log = log

  def toggle_listen(self, player, audio_list):
    if player.play_server is None:
      if len(audio_list) > 0:
        new = audio_list[0]
      else:
        new = None
    else:
      # find next audio entry
      pos = 1
      for a in audio_list:
        if a == player.play_server:
          break
        pos += 1
      if pos == len(audio_list):
        new = None
      else:
        new = audio_list[pos]
    if new:
      self.send_command(['player', 'listen', new.name], to=[player.name])
    else:
      self.send_command(['player', 'monitor'], to=[player.name])

  def toggle_mute(self, player):
    if player.mode == 'mute':
      cmd = 'monitor'
    else:
      cmd = 'mute'
    self.send_command(['player', cmd], to=[player.name])

  def toggle_chime(self, player):
    if player.chime:
      new = False
    else:
      new = True
    self.send_command(['player', 'chime', str(new)], to=[player.name])
