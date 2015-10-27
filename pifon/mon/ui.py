class UI:
  """generic interface class for user interface implementations"""

  EVENT_PREV = 1
  EVENT_NEXT = 2
  EVENT_INC  = 4
  EVENT_DEC  = 8
  EVENT_PICK = 16

  BACK_OFF = 0
  BACK_WHITE = 1
  BACK_RED = 2
  BACK_GREEN = 3
  BACK_BLUE = 4
  BACK_YELLOW = 5
  BACK_TEAL = 6
  BACK_VIOLET = 7

  def shutdown(self):
    """shutdown all"""
    pass

  def get_next_event(self):
    """return the next event or 0 if no event occurred"""
    pass

  def show_menu(self, title, value):
    """start showing a menu"""
    pass

  def hide_menu(self):
    pass

  def update_clock(self, hours, mins, secs):
    pass

  def update_audio_ping(self, ping):
    pass

  def update_audio_state(self, state, is_audio_active, is_connected):
    pass

  def update_audio_play(self, is_audio_playing):
    pass

  def update_audio_levels(self, max_value, cur_value, hide):
    pass

  def update_mon_state(is_audio_muted, is_audio_listen, allow_chime, allow_blank):
    pass

  def update_menu_value(self, value):
    """update a value change in the menu"""
    pass

  def update_background(self, back):
    """update background"""
    pass

  def show_message(self, msg):
    """if no menu is shown then you can show a message"""
    pass
