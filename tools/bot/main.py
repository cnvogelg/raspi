#!/usr/bin/env python

from __future__ import print_function
import time
import sys
import importlib
import traceback

from bot.io import BotIO, BotIOMsg
from bot.cmd import BotCmd
from bot.opts import BotOpts
from bot.event import BotEvent

class Bot:
  """main class for a bot instance"""
  def __init__(self, verbose=False):
    self.modules = []
    self.bio = None
    self.nick = None
    self.cmd_name = None
    self.cfg_name = None
    self.cfg_paths = None
    self.verbose = verbose
    self.connected = False
    self.rem_mods = {}

  def add_module(self, module):
    """add a module to the bot"""
    self.modules.append(module)

  def _log(self, *args):
    if self.verbose:
      t = time.time()
      millis = int(t * 1000) % 1000
      a = ["%s.%03d" % (time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(t)), millis)] + list(args)
      print(*a,file=sys.stderr)

  def run(self):
    """run the bot"""
    self._setup()
    self._auto_add_modules()
    self._setup_modules()
    self._setup_cmds()
    self._main_loop()

  def _setup(self):
    self._log("bot: setup")
    self.bio = BotIO(verbose=False)
    self.nick = self.bio.get_nick()
    self.cmd_name = self.bio.get_cmd_name()
    self.cfg_name = self.bio.get_cfg_name()
    self.cfg_paths = self.bio.get_cfg_paths()
    self._log("bot: got nick='%s' cmd_name='%s' cfg_name='%s' cfg_paths=%s" % \
      (self.nick, self.cmd_name, self.cfg_name, self.cfg_paths))

  def _gen_funcs(self, name, other_mod):
    # set reply function for module
    def send(args, to=None):
      self.bio.write_args(args, receivers=to)
      # internal loop back
      if to is None or self.nick in to:
        a = map(str, args)
        msg = BotIOMsg(" ".join(a), self.nick, to, False)
        msg.split_args()
        self._handle_msg(msg, other_mod)

    # set log function
    def log(*args):
      a = [name + ":"] + list(args)
      self._log(*a)

    return send, log

  def _auto_add_modules(self):
    """auto add modules from config"""
    cfg = self.bio.get_cfg()
    def_cfg = {
      'auto_load' : None
    }
    mod_cfg = cfg.get_section("modules", def_cfg)
    auto_load = mod_cfg['auto_load']
    if auto_load:
      mod_list = auto_load.split(',')
      for mod in mod_list:
        # expect package.Class name
        dot = mod.rfind('.')
        if dot == -1:
          raise RuntimeError("Invalid module name: " + mod)
        pkg = mod[:dot]
        clz = mod[dot+1:]
        self._log("bot: auto load module:", pkg, clz)
        # get python module
        pmod = importlib.import_module(pkg)
        pdict = pmod.__dict__
        if clz not in pdict:
          raise RuntimeError("Class '%s' not found in Module '%s'" % (pkg, clz))
        # create instance
        pclz = pdict[clz]
        my_mod = pclz()
        self.modules.append(my_mod)

  def _setup_modules(self):
    if len(self.modules) == 0:
      raise RuntimeError("No modules added!")
    self.bot_tick_interval = 1
    for m in self.modules:
      name = m.get_name()

      # other modules
      other_mod = []
      for m2 in self.modules:
        if m2 != m:
          other_mod.append(m2)

      send, log = self._gen_funcs(name, other_mod)

      # get bot config
      cfg = self.bio.get_cfg()

      # has options?
      opts = m.get_opts()
      bo = None
      if opts is not None:

        def send_mod_event(args, to=None):
          a = [name + ".event"] + args
          send(a, to=to)

        cfg_name = m.get_opts_name()
        bo = BotOpts(send_mod_event, opts, cfg=cfg, cfg_name=cfg_name)

        def field_handler(field):
          self._trigger_internal_event(BotEvent.UPDATE_FIELD, [field], mods=[m])

        bo.set_notifier(field_handler)
        self._log("bot: module",name,"opts:", bo.get_values())

      # setup bot
      m.nick = self.nick
      m.bot = self
      m.setup(send, log, cfg, bo)

      # get tick (after setup of bot)
      tick = m.get_tick_interval()
      self._log("bot: module",name,"tick",tick)
      if tick > 0 and tick < self.bot_tick_interval:
        self.bot_tick_interval = tick

    # report bot tick
    self._log("bot: tick", self.bot_tick_interval)

  def _setup_cmds(self):
    self.cmds = [
      BotCmd("lsmod",callee=self._cmd_lsmod),
      BotCmd("ping",callee=self._cmd_ping)
    ]
    self.events = [
      BotEvent("bot","module",arg_types=(str,str),callee=self._event_bot_module),
      BotEvent("bot","end_module",callee=self._event_bot_end_module)
    ]

  def _cmd_lsmod(self, sender):
    self._log("cmd: lsmod")
    for a in self.modules:
      self._reply(["bot.event", "module", a.get_name(), a.get_version()], to=[sender])
    self._reply(["bot.event", "end_module"], to=[sender])

  def _cmd_ping(self, sender):
    self._reply(["bot.event", "pong"], to=[sender])

  def _get_mod_set(self, sender):
    if sender in self.rem_mods:
      return self.rem_mods[sender]
    else:
      s = {}
      self.rem_mods[sender] = s
      return s

  def _event_bot_module(self, sender, args):
    mod_name = args[0]
    mod_ver = args[1]
    self._log("bot module", sender, mod_name, mod_ver)
    s = self._get_mod_set(sender)
    s[mod_name] = mod_ver

  def _event_bot_end_module(self, sender):
    self._log("bot end_module", sender)
    s = self._get_mod_set(sender)
    # post a peer mod list event
    self._trigger_internal_event(BotEvent.PEER_MOD_LIST, [sender, s])

  def _send_my_mod_list(self):
    s = {}
    for m in self.modules:
      name = m.get_name()
      ver = m.get_version()
      s[name] = ver
    self._trigger_internal_event(BotEvent.MOD_LIST, [s])

  def request_shutdown(self):
    self._log("requesting shutdown")
    self.stay = False

  def _main_loop(self):
    self._init_tick()

    # report start
    self._trigger_internal_event(BotEvent.START)

    tick_delta = self.bot_tick_interval

    self.delta_range = [tick_delta, -tick_delta]
    self.extra_range = [tick_delta, -tick_delta]
    self.show_ts = time.time()

    self.stay = True
    extra = 0
    while self.stay:
      try:
        # handle tick
        b = time.time()
        self._tick()
        e = time.time()

        # calc remaining time in interval to wait
        delta = e - b
        wait = tick_delta - delta - extra
        if wait <= 0.01:
          wait = 0.01

        # handle incoming messages
        real_wait = self._read_dispatch_msgs(wait)
        extra = real_wait - wait

        # internal (debug) accounting
        self._account_delta(b, delta, extra)

      except KeyboardInterrupt:
        self._log("bot: Break")
        break
      except Exception as e:
        self._log("bot: ERROR:", str(e))
        traceback.print_exc(file=sys.stderr)
        break

    # report stop
    self._trigger_internal_event(BotEvent.STOP)

  def _account_delta(self, ts, delta, extra):
    if delta < self.delta_range[0]:
      self.delta_range[0] = delta
    if delta > self.delta_range[1]:
      self.delta_range[1] = delta

    if extra < self.extra_range[0]:
      self.extra_range[0] = extra
    if extra > self.extra_range[1]:
      self.extra_range[1] = extra

    show_delta = ts - self.show_ts
    if show_delta > 10:
      dmi = int(self.delta_range[0] * 1000)
      dma = int(self.delta_range[1] * 1000)
      emi = int(self.extra_range[0] * 1000)
      ema = int(self.extra_range[1] * 1000)
      self._log("dispatch delta:", dmi, dma, " extra:", emi, ema)
      self.show_ts = ts
      # reset ranges
      tick_delta = self.bot_tick_interval
      self.delta_range = [tick_delta, -tick_delta]
      self.extra_range = [tick_delta, -tick_delta]

  def _read_dispatch_msgs(self, timeout):
    start = time.time()
    end = start + timeout
    t = start
    while t < end:
      msg = self.bio.read_args(timeout=timeout)
      if msg:
        if msg.is_internal:
          self._handle_internal_msg(msg)
        else:
          self._handle_msg(msg, self.modules)
      tn = time.time()
      delta = tn - t
      t = tn
      timeout -= delta
      if timeout <= 0:
        break
    return t - start

  def _init_tick(self):
    ts = time.time()
    for m in self.modules:
      m.last_ts = ts

  def _tick(self):
    """call tick in modules"""
    ts = time.time()
    for m in self.modules:
      tick = m.get_tick_interval()
      if tick > 0:
        delta = ts - m.last_ts
        if delta >= tick:
          #self._log("bot: do tick", m.name)
          self._trigger_internal_event(BotEvent.TICK, [ts, delta], mods=[m])
          m.last_ts = ts

  def _reply(self, args, to=None):
    self.bio.write_args(args, receivers=to)

  def _error(self, msg, to):
    self._reply(["bot.event", "error", msg], [to])

  def _handle_internal_msg(self, msg):
    """handle internal message"""
    if msg.int_cmd == 'exit':
      self._log("exit")
      return False
    # connected?
    my_nick = self.bio.get_nick()
    msg_nick = msg.int_nick
    self._log("internal", msg_nick, msg.int_cmd)
    if msg.int_cmd == 'connected':
      if msg.int_nick == my_nick:
        if not self.connected:
          self._log("I am connected")
          self.connected = True
          self._trigger_internal_event(BotEvent.CONNECT)
          # send my mod list
          self._send_my_mod_list()
      else:
        self._trigger_internal_event(BotEvent.PEER_CONNECT, [msg_nick])
        # request module list
        self._reply(['bot','lsmod'], to=[msg_nick])
    # disconnected?
    elif msg.int_cmd == 'disconnected':
      if msg.int_nick == my_nick:
        if self.connected:
          self._log("I am disconnected")
          self.connected = False
          self._trigger_internal_event(BotEvent.DISCONNECT)
      else:
        self._trigger_internal_event(BotEvent.PEER_DISCONNECT, [msg_nick])
    return True

  def _handle_msg(self, msg, modules):
    # get command name
    a = msg.args
    n = len(a)
    to = msg.sender
    # no command given?
    if n < 2:
      self._error("huh?", to)
      return
    # is it a bot command?
    mod_name = a[0]
    cmd_name = a[1]
    if mod_name == 'bot':
      # check internal command
      for cmd in self.cmds:
        if cmd_name == cmd.get_name():
          res = cmd.handle_cmd(a[1:], msg.sender)
          if type(res) is str:
            self._error(cmd_name + ": " + res, to)
            return res
    # is it a module prefix
    for mod in modules:
      if mod_name == mod.get_name():
        # parse module command
        res = self._handle_mod_cmd(mod, a[1:], msg.sender)
        if type(res) is str:
          self._error(cmd_name + ": " + res, to)
          return res
      # is it an event?
      res = self._handle_mod_event(mod.get_events(), a, to)
      if type(res) is str:
        self._error(cmd_name + ": " + res, to)
        return res
    # check for an bot event?
    res = self._handle_mod_event(self.events, a, to)
    if type(res) is str:
      self._error(cmd_name + ": " + res, to)
      return res
    # unknown
    #self._error("Unknown command: " + cmd_name, to)

  def _handle_mod_event(self, events, args, to):
    """handle a module event"""
    if len(args) < 1:
      return False
    # check events
    if events is not None:
      for ev in events:
        if ev.mod_name == args[0] and ev.name == args[1]:
            res = ev.handle_event(args, to)
            if type(res) is str:
              self._error(ev.mod_name + " " + ev.name + ": " + res, to)
              return res

  def _handle_mod_cmd(self, mod, args, to):
    """handle a module command"""
    cmd_name = args[0]
    # check bot commands
    cmds = mod.get_commands()
    if cmds is not None:
      for c in cmds:
        if cmd_name == c.get_name():
          return c.handle_cmd(args, to)
    # check options
    bo = mod.botopts
    if bo is not None:
      res = bo.handle_command(args, to)
      if res is not None:
        return res
    # nothing found
    return "huh? " + cmd_name

  def _trigger_internal_event(self, name, args=None, mods=None):
    if mods is None:
      mods = self.modules
    for mod in mods:
      events = mod.get_events()
      if events is not None:
        for ev in events:
          if ev.mod_name == BotEvent.INTERNAL + ".event" and ev.name == name:
            callee = ev.callee
            if callee is not None:
              if args is None:
                callee()
              else:
                callee(*args)


# ----- test -----
if __name__ == '__main__':
  from mod import BotMod
  bot = Bot(True)
  bm = BotMod("test")
  bot.add_module(bm)
  bot.run()

