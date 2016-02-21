
class Backlight:
    """Helper class that controls the color of the backlight"""
    def __init__(self, lcd):
        self.lcd = lcd
        self.connected = False
        self.active = False
        self.ping_lost = False
        self.blank = False
        self.update()

    def update(self):
        if self.blank:
            col = self.lcd.OFF
        elif not self.connected:
            col = self.lcd.BLUE
        elif self.active:
            col = self.lcd.RED
        elif self.ping_lost:
            col = self.lcd.VIOLET
        else:
            col = self.lcd.GREEN
        self.lcd.backlight(col)

    def set_connected(self, on):
        self.connected = on
        self.update()

    def set_active(self, on):
        self.active = on
        self.update()

    def set_ping_lost(self, on):
        self.ping_lost = on
        self.update()

    def set_blank(self, on):
        self.blank = on
        self.update()
