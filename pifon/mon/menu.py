#!/usr/bin/env python

class MenuItem:
  def __init__(self, name):
    self.name = name

  def inc(self):
    """perform increment op and return True if value was changed"""
    return False
  
  def dec(self):
    """perform decrement op and return True if value was changed"""
    return False
    
  def show(self, ui):
    ui.show_menu(self.name)
    self.update(ui)
    
  def hide(self, ui):
    ui.hide_menu()
    
  def update(self, ui):
    ui.update_menu_value(self.get_value_str())
    
  def get_value(self):
    return ""
    
  def get_value_str(self):
    return str(self.get_value())
  
class IntMenuItem(MenuItem):
  def __init__(self, name, value, vmin, vmax):
    MenuItem.__init__(self, name)
    self.vmin = vmin
    self.vmax = vmax
    self.value = value
  
  def inc(self):
    if self.value < self.vmax:
      self.value += 1
      return True
    else:
      return False
  
  def dec(self):
    if self.value > self.vmin:
      self.value -= 1
      return True
    else:
      return False
      
  def get_value(self):
    return self.value
  
  def set_value(self, value):
    self.value = value
  
  def __str__(self):
    return "[Int:%s:%d]" % (self.name, self.value)
    
class BoolMenuItem(MenuItem):
  def __init__(self, name, value):
    MenuItem.__init__(self, name)
    self.value = value
    
  def inc(self):
    if not self.value:
      self.value = True
      return True
    else:
      return False
  
  def dec(self):
    if self.value:
      self.value = False
      return True
    else:
      return False
      
  def get_value(self):
    return self.value    
  
  def get_value_str(self):
    if self.value:
      return "on"
    else:
      return "off"

  def set_value(self, value):
    self.value = value
  
  def __str__(self):
    return "[Bool:%s:%d]" % (self.name, self.value)

class Menu:  
  def __init__(self, ui, items):
    self.ui = ui
    self.items = items
    self.current_item = None
    self.pos = 0
    self.shown = False
  
  def get_current_item(self):
    return self.current_item
  
  def show(self):
    """show menu and begin handling events for menu"""
    self.pos = 0
    self.current_item = self.items[self.pos]
    self.current_item.show(self.ui)
    self.shown = True
  
  def hide(self):
    """hide menu and end handling events for menu"""
    self.current_item.hide(self.ui)
    self.shown = False
    self.current_item = None
    
  def update_current_item(self):
    if self.current_item != None:
      self.current_item.show(self.ui)
  
  def handle_next_event(self):
    """handle input events and return menu item if something has changed. 
    return None if nothign happened or False if menu wants to be left"""
    if not self.shown:
      return None
    # poll next event from ui
    ev = self.ui.get_next_event()
    changed = False
    # change current value
    if ev & self.ui.EVENT_INC:
      changed = self.current_item.inc()
    elif ev & self.ui.EVENT_DEC:
      changed = self.current_item.dec()
    # change item
    elif ev & self.ui.EVENT_NEXT:
      self.pos += 1
      if self.pos == len(self.items):
        self.pos = 0
      self.current_item = self.items[self.pos]
      self.current_item.show(self.ui)
    elif ev & self.ui.EVENT_PREV:
      if self.pos == 0:
        self.pos = len(self.items) - 1
      else:
        self.pos -= 1
      self.current_item = self.items[self.pos]
      self.current_item.show(self.ui)
    # leave menu?
    elif ev & self.ui.EVENT_PICK:
      return False
    # return changed value
    if changed:
      self.current_item.update(self.ui)
      return self.current_item
    else:
      return None

# test
if __name__ == '__main__':
  from lcdui import LCDUI
  import time
  
  print("Menu test")
  ui = LCDUI()
  entries = [
      BoolMenuItem("bool",True),
      IntMenuItem("a",10,0,100),
      IntMenuItem("b",0,0,10)
  ]
  menu = Menu(ui, entries)
  menu.show()
  while True:
    ev = menu.handle_next_event()
    if ev == False:
      break
    elif ev != None:
      print ev
    time.sleep(0.1)
  menu.hide()
