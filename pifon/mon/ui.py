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
  
  def update_menu_value(self, value):
    """update a value change in the menu"""
    pass

  def update_title(self, title):
    """update the title message"""
    pass

  def update_status(self, status):
    """update the status bar"""
    pass

  def update_background(self, back):
    """update background"""
    pass

  def show_message(self, msg):
    """if no menu is shown then you can show a message"""
    pass
  
  def update_message(self, msg):
    """after the message is shown then update it now"""
    pass
  
  def hide_message(self):
    """if a message is shown then hide it"""
    pass
