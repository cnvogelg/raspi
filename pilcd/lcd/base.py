BUTTON_SELECT = 1
BUTTON_RIGHT = 2
BUTTON_DOWN = 4
BUTTON_UP = 8
BUTTON_LEFT = 16

ALL_BUTTONS = (BUTTON_SELECT, BUTTON_RIGHT,
               BUTTON_DOWN, BUTTON_UP, BUTTON_LEFT)

BLACK = (0, 0, 0)
RED = (100, 0, 0)
GREEN = (0, 100, 0)
BLUE = (0, 0, 100)
YELLOW = (100, 100, 0)
TEAL = (0, 100, 100)
VIOLET = (100, 0, 100)
WHITE = (100, 100, 100)

ON = WHITE
OFF = BLACK

pi_char = chr(0xf7)

# custom chars
play_char = chr(0)
bell_char = chr(1)

# bar chars from 0 to 8
bar_chars = (chr(32), chr(1), chr(2), chr(3), chr(4),
             chr(5), chr(6), chr(7), chr(0xff))

# custom chars (5x8 pixels)
# (source http://www.quinapalus.com/hd44780udg.html)
custom_chars = (
    # 0: play
    (0x0, 0x8, 0xc, 0xe, 0xc, 0x8, 0x0, 0x0),
    # 1: 1 px bar
    (0, 0, 0, 0, 0, 0, 0, 0x1f),
    # 2: 2 px bar
    (0, 0, 0, 0, 0, 0, 0x1f, 0x1f),
    # 3: 3 px bar
    (0, 0, 0, 0, 0, 0x1f, 0x1f, 0x1f),
    # 4: 4 px bar
    (0, 0, 0, 0, 0x1f, 0x1f, 0x1f, 0x1f),
    # 5: 5 px bar
    (0, 0, 0, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f),
    # 6: 6 px bar
    (0, 0, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f),
    # 7: 7 px bar
    (0, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f, 0x1f)
)
