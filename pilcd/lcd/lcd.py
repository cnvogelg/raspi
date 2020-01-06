import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd

from .base import *


class LCD16x2:
    """a wrapper class to control an Adafruit HW display via I2C"""
    button_map = {
        BUTTON_SELECT: "select_button",
        BUTTON_LEFT: "left_button",
        BUTTON_RIGHT: "right_button",
        BUTTON_UP: "up_button",
        BUTTON_DOWN: "down_button"
    }

    def __init__(self):
        lcd_columns = 16
        lcd_rows = 2
        i2c = busio.I2C(board.SCL, board.SDA)
        self._lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
        # load custom chars
        num = 0
        for data in custom_chars:
            self._lcd.create_char(num, list(data))
            num += 1

    def off(self):
        self.backlight(OFF)

    def clear(self):
        self._lcd.clear()

    def text(self, cx, cy, txt):
        self._lcd.cursor_position(cx, cy)
        self._lcd.message = txt

    def backlight(self, color):
        self._lcd.color = color

    def buttonRead(self):
        result = 0
        for button in ALL_BUTTONS:
            if getattr(self._lcd, self.button_map[button]):
                result |= button
        return result
