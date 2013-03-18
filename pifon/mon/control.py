import time
import menu

class Control:
  """control the monitor from a ui"""
  
  # menu items
  mute_item = menu.BoolMenuItem("mute",False)
  level_item = menu.IntMenuItem("audio", 10, 1, 255)
  update_item = menu.IntMenuItem("update", 2, 1, 100) # in 100ms
  silence_item = menu.IntMenuItem("silence", 5, 1, 100) # in 100ms
  trace_item = menu.BoolMenuItem("trace",False)
  items = [
    mute_item,
    level_item,
    update_item,
    silence_item,
    trace_item
  ]
  update_rate = 250
  
  def __init__(self, ui, say=None):
    self.ui = ui
    self.say = say
    self.menu = menu.Menu(ui, self.items)
    self.in_menu = False
    self.last_muted = False
    self.last_active = False
    self.last_error = None
    self.last_level = 0
    self.last_level_ts = 0
    self._print_state()
  
  def set_muted(self, muted):
    self.muti.item.value = muted
    if self.last_muted != muted:
      self.last_muted = muted
      self._print_state()
  
  def set_active(self, active):
    if self.last_active != active:
      self.last_active = active
      self._print_state()
  
  def set_error(self, error):
    if self.last_error != error:
      self.last_error = error
      self._print_state()
  
  def _print_state(self):
    if self.in_menu:
      return
    if self.last_muted:
      txt = "MUTE "
    else:
      txt = "     "
    if self.last_active:
      txt += "ACTIVE "
    else:
      txt += "------ "
    if self.last_error != None:
      txt += "E%03x" % self.last_error
    self.ui.update_message(txt)
  
  def set_current_level(self, level):
    if level != self.last_level:
      self.last_level = level
      ts = time.time()
      delta = (ts - self.last_level_ts) * 1000
      if delta > self.update_rate:
        self.ui.update_status(level)
        self.last_level_ts = ts
      
  def _leave_menu(self):
    self.in_menu = False
    self.menu.hide()
    self.ui.show_message("")
    self._print_state()
    
  def _enter_menu(self):
    self.in_menu = True
    self.ui.hide_message()
    self.menu.show()
    
  def handle_events(self):
    # inside menu
    if self.in_menu:
      ev = self.menu.handle_next_event()
      if ev == False:
        self._leave_menu()
      elif ev != None:
        val = ev.get_value()
        if ev == self.mute_item:
          if val:
            self.say("mute")
          else:
            self.say("unmute")
        elif ev == self.level_item:
          self.say("set_audio_level %d" % val)
        elif ev == self.update_item:
          self.say("set_audio_update %d" % val)
        elif ev == self.silence_item:
          self.say("set_audio_silence %d" % val)
        elif ev == self.trace_item:
          self.say("set_audio_trace %d" % val)
    # outside menu
    else:
      ev = self.ui.get_next_event()
      if ev & self.ui.EVENT_PICK:
        self._enter_menu()

# ----- test -----
if __name__ == '__main__':
  from lcdui import LCDUI
  import time
  import sys
  import random
  def say(msg):
    sys.stdout.write(msg+"\n")
    sys.stdout.flush()
  c = Control(LCDUI(),say)
  count = 0
  active = False
  muted = False
  error = None
  while True:
    c.handle_events()
    time.sleep(0.1)
    count += 1
    # simulate active
    if count % 23 == 0:
      active = not active
      c.set_active(active)
    # simulate mute
    if count % 13 == 0:
      muted = not muted
      c.set_muted(muted)
    # simulate error
    if count % 37 == 0:
      error = random.randint(0,0xfff)
      if error < 10:
        error = None
      c.set_error(error)
    # simulate level
    if count % 5 == 0:
      level = random.randint(0,256)
      if level == 0:
        level = None
      c.set_level(level)
