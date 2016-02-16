import info
import importlib

from bot import BotCmd
from playctl import PlayerControl

class UIMod(info.InfoMod):
  def __init__(self):
    super(UIMod, self).__init__("ui")
    self.cmds = [
      BotCmd("print",callee=self.cmd_print,arg_types=(str,))
    ]

  def setup(self, reply, log, cfg, botopts):
    super(UIMod, self).setup(reply, log, cfg, botopts)
    # now create ui
    ui_cfg = self._get_ui_cfg(cfg)
    self.ui = self._create_ui(ui_cfg, cfg)
    self.ui.play_ctl = PlayerControl(self.send_command, self.log)
    # fetch tick interval from ui
    self.tick = self.ui.get_tick_interval()
    self.listener = self.ui

  def get_commands(self):
    return self.cmds

  def cmd_print(self, sender, args):
    self.ui.print_cmd(sender, args[0])

  def _get_ui_cfg(self, cfg):
    def_cfg = {
      'name' : 'dummy'
    }
    ui_cfg = cfg.get_section("ui", def_cfg)
    self.log("cfg ui=",ui_cfg)
    return ui_cfg

  def _create_ui(self, ui_cfg, cfg):
    pkg_name = "ui." + ui_cfg['name']
    pkg = importlib.import_module(pkg_name)
    pdict = pkg.__dict__
    if 'UI' not in pdict:
      raise RuntimeError("no 'UI' class in pkg found: " + pkg_name)
    clz = pdict['UI']
    return clz(cfg)
