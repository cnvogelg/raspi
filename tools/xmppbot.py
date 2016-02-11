#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  xmppbot - attach a process as bot XMPP client

  stdin of process is fed with incoming messages adressed with <name>:
  stdout of process is received and print as messages
"""

from __future__ import print_function

import sys
import os
import logging
import argparse
import time

import sleekxmpp
import threading
try:
  import queue
except ImportError:
  import Queue as queue
import subprocess
import select

import socket

import bot.cfg

# ----- ProcRunner -----

class ProcRunner:
  def __init__(self, cmd):
    self.cmd = cmd
    self.in_queue = queue.Queue()
    self.stop_flag = False
    self.proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stdin=subprocess.PIPE,bufsize=0)
    self.output = None
    self.old_data = ""

  def set_output(self, output):
    self.output = output

  def put(self, line):
    self.in_queue.put(line)

  def process(self, timeout=0.1):
    stdout = self.proc.stdout
    stdin  = self.proc.stdin
    # update return code
    self.proc.poll()
    ret = self.proc.returncode
    if ret is not None:
      return ret
    # check for input/output
    (r,w,x) = select.select([stdout],[],[],timeout)
    if stdout in r:
      # read data
      data = stdout.readline()
      line = data.decode()
      self.output.put(line)
    # something to write to stdout?
    try:
      line = self.in_queue.get(False)
      line += '\n'
      data = line.encode()
      stdin.write(data)
      stdin.flush()
    except queue.Empty:
      pass

  def is_running(self):
    self.proc.poll()
    return self.proc.returncode is None

  def end(self):
    self.proc.terminate()

# ----- XMPP Bot -----

class ProcBot(sleekxmpp.ClientXMPP):
  def __init__(self, jid, password, room, nick, filter_nick=True):
    sleekxmpp.ClientXMPP.__init__(self, jid, password)

    self.in_room = False
    self.room = room
    self.nick = nick
    self.filter_nick = filter_nick
    self.queue = queue.Queue()
    self.is_stopped = False

    self.add_event_handler("session_start", self.start)
    self.add_event_handler("session_stop", self.stop)
    self.add_event_handler("groupchat_message", self.muc_message)
    self.add_event_handler("muc::%s::got_online" % self.room,
                           self.muc_online)
    self.add_event_handler("muc::%s::got_offline" % self.room,
                           self.muc_offline)

    self.register_plugin('xep_0030') # Service Discovery
    self.register_plugin('xep_0045') # Multi-User Chat
    self.register_plugin('xep_0199') # XMPP Ping

  def set_output(self, output):
    self.output = output

  def start(self, event):
    self.getRoster()
    self.sendPresence()
    self.plugin['xep_0045'].joinMUC(self.room,
                                    self.nick,
                                    # password=the_room_password,
                                    wait=True)

  def stop(self, event):
    self.is_stopped = True

  def muc_message(self, msg):
    got_nick = msg['mucnick']
    body = msg['body']
    if got_nick != self.nick:
      logging.info("bot: got nick=%s,line='%s'" % (got_nick, body))
      # receiver[,receiver]|text
      valid = not self.filter_nick
      pos = body.find('|')
      if pos != -1:
        addrs = body[0:pos].split(',')
        for addr in addrs:
          # check addr
          if addr == self.nick:
            valid = True
      else:
        # no receiver
        body = "|" + body
        valid = True
      # post message to stdout
      if valid:
        # prefix line with sender
        body = got_nick + ';' + body
        self.output.put(body)

  def muc_online(self, presence):
    nick = presence['muc']['nick']
    # write a 'connected' message to output
    self.send_internal("connected " + nick)
    if nick == self.nick:
      self.in_room = True
      logging.info("bot: enter room")
      # empty queue
      try:
        while True:
          msg = self.queue.get(False)
          self.put(msg)
      except queue.Empty:
        pass

  def muc_offline(self, presence):
    nick = presence['muc']['nick']
    if nick == self.nick:
      self.in_room = False
      logging.info("bot: left room")
    # write a 'disconnected' message to output
    self.send_internal("disconnected " + nick)

  def put(self, msg):
    if self.in_room:
      logging.info("bot: put msg='%s'" % msg)
      self.send_message(mto=self.room, mbody=msg, mtype='groupchat')
    else:
      logging.info("bot: queue msg='%s'" % msg)
      self.queue.put(msg)

  def send_internal(self, msg):
    logging.info("bot: put internal msg='%s'" % msg)
    self.output.put("%s;|%s" % (self.nick, msg))

# ----- main -----

def parse_args():
  parser = argparse.ArgumentParser(description="XMPP bot for external programs")
  parser.add_argument('cmd', nargs='+', help="command with optional arguments to launch")
  parser.add_argument('-v', '--verbose', action='store_true', default=False, help="be more verbos")
  parser.add_argument('-d', '--debug', action='store_true', default=False, help="show debug output")
  parser.add_argument('-c', '--config-file', action='store', default=None, help="name of config file")
  parser.add_argument('-C', '--config-name', action='store', default=None, help="name of program used for configuration")
  parser.add_argument('-f', '--no-filter', action='store_false', default=True, help="disable nick name filter")
  # overwrite config options
  parser.add_argument('-n', '--nick', default=None, help="set nick name")
  parser.add_argument('-p', '--password', default=None, help="set password")
  parser.add_argument('-j', '--jid', default=None, help="set jabber id")
  parser.add_argument('-r', '--room', default=None, help="set room name")
  parser.add_argument('-a', '--address', default=None, help="set jabber server host address")
  args = parser.parse_args()
  return args

def get_cmd_name(cmd):
  name = os.path.basename(cmd)
  pos = name.rfind('.')
  if pos > 0:
    name = name[:pos]
  return os.path.join(os.path.dirname(cmd), name)

# default 'xmppbot' config section
def_cfg = {
  'nick' : None,
  'password' : None,
  'jid' : None,
  'room' : None,
  'address' : None
}

def overlay_cfg_args(cfg, args):
  for field in ('nick', 'password', 'jid', 'room', 'address'):
    val = getattr(args, field)
    if val is not None:
      cfg[field] = val

def check_cfg(cfg):
  for field in ('nick', 'password', 'jid', 'room'):
    if cfg[field] is None:
      return "No '%s' given!" % field
  return None

if __name__ == '__main__':
  # parse command line arguments
  args = parse_args()
  cmd = args.cmd

  cmd_name = get_cmd_name(cmd[0])

  # load config for parameters
  cfg_name = args.config_name
  if cfg_name is None:
    cfg_name = cmd_name
  bot_cfg = bot.cfg.BotCfg(cfg_name, force_cfg_file=args.config_file)
  path = bot_cfg.load()
  if path is not None:
    print("xmppbot config loaded from:",path,file=sys.stderr)
  cfg = bot_cfg.get_section("xmppbot", def_cfg)

  # overwrite config with arguments
  overlay_cfg_args(cfg, args)

  # check config
  error = check_cfg(cfg)
  if error is not None:
    print("config error:",error,file=sys.stderr)
    sys.exit(1)

  # setup logging
  log=logging.ERROR
  if args.verbose:
    log=logging.INFO
  if args.debug:
    log=logging.DEBUG
  logging.basicConfig(level=log,
                      format='%(levelname)-8s %(message)s')

  # check cmd
  if not os.path.exists(cmd[0]):
    print("command not found:",cmd[0],file=sys.stderr)
    sys.exit(2)

  # show config
  print("xmppbot config: ",cfg,file=sys.stderr)

  # setup proc bot
  pr = ProcRunner(cmd)

  # setup nick
  host = socket.gethostname()
  pos = host.find('.')
  if pos != -1:
    host = host[0:pos]
  nick = cfg['nick'] + "@" + host

  # prepare bot options
  jid = cfg['jid']
  pw = cfg['password']
  room = cfg['room']
  addr = cfg['address']
  if addr is not None:
    addr = (addr, 5222)
  no_filter = args.no_filter

  # main loop
  stay = True
  while stay:
    try:
      bot = ProcBot(jid, pw, room, nick, no_filter)
      bot.set_output(pr)
      pr.set_output(bot)

      # send init
      bot.send_internal("init " + cmd_name + " " + path)
      pr.process()

      # connect bot
      logging.info("bot: connecting...")
      if bot.connect(address=addr):
        bot.send_internal("connected "+nick)
        logging.info("bot: connected")
        try:
          bot.process(block=False)
          # main loop
          while stay:
            ret = pr.process()
            if ret is not None:
              print("Process ended with ret=",ret,file=sys.stderr)
              stay = False
              break
        # user wants to abort
        except KeyboardInterrupt:
          print("***Break***",file=sys.stderr)
          stay = False
        except Exception as e:
          print("ERROR: ",e,file=sys.stderr)
          # report to process
          bot.send_internal("disconnected "+nick)
          # retry...
      else:
        print("Unable to connect!",file=sys.stderr)
        break
    except KeyboardInterrupt:
      print("***Break",file=sys.stderr)
      break
    except Exception as e:
      print("ERROR:",e,file=sys.stderr)
    finally:
      logging.info("bot: disconnect")
      bot.disconnect()

  # shutdown proc?
  if pr.is_running():
    logging.info("bot: end proc")
    pr.end()

  logging.info("bot: done")
