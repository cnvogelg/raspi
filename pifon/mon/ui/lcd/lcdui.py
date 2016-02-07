from __future__ import print_function
import sys

import lcd
import backlight
import ui.widgets

class UI:

  def __init__(self, cfg):
    self.cfg = cfg
    self.lcd = self._setup_lcd()
    self.widgets = []
    # clock
    self.clock = ui.widgets.Clock((0,0))
    self.widgets.append(self.clock)
    # scroller
    self.scroller = ui.widgets.Scroller((0,0),16)
    self.scroller.add_message("pifon2")
    self.scroller.show(False)
    self.widgets.append(self.scroller)
    # alarm group
    self.alarm_group = ui.widgets.Group((0,0),16)
    self.room_label = ui.widgets.Label((0,0),8)
    self.duration_label = ui.widgets.Label((8,0),2,align=ui.widgets.Label.ALIGN_RIGHT)
    self.level_label = ui.widgets.Label((14,0),2,align=ui.widgets.Label.ALIGN_RIGHT)
    self.level_fifo = ui.widgets.Fifo((10,0),4)
    self.alarm_group.add_widget(self.room_label)
    self.alarm_group.add_widget(self.duration_label)
    self.alarm_group.add_widget(self.level_label)
    self.alarm_group.add_widget(self.level_fifo)
    self.alarm_group.show(False)
    self.widgets.append(self.alarm_group)
    # audio - reserve two instances
    a0 = ui.widgets.AudioShow((0,1), 0, self.lcd.bar_chars)
    a1 = ui.widgets.AudioShow((5,1), 1, self.lcd.bar_chars)
    a2 = ui.widgets.AudioShow((10,1), 1, self.lcd.bar_chars)
    self.widgets += [a0,a1,a2]
    self.audio_list = [a0,a1,a2]
    self.audio_map = {}
    self.ping_lost = set()
    self.alarm_audio = None
    # player
    self.player = None
    self.player_active = False
    self.player_show = ui.widgets.PlayerShow((15,1), self._index_mapper, self.lcd.play_char)
    self.widgets.append(self.player_show)
    # backlight
    self.backlight = backlight.Backlight(self.lcd)
    # quit
    self.quit_pending = False

  def _setup_lcd(self):
    def_cfg = {
      'mode' : 'auto',
      'font_path' : 'font'
    }
    lcd_cfg = self.cfg.get_section('ui_lcd', def_cfg)
    font_path = lcd_cfg['font_path']
    mode = lcd_cfg['mode']
    if mode == 'auto':
      sim = lcd.autodetect_sim()
    elif mode == 'sim':
      sim = True
    elif mode == 'hw':
      sim = False
    else:
      raise ValueError("Invalud lcd mode: '%s'" % mode)
    return lcd.LCD16x2(font_path=font_path, sim=sim)

  def _p(self, *args, **kwargs):
    a = ["**UI**"] + list(args)
    print(*a,file=sys.stderr,**kwargs)

  def get_tick_interval(self):
    return 0.25

  def on_tick(self, ts, delta):
    """tick timer for ui. called every 0.25s"""
    # check buttons
    self._handle_buttons()
    # tick update all widgets
    self._tick_widgets(ts, delta)
    # what to show in first line?
    # alarm?
    if self.alarm_audio is not None:
      self.scroller.show(False)
      self.clock.show(False)
      self.alarm_group.show(True)
    elif self.scroller.is_busy():
      # show scroller if its busy
      self.scroller.show(True)
      self.clock.show(False)
      self.alarm_group.show(False)
    else:
      # if nothing todo then show clock
      self.scroller.show(False)
      self.clock.show(True)
      self.alarm_group.show(False)
      # is a quit pending? -> quit now
      if self.quit_pending:
        return False
    # perform redraw
    self._redraw_widgets()

  def on_start(self, nick):
    self.nick = nick
    self.scroller.add_message(nick)

  def on_stop(self, nick):
    # disable lcd
    self.lcd.backlight(self.lcd.OFF)

  def on_connect(self):
    self.scroller.add_message("Connected!")
    self.backlight.set_connected(True)

  def on_disconnect(self):
    self.scroller.add_message("Disconnected:(")
    self.backlight.set_connected(False)

  def on_peer_connect(self, peer):
    self.scroller.add_message("'%s' connected." % peer)

  def on_peer_disconnect(self, peer):
    self.scroller.add_message("'%s' disconnected." % peer)

  def _tick_widgets(self, ts, delta):
    for w in self.widgets:
      w.tick(ts, delta)

  def _clear_screen(self):
    self.lcd.clear()

  def _draw_func(self, pos, txt):
    self.lcd.text(pos[0], pos[1], txt)

  def _redraw_widgets(self, force=False):
    for w in self.widgets:
      w.redraw(self._draw_func)

  def _handle_buttons(self):
    b = self._read_buttons()
    if b is not None:
      self._p("buttons:", b)
      # quit bot?
      if b == 'q' or b == 'rl':
        self.scroller.add_message("shutting down!!")
        self.quit_pending = True

  def _read_buttons(self):
    """return either string with pressed buttons or None if no button
       is pressed"""
    but = self.lcd.buttonRead()
    if but == 0:
      return None
    if but is None:
      return "q"
    res = ""
    if but & self.lcd.BUTTON_SELECT == self.lcd.BUTTON_SELECT:
      res += "s"
    if but & self.lcd.BUTTON_RIGHT == self.lcd.BUTTON_RIGHT:
      res += "r"
    if but & self.lcd.BUTTON_LEFT == self.lcd.BUTTON_LEFT:
      res += "l"
    if but & self.lcd.BUTTON_UP == self.lcd.BUTTON_UP:
      res += "u"
    if but & self.lcd.BUTTON_DOWN == self.lcd.BUTTON_DOWN:
      res += "d"
    return res

  # audio calls

  def audio_add(self, a):
    self._p("audio_add", a)
    # find free slot
    for ai in self.audio_list:
      if ai.get_audio() is None:
        ai.set_audio(a)
        idx = ai.idx
        self.audio_map[a] = ai
        self.scroller.add_message("add %d:%s" % (idx, a.name))
        self._check_ping(a)
        return
    # no slot free
    self.scroller.add_message("skip: " + a.name)

  def audio_del(self, a):
    self._p("audio_del", a)
    if a in self.audio_map:
      ai = self.audio_map[a]
      idx = ai.idx
      del self.audio_map[a]
      ai.set_audio(None)
      self.scroller.add_message("rem %d:%s" % (idx, a.name))
      self._remove_ping(a)
      return
    # no slot assigned
    self.scroller.add_message("lost: " + a.name)

  def audio_update(self, a, flags):
    self._p("audio_update", a)
    if a in self.audio_map:
      ai = self.audio_map[a]
      ai.update()
      self._check_ping(a)
      self._check_alarm_state(a)
      if self.alarm_audio == a:
        self._update_alarm_info(a)

  def _check_alarm_state(self, a):
    state = a.audio_state
    idle = state is None or state == 'idle'
    if self.alarm_audio == a:
      if idle:
        self.alarm_audio = None
    else:
      if not idle:
        self.alarm_audio = a

  def _update_alarm_info(self, a):
      # set room name
      src = a.audio_listen_src
      if src is not None:
        room = src[0]
      else:
        room = None
      self.room_label.set_text(room)
      # set level/duration
      level = a.audio_level
      if level is not None:
        lvl = level[1]
        dur = level[2]
        self.level_fifo.add(self._get_level_char(lvl))
      else:
        lvl = ""
        dur = ""
        self.level_fifo.clear()
      self.level_label.set_text(lvl)
      self.duration_label.set_text(dur)

  def _get_level_char(self, l):
    if l > 8:
      l = 8
    return self.lcd.bar_chars[l]

  def _check_ping(self, a):
    if a.ping == "timeout":
      self.ping_lost.add(a)
    elif a in self.ping_lost:
      self.ping_lost.remove(a)
    self.backlight.set_ping_lost(len(self.ping_lost)>0)

  def _remove_ping(self, a):
    if a in self.ping_lost:
      self.ping_lost.remove(a)

  # player calls

  def _index_mapper(self, ai):
    """map an audio info to a list index"""
    for a in self.audio_list:
      if a.get_audio() == ai:
        return str(a.idx)
    return None

  def _is_my_player(self, name):
    """check if given player is my associated player"""
    return name == self.nick

  def player_add(self, p):
    self._p("player_add", p)
    if self._is_my_player(p.name):
      self.player = p
      self.player_active = p.play_server is not None
      self.player_show.set_player(p)
      self.backlight.set_active(self.player_active)
      # overwrite audio alarm
      if p.play_server != self.alarm_audio:
        self.alarm_audio = p.play_server

  def player_del(self, p):
    self._p("player_del", p)
    if p == self.player:
      self.player = None
      self.player_show.set_player(None)
      self.backlight.set_active(False)

  def player_update(self, p, flags):
    self._p("player_update", p, flags)
    if p == self.player:
      self.player_active = p.play_server is not None
      self.player_show.update()
      self.backlight.set_active(self.player_active)
      # overwrite audio alarm
      if p.play_server != self.alarm_audio:
        self.alarm_audio = p.play_server
