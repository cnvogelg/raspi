import widget

class Control(widget.Widget):
  def __init__(self, pane, rect):
    super(Control, self).__init__(pane, rect)

  def handle_event(self, event):
    pass

