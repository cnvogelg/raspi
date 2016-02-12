#!/usr/bin/env python3
from __future__ import print_function
import os
try:
  from configparser import SafeConfigParser, Error
except ImportError:
  from ConfigParser import SafeConfigParser, Error

class BotCfg:
  """manage a configuration in a *.cfg file"""
  def __init__(self, name, force_cfg_file=None):
    self.name = name
    self.force_cfg_file = force_cfg_file
    file_name = name + ".cfg"
    self.home_cfg_file = os.path.expanduser("~/." + file_name)
    self.cwd_cfg_file = file_name
    self.cfg = SafeConfigParser()

  def __repr__(self):
    return "[BotCfg:read=%s,write=%s,%s]" % \
      (self.get_read_file(), self.get_write_file(), self.cfg.sections())

  def _get_read_files(self):
    files = []
    # check current working dir
    if os.access(self.cwd_cfg_file, os.R_OK):
      files.append(self.cwd_cfg_file)
    # check user's home dir
    if os.access(self.home_cfg_file, os.R_OK):
      files.append(self.home_cfg_file)
    # a forced config file?
    if self.force_cfg_file is not None:
      # force file is readble
      if os.access(self.force_cfg_file, os.R_OK):
        files.append(self.force_cfg_file)
    if len(files) == 0:
      return None
    else:
      return files

  def _get_write_file(self):
    if self.force_cfg_file is not None:
      # force file needs to be writable
      return self.force_cfg_file
    else:
      return self.home_cfg_file

  def load(self):
    """load config from file
       returns the config file or None
    """
    cfg_files = self._get_read_files()
    if cfg_files is None:
      return None
    # parse config
    try:
      self.cfg.read(cfg_files)
      return cfg_files
    except Error:
      return None
    except IOError:
      return None

  def save(self):
    """save config to file
       return the config file or None"""
    cfg_file = self._get_write_file()
    if cfg_file is None:
      return None
    try:
      fh = open(cfg_file, "w")
      self.cfg.write(fh)
      fh.close()
      return cfg_file
    except Error:
      return None
    except IOError:
      return None

  def _read_value(self, def_value, value):
    if def_value is None:
      if value == '':
        return None
      else:
        return value
    elif type(def_value) is str:
      if value == '':
        return None
      else:
        return value
    elif type(def_value) is bool:
      if value.lower() in ('on','1','true'):
        return True
      else:
        return False
    else:
      t = type(def_value)
      return t(value)

  def _write_value(self, value):
    if value is None:
      return ''
    elif type(value) is str:
      return value
    else:
      return repr(value)

  def get_section(self, name, def_dict):
    """give a default section and look up values in config
      return new section dictionary with config and default values
    """
    # make sure parser has section
    if not self.cfg.has_section(name):
      self.cfg.add_section(name)
    # get config dictionary
    cfg_dict = dict(self.cfg.items(name))
    result = {}
    for key in def_dict:
      # get default value and type
      value = def_dict[key]
      # we have a config value
      if key in cfg_dict:
        cvalue = cfg_dict[key]
        result[key] = self._read_value(value, cvalue)
      # use default value
      else:
        # set value in cfg
        self.cfg.set(name, key, self._write_value(value))
        # return default
        result[key] = value
    return result

  def set_section(self, name, val_dict):
    """give new values for a section"""
    # make sure parser has section
    if not self.cfg.has_section(name):
      self.cfg.add_section(name)
    # parse values
    for key in val_dict:
      value = val_dict[key]
      self.cfg.set(name, key, self._write_value(value))


if __name__ == '__main__':
  cfg = BotCfg("test")
  my_sect = {
    'aint' : 42,
    'abool' : False,
    'bbool' : True,
    'astr' : "Hello, world!",
    'anone' : None
  }
  print(my_sect)
  cfg.set_section("my",my_sect)
  name = cfg.save()
  print("save to", name)
  # new cfg
  cfg2 = BotCfg("test")
  names = cfg2.load()
  print("load from", names)
  res = cfg.get_section("my",my_sect)
  print(res)
