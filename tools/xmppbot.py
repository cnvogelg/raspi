#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  xmppbot - attach a process as bot XMPP client

  stdin of process is fed with incoming messages adressed with <name>:
  stdout of process is received and print as messages
"""

import sys
import os
import logging
import argparse
import configparser
import time

import sleekxmpp
import threading
import queue
import subprocess
import select

import socket

# ----- ProcRunner -----

class ProcRunner(threading.Thread):
  def __init__(self, cmd, output):
    threading.Thread.__init__(self, name="proc_runner")
    self.cmd = cmd
    self.in_queue = queue.Queue()
    self.stop_flag = False
    self.output = output

  def put(self, line):
    self.in_queue.put(line)

  def stop(self):
    self.proc.poll()
    if self.proc.returncode == None:
      self.proc.terminate()
    self.join()

  def run(self):
    try:
      self.proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
      stdout = self.proc.stdout
      stdin  = self.proc.stdin
      while self.proc.returncode == None:
        # update return code
        self.proc.poll()
        # check for input/output
        (r,w,x) = select.select([stdout],[],[],0.1)
        if stdout in r:
          # something to read from stdin
          data = stdout.readline().strip()
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
    except KeyboardInterrupt:
      print("bork!")
    except Exception:
      pass
    logging.info("bot: disconnecting after process death...")
    self.output.disconnect(wait=True)
    logging.info("bot: disconnecting done.")

# ----- XMPP Bot -----

class ProcBot(sleekxmpp.ClientXMPP):
  def __init__(self, jid, password, room, nick, filter_nick=True):
    sleekxmpp.ClientXMPP.__init__(self, jid, password)

    self.in_room = False
    self.room = room
    self.nick = nick
    self.filter_nick = filter_nick
    self.queue = queue.Queue()

    # add hostname to nick automatically
    host = socket.gethostname()
    pos = host.find('.')
    if pos != -1:
      host = host[0:pos]
    self.nick_host = nick + "@" + host

    self.add_event_handler("session_start", self.start)
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
                                    self.nick_host,
                                    # password=the_room_password,
                                    wait=True)
    self.send_internal("init")

  def muc_message(self, msg):
    got_nick = msg['mucnick']
    body = msg['body']
    if got_nick != self.nick_host:
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
          elif addr == self.nick_host:
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
    if nick == self.nick_host:
      self.in_room = True
      logging.info("bot: enter room")
      # empty queue
      try:
        while True:
          msg = self.queue.get(False)
          self.put(msg)
      except queue.Empty:
        pass
    # write a 'connected' message to output
    self.send_internal("connected " + nick)

  def muc_offline(self, presence):
    nick = presence['muc']['nick']
    if nick == self.nick_host:
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
    self.output.put("%s;|%s" % (self.nick_host, msg))

# ----- main -----

def parse_args():
  parser = argparse.ArgumentParser(description="XMPP bot for external programs")
  parser.add_argument('cmd', nargs='+', help="command with optional arguments to launch")
  parser.add_argument('-v', '--verbose', action='store_true', default=False, help="be more verbos")
  parser.add_argument('-d', '--debug', action='store_true', default=False, help="show debug output")
  parser.add_argument('-c', '--config-file', action='store', default=None, help="name of config file")
  parser.add_argument('-f', '--no-filter', action='store_false', default=True, help="disable nick name filter")
  args = parser.parse_args()
  return args

def parse_config(file_name):
  parser = configparser.SafeConfigParser()
  parser.read([file_name])
  if parser.has_section('xmppbot'):
    cfg = dict(parser.items('xmppbot'))
    req = ('nick','password','jid','room')
    for r in req:
      if r not in cfg:
        raise ValueError(r + " is missing in config")
    opt = ('address',)
    for o in opt:
      if o not in cfg:
        cfg[o] = None
    return cfg
  else:
    raise ValueError("section 'xmppbot' missing in config")

if __name__ == '__main__':
  # parse command line arguments
  args = parse_args()
  cmd = args.cmd

  # load config for parameters
  config_file = args.config_file
  if config_file == None:
    config_file = cmd[0] + '.cfg'
  if not os.path.exists(config_file):
    print("no config file:",config_file,file=sys.stderr)
    sys.exit(1)
  cfg = parse_config(config_file)

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
  print("config: ",cfg,file=sys.stderr)

  # setup proc bot
  bot = ProcBot(cfg['jid'], cfg['password'], cfg['room'], cfg['nick'],
                args.no_filter)
  pr = ProcRunner(cmd, bot)
  bot.set_output(pr)

  # try to start process
  pr.start()

  # main loop
  logging.info("bot: connecting...")
  addr = cfg['address']
  if bot.connect(address=cfg['address']):
    logging.info("bot: connected")
    bot.process(block=True)
    logging.info("bot: disconnect")
  else:
    print("Unable to connect!",file=sys.stderr)

  logging.info("bot: stop proc runner")
  pr.stop()
  logging.info("bot: done")
