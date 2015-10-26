from __future__ import print_function
import time
import menu
import sys
import time

class Control:
  """control the monitor from a ui"""
  update_rate = 250 # in ms
  blank_delay = 10 # s
  autohide_delay = 5000 # in ms

  def __init__(self, ui, state, opts, desc):
    self.ui = ui
    self.state = state
    self.items = self._create_menu(opts, desc)
    self.menu = menu.Menu(ui, self.items)
    self.in_menu = False
    self.last_level = ""
    self.last_level_ts = 0
    self.audio_state = "init"
    self.last_button_ts = None
    self.is_blanking = False
    self.last_backlight = self.ui.BACK_OFF
    self.allow_blank = True
    self.allow_chime = True
    self.ping_state = None
    self.ping_step = 0
    self.restart_ts = None
    # state
    self.is_connected = False
    self.is_audio_active = False
    self.is_audio_muted = False
    self.is_audio_playing = False
    self.is_audio_listen = False
    self._print_state()
    self._print_title()
    self._print_value()

  def _create_menu(self, opts, desc):
    result = []
    for key in opts:
      value = opts[key]
      t = type(value)
      if t == int:
        d = desc[key]
        m = menu.IntMenuItem(key, value, d[1], d[2])
      elif t == bool:
        m = menu.BoolMenuItem(key, value)
      result.append(m)
    return result

  def shutdown(self):
    self.ui.shutdown()

  # ----- update state calls -----

  def _print_title(self):
    # get time and display clock
    tim = time.time()
    t = time.localtime(tim)
    hour = t[3]
    mins = t[4]
    txt = "%02d:%02d " % (hour, mins)
    # ping state
    if self.ping_state == None:
      txt += " "
    elif self.ping_state == False:
      txt += "!"
    else:
      txt += "."
    self.ui.update_title(txt)
    self._update_back()

  def _update_back(self):
    if self.is_blanking:
      back = self.ui.BACK_OFF
    else:
      # yellow if force no blank
      if not self.allow_blank:
        back = self.ui.BACK_YELLOW
      # white is default color
      else:
        back = self.ui.BACK_WHITE

      # overwrite if state
      if self.is_connected:
        if self.is_audio_active:
          if self.is_audio_playing:
            back = self.ui.BACK_GREEN
          else:
            back = self.ui.BACK_RED
      else:
        back = self.ui.BACK_BLUE

    if back != self.last_backlight:
      self.last_backlight = back
      self.ui.update_background(back)

  def update_audio_ping(self, ping_state):
    """state of pinging the audio server: None=send ping, True=does ping, False=no ping"""
    self.ping_state = ping_state
    self._print_title()

  def update_audio_state(self, audio_state, is_audio_active, is_connected):
    self.audio_state = audio_state
    self.is_audio_active = is_audio_active
    self.is_connected = is_connected
    self._print_state()
    self._update_blanking()

  def update_mon_state(self, is_audio_muted, is_audio_listen, allow_chime, allow_blank):
    self.is_audio_muted = is_audio_muted
    self.is_audio_listen = is_audio_listen
    self.allow_chime = allow_chime
    self.allow_blank = allow_blank
    self._print_state()
    self._update_blanking()

  def update_audio_play(self, is_audio_playing):
    self.is_audio_playing = is_audio_playing
    self._print_state()

  def _print_state(self):
    if self.in_menu:
      return
    # audio state
    txt = "%7s " % self.audio_state
    # play state
    if self.is_audio_playing:
      txt += "PLAY"
    else:
      txt += "stop"
    # mon state
    if self.is_audio_muted:
      txt += " M"
    else:
      txt += "  "
    if self.is_audio_listen:
      txt += "L"
    else:
      txt += " "
    if self.allow_chime:
      txt += "*"
    else:
      txt += " "
    self.ui.update_message(txt)
    self._update_back()

  def update_audio_level(self, max_level, cur_level):
    """audio level changed"""
    level = "%03d %03d" % (max_level, cur_level)
    ts = time.time()
    if level != self.last_level:
      self.last_level = level
      delta = (ts - self.last_level_ts) * 1000
      if delta > self.update_rate:
        self._print_value()
    self.last_level_ts = ts

  def _autohide_levels(self):
    if self.last_level != "":
      ts = time.time()
      delta = (ts -self.last_level_ts) * 1000
      if  delta > self.autohide_delay:
        self.last_level = ""
        self._print_value()
        self.last_level_ts = ts

  def _print_value(self):
    self.ui.update_status(self.last_level)

  def _leave_menu(self):
    self.in_menu = False
    self.menu.hide()
    self.ui.show_message("")
    self._print_state()
    self._update_blanking(True)

  def _enter_menu(self):
    self.in_menu = True
    self.ui.hide_message()
    self.menu.show()

  def handle_events(self):
    self._autohide_levels()
    exit_flag = None
    # inside menu
    if self.in_menu:
      item = self.menu.handle_next_event()
      if item == False:
        self._leave_menu()
      elif item is not None:
        self._handle_menu_item(item)
    # outside menu
    else:
      ev = self.ui.get_next_event()
      if ev is None:
        return True
      munged = self._update_blanking(ev != 0)
      if not munged:
        exit_flag = self._handle_direct_key(ev)
    return exit_flag

  def update_audio_option(self, key, value):
    """set an audio option from bot"""
    item = None
    for i in self.items:
      if i.name == key:
        i.set_value(value)
        item = i
    # is currently shown?
    if self.in_menu and item == self.menu.get_current_item():
      self.menu.update_current_item()

  def _handle_menu_item(self, item):
    """set an audio option from menu"""
    self.state.set_audio_option(item.name, item.get_value(), False)

  def _handle_direct_key(self, ev):
    """some key outside of menu was pressed"""
    # check for restart combo
    ok = self._check_restart(ev)
    if ok == True:
      return True
    elif ok == False:
      return None

    if ev & self.ui.EVENT_PICK:
      # enter menu
      self._enter_menu()
    elif ev & self.ui.EVENT_NEXT:
      # toggle mute
      on = not self.state.is_audio_muted
      self.state.execute_audio_mute(on, False)
    elif ev & self.ui.EVENT_PREV:
      # toggle listen
      on = not self.state.is_audio_listen
      self.state.execute_audio_listen(on, False)
    elif ev & self.ui.EVENT_DEC:
      # toggle no/blank
      on = not self.allow_blank
      self.state.execute_blank(on, False)
    elif ev & self.ui.EVENT_INC:
      # toggle no/chime
      on = not self.allow_chime
      self.state.execute_audio_chime(on, False)
    return None

  def _check_restart(self, ev):
    """key if restart key was pressed long enough"""
    restart_combo = self.ui.EVENT_DEC | self.ui.EVENT_INC
    pressed = (ev & restart_combo) == restart_combo
    if pressed:
      ts = time.time()
      if self.restart_ts == None:
        self.restart_ts = ts
      else:
        delta = (ts - self.restart_ts)
        print("restart delta",delta,file=sys.stderr)
        if delta > 1: # 1s triggers restart
          self.ui.show_message("--> RESTART <--")
          return True
      return False
    elif ev != 0:
      # any other combo resets
      print("no restart",file=sys.stderr)
      self.restart_ts = None
    return None

  def _update_blanking(self, any_key=None):
    """check if blanking state has changed"""
    new_blanking = self.is_blanking

    # init ts on startup
    if self.last_button_ts == None:
      self.last_button_ts = time.time()

    # a key press was reported
    if any_key == True:
      # disable any blanking
      new_blanking = False
      self.last_button_ts = None

    # no key press was reported
    elif any_key == False:
      # wait
      delay = (time.time() - self.last_button_ts)
      if delay >= self.blank_delay:
        new_blanking = True

    # allow blanking only in some states
    if self.audio_state not in ('idle','init','online'):
      new_blanking = False

    # blanking not allowed by user
    if not self.allow_blank:
      new_blanking = False

    # changed blanking?
    if new_blanking != self.is_blanking:
      print("blanking: ",self.is_blanking,file=sys.stderr)
      self.is_blanking = new_blanking
      self._update_back()
      return True
    else:
      return False

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
