#!/usr/bin/env python3
import time
import lcd


winners = (
    ('Felix', 'Jonas', 'Anna'),
    ('Anna', 'Felix', 'Jonas'),
    ('Jonas', 'Anna', 'Felix')
)


colors = (
    lcd.YELLOW,
    lcd.RED,
    lcd.GREEN
)


def show(mylcd, offset):
    mylcd.clear()
    # time
    ts = time.time()
    lt = time.localtime(ts)
    txt = time.strftime("%H:%M:%S",lt)
    mylcd.text(8, 0, txt)
    # calc winner
    n = (lt.tm_yday + offset) % 3
    w = winners[n]
    mylcd.backlight(colors[n])
    mylcd.text(0, 0, "1:" + w[0])
    mylcd.text(0, 1, "2:" + w[1])
    mylcd.text(8, 1, "3:" + w[2])


def main():
    mylcd = lcd.LCD()
    print("using", mylcd.__class__.__name__)
    mylcd.clear()
    offset = 1
    try:
        while True:
            but = mylcd.buttonRead()
            if but is None or but == 0xc:
                break
            elif but == lcd.BUTTON_LEFT | lcd.BUTTON_UP:
                offset -= 1
            elif but == lcd. BUTTON_RIGHT | lcd.BUTTON_UP:
                offset += 1
            show(mylcd, offset)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        mylcd.off()
        print("bye")


if __name__ == '__main__':
    main()
