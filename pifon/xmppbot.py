#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
  procbot - attach a process as bot XMPP client
  
  stdin of process is fed with incoming messages adressed with <name>: 
  stdout of process is received and print as messages
"""

import sys
import logging
import getpass
from optparse import OptionParser
import time

import sleekxmpp
import threading
import queue
import subprocess
import select

class ProcRunner(threading.Thread):
  def __init__(self, cmd, output):
    threading.Thread.__init__(self)
    self.cmd = cmd
    self.in_queue = queue.Queue()
    self.stop = False
    self.output = output
  
  def put(self, line):
    self.in_queue.put(line)
    
  def get_output(self, block=True):
    try:
      return self.out_queue.get(block)
    except query.Empty:
      return None
  
  def stop(self):
    self.stop = True
    self.join()
  
  def run(self):
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
    stdout = proc.stdout
    stdin  = proc.stdin
    while proc.returncode == None:      
      # update return code
      proc.poll()
      # send a terminate to the process
      if self.stop:
        proc.terminate()
        break
      # check for input/output
      (r,w,x) = select.select([stdout],[stdin],[],0.1)
      print(r,w)
      if stdout in r:
        # something to write to stdout?
        try:
          line = self.in_queue.get(False)
          print("in: ",line)
          line += '\n'
          data = line.encode()
          stdin.write(data)
        except queue.Empty:
          pass
      if stdin in w:
        # something to read from stdin
        data = stdout.readline().strip()
        line = data.decode()
        self.output.put(line)
        print("out:",line)

class ProcBot(sleekxmpp.ClientXMPP):
  def __init__(self, jid, password, room, nick):
    sleekxmpp.ClientXMPP.__init__(self, jid, password)

    self.in_room = False
    self.room = room
    self.nick = nick
    self.queue = queue.Queue()

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
                                    self.nick,
                                    # password=the_room_password,
                                    wait=True)

  def muc_message(self, msg):
    if msg['mucnick'] != self.nick:
      body = msg['body']
      prefix = self.nick + ':'
      if body.startswith(prefix):
        cmd = body[len(prefix):]
        print("got:",cmd)
        self.output.put(cmd)
        
  def muc_online(self, presence):
    if presence['muc']['nick'] != self.nick:
      self.send_message(mto=presence['from'].bare,
                        mbody="Hello, %s %s" % (presence['muc']['role'],
                                                  presence['muc']['nick']),
                        mtype='groupchat')
    else:
      self.in_room = True
      print("in room")
      # empty queue
      try:
        while True:
          msg = self.queue.get(False)
          self.put(msg)
      except queue.Empty:
        pass
  
  def muc_offline(self, presence):
    if presence['muc']['nick'] == self.nick:
      self.in_room = False
  
  def put(self, msg):
    if self.in_room:
      self.send_message(mto=self.room, mbody=msg, mtype='groupchat')
    else:
      self.queue.put(msg)

if __name__ == '__main__':
  # Setup the command line arguments.
  optp = OptionParser()

  # Output verbosity options.
  optp.add_option('-q', '--quiet', help='set logging to ERROR',
                  action='store_const', dest='loglevel',
                  const=logging.ERROR, default=logging.INFO)
  optp.add_option('-d', '--debug', help='set logging to DEBUG',
                  action='store_const', dest='loglevel',
                  const=logging.DEBUG, default=logging.INFO)
  optp.add_option('-v', '--verbose', help='set logging to COMM',
                  action='store_const', dest='loglevel',
                  const=5, default=logging.INFO)

  # JID and password options.
  optp.add_option("-j", "--jid", dest="jid",
                  help="JID to use")
  optp.add_option("-p", "--password", dest="password",
                  help="password to use")
  optp.add_option("-r", "--room", dest="room",
                  help="MUC room to join")
  optp.add_option("-n", "--nick", dest="nick",
                  help="MUC nickname")

  opts, args = optp.parse_args()

  # Setup logging.
  logging.basicConfig(level=opts.loglevel,
                      format='%(levelname)-8s %(message)s')

  if opts.jid is None:
    opts.jid = "audio@pifon.local"
  if opts.password is None:
    opts.password = "audio"
  if opts.room is None:
    opts.room = "felix@muc.pifon.local"
  if opts.nick is None:
    opts.nick = "audio"

  bot = ProcBot(opts.jid, opts.password, opts.room, opts.nick)
  cmd = ['./pifon_audio_fake']
  pr = ProcRunner(cmd, bot)
  bot.set_output(pr)

  pr.start()

  print("Connecting")
  if bot.connect():
    print("Connected")
    bot.process(block=True)
    print("Disconnect")
  else:
    print("Unable to connect.")

  pr.stop()
  print("Done")