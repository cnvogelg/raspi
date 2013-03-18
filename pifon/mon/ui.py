class UI:
  """generic interface class for user interface implementations"""
  
  EVENT_PREV = 1
  EVENT_NEXT = 2
  EVENT_INC  = 4
  EVENT_DEC  = 8
  EVENT_PICK = 16
  
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

  def update_status(self, status):
    """update the status bar"""
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
