# unittests for grblhost

import unittest
import glob
import time

import host
import jog

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


class GrblJogTests(unittest.TestCase):
    def setUp(self):
        self.host = host.GrblHost(ser_port, ser_baud)
        self.host.open()

    def tearDown(self):
        self.host.close()

    def testSetupCleanup(self):
        j = jog.GrblJog(self.host)
        j.setup()
        j.cleanup()

    def testIdle(self):
        j = jog.GrblJog(self.host)
        j.setup()
        self.assertTrue(j.handle())
        j.cleanup()

    def testMove(self):
        u = KeepLastUpdater()
        j = jog.GrblJog(self.host, u)
        j.setup()
        self.assertTrue(j.handle())
        j.move_delta([1.0, 0.0, 0.0])
        self.assertFalse(j.handle())
        # wait for true
        end = time.time() + 10
        while time.time() < end:
            if j.handle():
                break
            time.sleep(0.1)
        if time.time() >= end:
            raise AssertError("Timeout")
        j.cleanup()
        # assert final pos
        self.assertEquals(u.last.mpos, (1.0, 0.0, 0.0))

    def testMultiMove(self):
        u = KeepLastUpdater()
        j = jog.GrblJog(self.host, u)
        j.setup()
        self.assertTrue(j.handle())
        j.move_delta([1.0, 0.0, 0.0])
        j.handle()
        time.sleep(0.1)
        j.move_delta([0.0, 2.0, 0.0])
        j.handle()
        time.sleep(0.1)
        j.move_delta([0.0, 0.0, 3.0])
        # wait until done
        end = time.time() + 10
        while time.time() < end:
            if j.handle():
                break
            time.sleep(0.1)
        if time.time() >= end:
            raise AssertError("Timeout")
        j.cleanup()
        # assert final pos
        self.assertEquals(u.last.mpos, (1.0, 2.0, 3.0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
