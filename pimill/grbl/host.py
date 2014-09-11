# grblhost.py
# 
# a host interface for the grbl firmware

import serial
import time
import threading

# event constants
ID_OK = 0
ID_ERROR = 1
ID_ALARM = 2
ID_INFO = 3
ID_STATE = 4

event_names = (
    "ok",
    "error",
    "alarm",
    "info",
    "state"
)

# state
STATE_IDLE = 0
STATE_QUEUED = 1
STATE_CYCLE = 2
STATE_HOLD = 3
STATE_HOMING = 4
STATE_ALARAM = 5
STATE_CHECK_MODE = 6

state_names = (
    "Idle",
    "Queued",
    "Cycle",
    "Hold",
    "Homing",
    "Alarm",
    "Check_Mode"
)

# ----- Errors -----
class GrblBaseError(Exception):
    pass

class GrblHostError(GrblBaseError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "GrblHostError: " + self.msg

class GrblEventError(GrblBaseError):
    def __init__(self, event):
        self.event = event

    def __str__(self):
        return "GrblEventError: " + self.event

class GrblStateError(GrblBaseError):
    def __init__(self, state):
        self.state = state

    def __str__(self):
        return "GrblStateError: " + self.state


# ----- Helper Classes -----
class GrblEvent:
    def __init__(self, id, data=None):
        self.id = id
        self.data = data

    def __str__(self):
        if self.data != None:
            return "{%s,%s}" % (event_names[self.id], self.data)
        else:
            return "{%s}" % event_names[self.id]


class GrblState:
    def __init__(self, id, mpos, wpos):
        self.id = id
        self.mpos = mpos
        self.wpos = wpos

    def __str__(self):
        return "<%s,MPos=%s,WPos=%s>" % (state_names[self.id], self.mpos, self.wpos)


class GrblHost:
    """
    The GrblHost class provides a more user-friendly interface to the raw Grbl
    serial protocol.

    It has a simple send commands and poll/retrieve events interface.
    Commands that can be sent include gcode lines but also real-time commands
    like cycle start and feed feed_hold.

    It does some minimal state tracking, e.g. for check mode but does not 
    validate any gcode commands
    """

    def __init__(self, ser_port, ser_baud=115200, timeout=5):
        """create the host and open the associated serial ser_port
        """
        # params
        self.ser_port = ser_port
        self.ser_baud = ser_baud
        self.timeout = timeout
        # state
        self.ser = None
        self.grbl_version = None
        self.in_check_mode = False
        self.line_active = False
        self.is_open = False

    def open(self):
        """open serial port and wait for Grbl firmware hello"""
        if self.is_open:
            raise GrblHostError("already open!")
        self.ser = serial.Serial(self.ser_port, self.ser_baud)
        self._handle_reset()
        self.is_open = True

    def close(self):
        """close serial port and shut down grbl host"""
        if not self.is_open:
            raise GrblHostError("not open!")
        self.ser.close()
        self.ser = None
        self.is_open = False
        self.grbl_version = None

    def _handle_reset(self):
        """reset of state and wait for Grbl hello"""
        # reset own state
        self.grbl_version = None
        self.in_check_mode = False
        self.line_active = False
        # wait for init
        self._wait_for_grbl_init()

    def _slurp_until(self, char='G', timeout=10, sleep=0.1):
        """read serial stream until a given character was found or timeout"""
        num = 0
        end = time.time() + timeout
        while time.time() < end:
            while self.ser.inWaiting():
                c = self.ser.read()
                num += 1
                if c == char:
                    return num
                was_slurp = True
            time.sleep(sleep)
        return 0

    def _wait_for_grbl_init(self):
        # read unti a 'G' is found
        num = self._slurp_until('G')
        if num == 0:
            raise GrblHostError("No Grbl hello!")
        # check for rest of line
        r = self.ser.readline()
        if r is None:
            raise GrblHostError("Invalid Grbl hello!")
        r = r.strip()
        if r.startswith('rbl '):
            c = r.split(' ')
            if len(c) < 2:
                raise GrblHostError("Invalid Grbl hello!")
            self.grbl_version = c[1]
            self.ser.flushInput()
        else:
            raise GrblHostError("Invalid Grbl hello!")

    # ----- get firmware release ----

    def get_firmware_version(self):
        """return firmware release"""
        return self.grbl_version

    # ----- resets -----

    def hard_reset(self):
        """perform a hard reset by closing re-opening the serial port"""
        self.close()
        self.open()

    def soft_reset(self):
        """perform a firmware self init"""
        self.ser.write("\030")
        self._handle_reset()

    # ----- toggle check mode -----

    def toggle_check_mode(self):
        # make sure there are no pending events 
        self.slurp_events()
        # send command
        self.ser.write("$C\r")
        # get state
        e = self.get_event()
        if e.id != ID_INFO:
            raise GrblEventError(e)
        state = e.data
        if state == 'Enabled':
            self.in_check_mode = True
        elif state == 'Disabled':
            self.in_check_mode = False
        else:
            raise GrblHostError("Invalid check_mode state: " + state)
        # get ok
        e = self.get_event()
        if e.id != ID_OK:
            raise GrblEventError(e)
        # wait for Grbl soft-reset after disable
        if not self.in_check_mode:
            self._handle_reset()

    def is_check_mode_enabled(self):
        """return true if check mode was enabled"""
        return self.in_check_mode

    # --- send commands ---

    def send_line(self, line):
        """send a line of GCode

            Note: the line has not to be terminated by a return or newline
        """
        self.ser.write(line + "\r")

    def send_kill_alarm(self):
        self.ser.write("$X\r\n")

    def send_start_homing(self):
        self.ser.write("$H\r\n")

    # ---- real time commands ----

    def cycle_start(self):
        self.ser.write("~")

    def feed_hold(self):
        self.ser.write("!")

    def request_state(self):
        self.ser.write("?")

    # ---- some helpers ----

    def get_state(self):
        """request a state event and pull it

            Note: this call fails if another event arrives!
        """
        self.request_state()
        e = self.get_event()
        if e.id != ID_STATE:
            raise GrblEventError(e)
        return e.data

    def assume_state(self, state):
        """make sure grbl firmware agrees with you on the current state

            will raise a GrblStateError if state does not match!
        """
        s = self.get_state()
        if s.id != state:
            raise GrblStateError(s)

    def wait_for_state(self, state_id, timeout=10, interval=0.1):
        """wait until a given state is reached.

           poll for up to 'timeout' seconds in intervals of 'interval' seconds

           returns True if state was reached, False otherwise
        """
        end = time.time() + timeout
        while time.time() <= end:
            s = self.get_state()
            if s.id == state_id:
                return True
        return False

    def send_line_result(self, line):
        """send a line and return the result

            note: it blocks until a result was returned.
            note: everything not a return state gives a GrblStateError or GrblEventError
        """

    # ---- grbl events ----

    def has_event(self):
        """poll if an event is ready to be read"""
        return self.ser.inWaiting()

    def get_event(self):
        """read the next line of grbl outputs and parse it

            returns a tuple (event_id, extra_data)
        """
        line = self.ser.readline()
        if line is None:
            return None
        line = line.strip()

        if len(line) > 1:
            if line == 'ok':
                return GrblEvent(ID_OK)
            elif line.startswith('error:'):
                return GrblEvent(ID_ERROR, line[6:])
            elif line.startswith('ALARM:'):
                return GrblEvent(ID_ALARM, line[6:])
            elif line[0] == '[' and line[-1] == ']':
                return GrblEvent(ID_INFO, line[1:-1]) 
            elif line[0] == '<' and line[-1] == '>':
                s = self._parse_state(line[1:-1])
                return GrblEvent(ID_STATE, s)

        raise GrblHostError("Invalid event text: "+line)

    def slurp_events(self):
        """consume events until there are no more"""
        while self.has_event():
            self.get_event()

    def _parse_state(self, input):
        elem = input.split(',')
        if len(elem) < 7:
            raise GrblHostError("Too few state elements: "+input)
        # parse state
        state = self._parse_state_mode(elem[0])
        # check for machine and work pos
        mpos = self._parse_pos('MPos', elem[1:4])
        wpos = self._parse_pos('WPos', elem[4:7])
        return GrblState(state, mpos, wpos)

    def _parse_pos(self, tag, elem):
        # make sure tag matches
        if not elem[0].startswith(tag + ":"):
            raise GrblHostError("Invalid " + tag + " position text: " + elem[0])
        # strip tag
        elem[0] = elem[0][len(tag)+1:]
        return (float(elem[0]),
                float(elem[1]),
                float(elem[2]))

    def _parse_state_mode(self, s):
        if s == 'Idle':
            return STATE_IDLE
        elif s == 'Queue':
            return STATE_QUEUED
        elif s == 'Run':
            return STATE_CYCLE
        elif s == 'Hold':
            return STATE_HOLD
        elif s == 'Home':
            return STATE_HOME
        elif s == 'Alarm':
            return STATE_ALARM
        elif s == 'Check':
            return STATE_CHECK
        else:
            raise GrblHostError("Invalid state mode: "+s)
