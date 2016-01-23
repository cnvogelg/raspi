#
# pifon_fon audio module
#
# detect intervals ouf loudness and generate events
# uses SoX' rec tool with ALSA driver for USB WebCam audio
#

from __future__ import print_function

import time
import threading
try:
  import queue
except ImportError:
  import Queue as queue

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
    self.rec = recorder.Recorder(self.sample_rate, self.interval, self.channels, self.rec, self.dev)
    self.sim = simulator.Simulator()

    self.log("init audio")
    self.log("options=",self.botopts.get_values())

    # setup threading
    self.queue = queue.Queue()
    self.thread = threading.Thread(target=self.thread_run, name="audiorec")
    self.do_run = True
    self.thread.start()

  def _get_vumeter_cfg(self, cfg):
    def_cfg = {
      'sample_rate' : 48000,
      'channels' : 1,
      'interval' : 250,
      'recorder' : 'rec',
      'device' : 'mixin',
      'debug' : False,
    }
    vu_cfg = cfg.get_section("vumeter", def_cfg)
    self.log("vumeter=",vu_cfg)
    self.rec = vu_cfg['recorder']
    self.dev = vu_cfg['device']
    self.sample_rate = vu_cfg['sample_rate']
    self.channels = vu_cfg['channels']
    self.interval = vu_cfg['interval']
    self.debug = vu_cfg['debug']
    self.tick_interval = self.interval / 1000.0

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
    return self.tick_interval

  def on_connected(self):
    self.log("CONNECT")
    self.d.set_event_handler(self.ev)
    self.ev.first = True
    self.d.post_state()
    self.d.post_active()

  def on_disconnected(self):
    self.log("DISCONNECT")
    self.d.set_event_handler(None)

  def thread_run(self):
    """audio record thread"""
    self.log("starting audio thread")

    # init
    last_ts = time.time()
    last_alive_ts = last_ts
    tick = int(self.tick_interval * 1000) # convert to ms
    max_rec_delta = 0
    min_rec_delta = 10 * self.interval
    first = True

    # main loop
    while self.do_run:
      # calculate the delta time of our loop
      ts = time.time()
      delta = ts - last_ts
      last_ts = ts
      delta = int(delta * 1000.0) # convert to ms

      # report alive
      alive_delta = ts - last_alive_ts
      if alive_delta > 10:
        self.log("alive! rec_delta=", [min_rec_delta, max_rec_delta])
	max_rec_delta = 0
        min_rec_delta = 10 * self.interval
        last_alive_ts = ts

      # check delta
      if delta > 2 * tick:
        self.log("slow tick is=",delta,"want=",tick)

      # process audio data
      begin = time.time()
      rms = self.rec.read_rms()
      end = time.time()
      rec_d = int((end - begin) * 1000)
      if rms is None:
        return
      level = rms[1]
      rec_delta = rms[0]
      if rec_delta > max_rec_delta:
        max_rec_delta = rec_delta
      if rec_delta < min_rec_delta:
        min_rec_delta = rec_delta

      # check recording delta
      jitter = abs(rec_delta - self.interval)
      jit_prc = int(jitter * 100 / self.interval)
      if jit_prc > 10 or self.debug:
        self.log("jitter=", jitter, jit_prc)

      # replace with sim data
      if self.botopts.get_value('sim'):
        level = self.sim.read_rms()
        tag = "sim"
      else:
        tag = 'rec'

      # print values
      trace = self.botopts.get_value('trace')
      if self.debug or level > 0 or trace:
        self.log(tag, level, "delta", delta, "rec_delta", rec_delta, "of", self.interval, "rec_d", rec_d)

      # finally put result into queue
      if first:
        first = False
      else:
        self.queue.put(level)

  def on_tick(self, ts, delta):
    """tick handler of bot"""
    # check queue size
    size = self.queue.qsize()
    if size == 0:
      self.log("queue empty!")
      return
    elif size > 1:
      self.log("queue size:", size)
      # drain queue
      for i in range(size-1):
        self.queue.get()

    # get next element
    level = self.queue.get()

    # process rms value
    up_state, up_active = self.d.handle_rms(level)
    if up_state is not None:
      self.log("state", up_state, self.d.state_names[up_state])
    if up_active is not None:
      self.log("active", up_active)
