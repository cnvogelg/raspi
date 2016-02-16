
class AudioInfo:

  FLAG_PING = 1
  FLAG_AUDIO_LEVEL = 2
  FLAG_AUDIO_STATE = 4
  FLAG_AUDIO_ACTIVE = 8
  FLAG_AUDIO_LISTEN_URL = 16
  FLAG_AUDIO_LOCATION = 32
  FLAG_IS_PLAYING = 64
  FLAG_ALL = 127

  def __init__(self, name):
    self.name = name
    self.ping = None
    self.audio_level = None
    self.audio_state = None
    self.audio_active = None
    self.audio_listen_url = None
    self.audio_location = None
    self.is_playing = False

  def is_ready(self):
    return self.audio_state is not None and \
           self.audio_active is not None and \
           self.audio_location is not None and \
           self.audio_listen_url is not None

  def __repr__(self):
    return "[%s:ping=%s,audio=(level=%s,state=%s,active=%s,listen_url=%s,location=%s)],play=%s" % (self.name,
      self.ping,
      self.audio_level, self.audio_state, self.audio_active,
      self.audio_listen_url, self.audio_location,
      self.is_playing)
