# unittests for grblhost

import unittest
import glob
import time

import host

# find serial port
ser_ports = "/dev/tty.usbmodem*"
ports = glob.glob(ser_ports)
if len(ports) == 0:
    raise RuntimeError("No serial port found")
ser_port = ports[0]
ser_baud = 115200


class GrblHostBaseTests(unittest.TestCase):
    def setUp(self):
        self.host = host.GrblHost(ser_port, ser_baud)

    def testOpenClose(self):
        # no version yet
        self.assertIsNone(self.host.get_firmware_version())
        # open
        self.host.open()
        # make sure we have a version
        self.assertIsNotNone(self.host.get_firmware_version())
        # assume there is no event waiting
        self.assertFalse(self.host.has_event())
        # close
        self.host.close()
        # no version again
        self.assertIsNone(self.host.get_firmware_version())

    def testOpenCloseErrors(self):
        # close before open is not allowed
        with self.assertRaises(host.GrblHostError):
            self.host.close()
        # open
        self.host.open()
        # double open is not allowed
        with self.assertRaises(host.GrblHostError):
            self.host.open()
        # close
        self.host.close()

    def testHardReset(self):
        # not allowed before open
        with self.assertRaises(host.GrblHostError):
            self.host.hard_reset()
        # open
        self.host.open()
        # hard reset
        self.host.hard_reset()
        # assume there is no event waiting
        self.assertFalse(self.host.has_event())
        # close
        self.host.close()
        # not allowed after close     
        with self.assertRaises(host.GrblHostError):
            self.host.hard_reset()


class GrblHostTests(unittest.TestCase):
    def setUp(self):
        self.host = host.GrblHost(ser_port, ser_baud)
        self.host.open()

    def tearDown(self):
        self.host.close()

    def testSoftReset(self):
        self.host.soft_reset()

    def testCheckMode(self):
        # assume its disabled
        self.assertFalse(self.host.is_check_mode_enabled())
        # now enable it
        self.host.toggle_check_mode()
        # assume its enabled
        self.assertTrue(self.host.is_check_mode_enabled())
        # now disable it
        self.host.toggle_check_mode()
        # assume its disable again
        self.assertFalse(self.host.is_check_mode_enabled())

    def testStateEvent(self):
        self.host.request_state()
        e = self.host.get_event()
        self.assertEquals(host.ID_STATE, e.id)
        s = e.data
        # make sure result is a GrblState
        self.assertEquals(host.GrblState, s.__class__)

        # same works with get_state() helper
        s = self.host.get_state()
        # make sure result is a GrblState
        self.assertEquals(host.GrblState, s.__class__)

    def testSendLine(self):
        # assume idle operation
        s = self.host.assume_state(host.STATE_IDLE)
        # assume no event is waiting
        self.assertFalse(self.host.has_event())
        # send some gcode
        gcode = "G0 X1 Y2 Z3"
        self.host.send_line(gcode)
        # get state event (block until op is finished)
        e = self.host.get_event()
        self.assertEquals(host.ID_OK, e.id)
        # wait until not idle again
        ok = self.host.wait_for_state(host.STATE_IDLE)
        self.assertTrue(ok)
        # update state
        s = self.host.get_state()
        self.assertEquals((1.0, 2.0, 3.0), s.wpos)
        self.assertEquals((1.0, 2.0, 3.0), s.mpos)


if __name__ == '__main__':
    unittest.main(verbosity=2)
