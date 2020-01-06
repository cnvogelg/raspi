#!/usr/bin/env python3
import time
import lcd


def main():
    mylcd = lcd.LCD()
    mylcd.clear()
    mylcd.text(0, 0, lcd.pi_char + "hello, world!")
    off = 7
    for c in lcd.bar_chars:
        mylcd.text(off, 1, c)
        off += 1
    on = True
    col_map = (lcd.RED, lcd.GREEN, lcd.BLUE, lcd.WHITE)
    col = 0
    try:
        while True:
            but = mylcd.buttonRead()
            if but is None or but == 0xc:
                break
            if but == 1:
                if not on:
                    on = True
            if on:
                col = (col + 1) % 4
                mylcd.text(4, 1, "%d" % col)
                mylcd.backlight(col_map[col])
                on = False
            mylcd.text(0, 1, "%02x" % but)
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        mylcd.off()
        print("bye")


if __name__ == '__main__':
    main()
