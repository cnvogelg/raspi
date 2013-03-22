class Writer:
  """write bot commands"""
  
  def __init__(self, bio):
    self.bio = bio
  
  def send_query_audio(self):
    self.bio.write_line('get audio *')
  
  def send_audio_mute(self, on):
    if on:
      self.bio.write_line('mute')
    else:
      self.bio.write_line('unmute')

  def send_audio_listen(self, on):
    if on:
      self.bio.write_line('listen')
    else:
      self.bio.write_line('unlisten')
  
  def send_audio_option(self, key, val):
    args = [ "set","audio", key , str(val) ]
    self.bio.write_args(args)

  def send_audio_ping(self):
    self.bio.write_line('audio_ping')
    
  def send_audio_state(self):
    self.bio.write_line('audio_state')
