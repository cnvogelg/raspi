class Writer:
  """write bot commands"""
  
  def __init__(self, bio):
    self.bio = bio
  
  def send_query_audio(self):
    self.bio.write_line('query_audio')
  
  def send_audio_mute(self, on):
    if on:
      self.bio.write_line('mute')
    else:
      self.bio.write_line('unmute')
  
  def send_audio_option(self, key, val):
    args = [ "set_audio_" + key , str(val) ]
    self.bio.write_args(args)
