import info

import create

class UIMod(info.InfoMod):
  def __init__(self):
    super(UIMod, self).__init__("ui")

  def setup(self, reply, log, cfg, botopts):
    super(UIMod, self).setup(reply, log, cfg, botopts)
    # now create ui
    ui_cfg = self._get_ui_cfg(cfg)
    self.ui = create.create_ui(**ui_cfg)

  def _get_ui_cfg(self, cfg):
    def_cfg = {
      'name' : 'lcd',
      'sim' : True,
      'font_path' : './font'
    }
    ui_cfg = cfg.get_section("vumeter", def_cfg)
    self.log("cfg ui=",ui_cfg)
    return ui_cfg
