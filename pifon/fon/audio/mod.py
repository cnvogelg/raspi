#
# pifon_fon audio module
#
# detect intervals ouf loudness and generate events
# uses SoX' rec tool with ALSA driver for USB WebCam audio
#

from __future__ import print_function

import time
from bot import Bot, BotCmd, BotOptField, BotMod
from bot.event import *

import detector
import recorder
import simulator


class DetectorEventHandler:
  def __init__(self, reply, botopts):
    self.reply = reply
    self.botopts = botopts
    self.first = True

  def state(self, state):
    # write audio_state
    self.reply(["state", state])

  def active(self, active):
    # send source info before attack
    if active or self.first:
      name = self.botopts.get_value('src_name')
      url = self.botopts.get_value('listen_url')
      self.reply(["listen_src",name,url])
      self.first = False
    # write active state
    self.reply(["active", active])

  def level(self, max_level, cur_level, duration):
    self.reply(["level", max_level, cur_level, duration])


class AudioMod(BotMod):
  def __init__(self):
    BotMod.__init__(self, "audio")
    self.cmds = [
      BotCmd("ping",callee=self.cmd_ping),
      BotCmd("query_state",callee=self.cmd_query_state),
      BotCmd("query_active",callee=self.cmd_query_active)
    ]
    listen_url = 'http://your_server.com:8000/pifon.m3u'
    src_name = 'Maja+Willi'
    self.opts = [
      BotOptField('sim', bool, False, desc='enable level simulator'),
      BotOptField('trace', bool, False, desc='enable level tracing'),
      BotOptField('listen_url', str, listen_url, desc='url of audio stream'),
      BotOptField('src_name', str, src_name, desc='name of audio source'),
      BotOptField('alevel', int, 1, val_range=[1,100], desc='audio level to reach in attack phase [1-100]'),
      BotOptField('slevel', int, 1, val_range=[1,100], desc='audio level to stay below in sustain phase [1-100]'),
      BotOptField('attack', int, 0, val_range=[1,10], desc='period [1s] of loudness required to start playback'),
      BotOptField('sustain', int, 5, val_range=[0,60], desc='period [1s] of silence required to stop playback'),
      BotOptField('respite', int, 10, val_range=[0,60], desc='delay [1s] after playback to wait for next'),
      BotOptField('update', int, 5, val_range=[1,60], desc='update interval of current peak level [100ms]')
    ]
    self.events = [
      ConnectEvent(self.on_connected),
      DisconnectEvent(self.on_disconnected),
      TickEvent(self.on_tick)
    ]

  def setup(self, reply, log, cfg, botopts):
    BotMod.setup(self, reply, log, cfg, botopts)
    self._get_vumeter_cfg(cfg)

    self.ev = DetectorEventHandler(self.reply, self.botopts)
    self.d = detector.Detector(self.botopts)
    self.rec = recorder.Recorder(self.sample_rate, self.interval, self.channels, self.rec)
    self.sim = simulator.Simulator()

    self.log("init audio")
    self.log("options=",self.botopts.get_values())
    self.last_ts = time.time()

  def _get_vumeter_cfg(self, cfg):
    def_cfg = {
      'sample_rate' : 11025,
      'channels' : 1,
      'interval' : 250,
      'recorder' : 'auto',
      'debug' : False
    }
    vu_cfg = cfg.get_section("vumeter", def_cfg)
    self.log("vumeter=",vu_cfg)
    self.rec = vu_cfg['recorder']
    self.sample_rate = vu_cfg['sample_rate']
    self.channels = vu_cfg['channels']
    self.interval = vu_cfg['interval']
    self.debug = vu_cfg['debug']

  # ----- commands -----

  def cmd_ping(self, sender):
    self.reply(["pong"], to=[sender])

  def cmd_query_state(self, sender):
    self.reply(["state", self.d.get_state_name()], to=[sender])

  def cmd_query_active(self, sender):
    self.reply(["active", self.d.is_active()], to=[sender])

  def get_commands(self):
    return self.cmds

  def get_opts(self):
    return self.opts

  def get_events(self):
    return self.events

  # ----- tick -----

  def get_tick_interval(self):
    return self.interval / 1000.0

  def on_connected(self):
    self.log("CONNECT")
    self.d.set_event_handler(self.ev)
    self.ev.first = True
    self.d.post_state()
    self.d.post_active()

  def on_disconnected(self):
    self.log("DISCONNECT")
    self.d.set_event_handler(None)

  def on_tick(self, ts, delta):
    # process audio data
    rms = self.rec.read_rms()
    if rms is None:
      return
    level = rms[1]
    delta = rms[0]
    ts = time.time()
    delta_ts = ts - self.last_ts
    delta_ts = int(delta_ts * 1000)
    last_ts = ts

    # replace with sim data
    if self.botopts.get_value('sim'):
      level = self.sim.read_rms()
      tag = "sim"
    else:
      tag = 'rec'

    # print values
    if self.debug or level > 0:
      self.log(tag, level, delta, self.interval, delta_ts)

    # process rms value
    up_state, up_active = self.d.handle_rms(level)
    if up_state is not None:
      self.log("state", up_state)
    if up_active is not None:
      self.log("active", up_active)
