import threading
import subprocess
import os

import Queue

class Worker:

  CMD_PLAY = 0
  CMD_STOP = 1
  CMD_EXIT = 2

  CMD_NAMES = ("play", "stop", "exit")

  def __init__(self):
    """setup idle player without chime sounds set"""
    self.chime_start_sound = None
    self.chime_stop_sound = None
    self.state_cb = None
    self.error_cb = None
    self.info_cb = None
    # commands
    self.play_start_cmd = None
    self.play_stop_cmd = None
    self.chime_start_cmd = None
    self.chime_stop_cmd = None
    self.start_stream_cmd = None
    self.stop_stream_cmd = None
    # threading
    self.thread = threading.Thread(target=self._loop)
    self.cmd_queue = Queue.Queue()
    # state
    self.last_cmd = self.CMD_STOP
    self.play_chimes = True
    self.proc = None
    # go!
    self.thread.start()

  def shutdown(self):
    self.cmd_queue.put((self.CMD_EXIT,None))
    self.last_cmd = self.CMD_EXIT
    # kill a running process
    if self.proc is not None:
      self.proc.terminate()
    # wait for thread
    self.thread.join()

  def set_command(self, who, cmd):
    # auto convert strings to arrays
    if type(cmd) == str:
      cmd = cmd.split()
    if who == 'chime_start':
      self.chime_start_cmd = cmd
    elif who == 'chime_stop':
      self.chime_stop_cmd = cmd
    elif who == 'start_stream':
      self.start_stream_cmd = cmd
    elif who == 'stop_stream':
      self.stop_stream_cmd = cmd
    elif who == 'play_start':
      self.play_start_cmd = cmd
    elif who == 'play_stop':
      self.play_stop_cmd = cmd
    else:
      raise ValueError("invalid who: " + who)

  def set_chime_sound(self, who, snd):
    """define start/stop chime sounds"""
    if who == 'start':
      self.chime_start_sound = snd
    elif who == 'stop':
      self.chime_stop_sound = snd
    else:
      raise ValueError("invalid who: " + who)

  def set_callback(self, who, cb):
    """set a callback that will receive state changes"""
    if who == 'error':
      self.error_cb = cb
    elif who == 'state':
      self.state_cb = cb
    elif who == 'info':
      self.info_cb = cb
    else:
      raise ValueError("invalid who: " + who)

  def set_play_chimes(self, on):
    """enable playhing chimes on start"""
    self.play_chimes = on

  def get_play_chimes(self):
    """is playing chimes enabled?"""
    return self.play_chimes

  def is_playing(self):
    """is the current state playing?"""
    return self.last_cmd == self.CMD_PLAY

  def play(self, url):
    """start playing a stream with the given url"""
    if self.last_cmd == self.CMD_STOP:
      self.cmd_queue.put((self.CMD_PLAY,url))
      self.last_cmd = self.CMD_PLAY
      return True
    else:
      return False

  def stop(self):
    """stop playing"""
    if self.last_cmd == self.CMD_PLAY:
      self.cmd_queue.put((self.CMD_STOP,None))
      self.last_cmd = self.CMD_STOP
      # kill a running process
      if self.proc is not None:
        self.proc.terminate()
      return True
    else:
      return False

  def _loop(self):
    """threading work loop"""
    while True:
      # get next cmd
      cmd, url = self.cmd_queue.get()

      # report current command
      if self.state_cb is not None:
        self.state_cb(self, self.CMD_NAMES[cmd])

      # exit thread
      if cmd == self.CMD_EXIT:
        break

      # start playing
      elif cmd == self.CMD_PLAY:
        # play start
        self._run('play_start', self.play_start_cmd, None)
        # play a start chime?
        if self.chime_start_sound is not None and self.play_chimes:
          self._run('chime_start', self.chime_start_cmd, self.chime_start_sound)
        # start streaming
        self._run('start_stream', self.start_stream_cmd, url)

      # stop playing
      elif cmd == self.CMD_STOP:
        # stop streaming
        self._run('stop_stream', self.stop_stream_cmd, url)
        # play a stop chime?
        if self.chime_stop_sound is not None and self.play_chimes:
          self._run('chime_stop', self.chime_stop_cmd, self.chime_stop_sound)
        # stop playing
        self._run('play_stop', self.play_stop_cmd, None)

  def _find_bin(self, exe):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(exe)
    if fpath:
        if is_exe(exe):
            return exe
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, exe)
            if is_exe(exe_file):
                return exe_file
    return exe

  def _get_cmd(self, in_cmd, arg=None):
    if in_cmd is None or len(in_cmd) == 0:
      return None
    # clone command
    cmd = []
    first = True
    for c in in_cmd:
      if first:
        c = self._find_bin(c)
        first = False
      # path expansion
      c = os.path.expanduser(c)
      # replace %s with argument
      if arg is not None:
        c = c.replace("%s", arg)
      cmd.append(c)
    return cmd

  def _run(self, context, in_cmd, arg):
    # build command line
    if in_cmd is None:
      return
    cmd = self._get_cmd(in_cmd, arg)
    if cmd is None:
      return
    if self.info_cb is not None:
      self.info_cb(self, context, cmd)
    try:
      dev_null = open(os.devnull, "w")
      self.proc = subprocess.Popen(cmd, stdout=dev_null, stderr=dev_null)
      self.proc.wait()
      dev_null.close()
      ret = self.proc.returncode
      if ret != 0:
        if self.error_cb is not None:
          self.error_cb(self, context, cmd, "returncode: %d" % ret)
    except Exception as e:
      if self.error_cb is not None:
        self.error_cb(self, context, cmd, str(e))
    self.proc = None


# ----- test -----
if __name__ == '__main__':
  import time
  w = Worker()
  w.set_command('chime_start', 'echo chime_start %s')
  w.set_command('chime_stop', 'echo chime stop %s')
  w.set_command('start_stream', 'sleep 10')
  w.set_chime_sound('start', 'start.wav')
  w.set_chime_sound('stop', 'stop.wav')
  w.play('my.url')
  time.sleep(1)
  w.stop()
  time.sleep(1)
  w.shutdown()


