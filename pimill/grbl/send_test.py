# unittests for grblhost

import unittest
import glob
import time

import host
import send

# find serial port
ser_ports = "/dev/tty.usbmodem*"
ports = glob.glob(ser_ports)
if len(ports) == 0:
    raise RuntimeError("No serial port found")
ser_port = ports[0]
ser_baud = 115200


class KeepLastUpdater:
    def __init__(self):
        self.last = None
    def __call__(self, t, s):
        self.last = s


class KeepAllUpdater:
    def __init__(self):
        self.all = []
    def __call__(self, t, s):
        self.all.append( (t,s) )
    def get_last(self):
        return self.all[-1]


class GrblSendTests(unittest.TestCase):
    def setUp(self):
        self.host = host.GrblHost(ser_port, ser_baud)
        self.host.open()

    def tearDown(self):
        self.host.close()

    def testSendSingleLine(self):
        u = KeepLastUpdater()
        lines = ('G0 X1',)
        s = send.GrblSend(self.host, lines, u)
        i = s.__iter__()
        try:
            while True:
                delta = i.next()
                time.sleep(delta)
        except StopIteration:
            pass
        self.assertEquals(1, i.get_lines())
        self.assertIsNotNone(u.last)
        self.assertEquals((1.0, 0.0, 0.0), u.last.mpos)

    def testSendMultiLines(self):
        lines = (
            'G0 X1',
            'G0 Y2',
            'G0 Z3'
        )
        u = KeepAllUpdater()
        s = send.GrblSend(self.host, lines, u)
        i = s.__iter__()
        try:
            while True:
                delta = i.next()
                time.sleep(delta)
        except StopIteration:
            pass
        self.assertEquals(3, i.get_lines())
        self.assertEquals((1.0, 2.0, 3.0), u.get_last()[1].mpos)

if __name__ == '__main__':
    unittest.main(verbosity=2)
