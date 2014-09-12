import time

import host

class GrblJog:
    """The jog frontend allows you to send manual jog/move commands from
       a jog device (e.g. joystick) and this class will trigger move
       commands via the GrblHost.

       Since actual movements take some time on the real machine, this
       module ensures that all incoming jog device movements are kept
       and realized when possible.

       You can either implement a stop-and-go jogger, i.e. it will wait
       for the next jog device command until the last one has finished
       or you can implement an incremental jogger, i.e. you can send
       movements from the jog device any time and they will be accumulated
       and realized ASAP.
    """

    def __init__(self, host, state_callee=None, state_interval=0.3):
        """create jog and attach GrblHost to it"""
        self.host = host
        self.state_callee = state_callee
        self.state_interval = state_interval
        self.move_todo = [0.0, 0.0, 0.0]
        self.cmd_busy = False
        self.start_time = time.time()
        self.last_state_update = self.start_time
        self.final_update = False

    def setup(self):
        """prepare GCode state

            mainly set to relative movement with G91
        """
        self.host.send_line_wait("G91")

    def cleanup(self):
        """cleanup GCode state

            mainly set back to absolute movement with G90
        """
        self.host.send_line_wait("G90")

    def abort_moves(self):
        """abort any outstanding movements.

           it will still finish the current running command in Grbl
        """
        self.move_todo = [0.0, 0.0, 0.0]

    def move_delta(self, delta):
        """input new jog device movement

           delta -- x,y,z triple with delta values
        """
        for i in range(3):
            self.move_todo[i] += delta[i]

    def get_moves_todo(self):
        """return current scheduled move as a XYZ tuple"""
        return self.move_todo

    def set_moves_todo(self, nm):
        """overwrite current move to do. pass a XYZ tuple"""
        self.move_todo = [nm[0], nm[1], nm[2]]

    def has_moves_todo(self):
        """are there any moves already submitted but not yet sent?"""
        return self.move_todo != [0.0, 0.0, 0.0]

    def is_busy_moving(self):
        """is machine currently moving?"""
        return self.cmd_busy

    def is_on_target(self):
        """is machine on currently requested target?"""
        return not self.is_busy_moving() and not self.has_moves_todo()

    def handle(self):
        """call this in regular intervals to perform the movements

            use a regular polling interval of e.g. 100 ms to keep
            the jog movements interactive.

            returns True if target position is reached and no movements need
            to be performed currently
        """
        now = time.time()

        # nothing to be done
        if self.is_on_target() and not self.final_update:
            return True

        # is a command busy?
        if self.host.has_event():
            ev = self.host.get_event()
            if ev.id == host.ID_OK:
                if self.cmd_busy:
                    # last command is done
                    self.cmd_busy = False
                else:
                    raise host.GrblEventError(ev)
            elif ev.id in (host.ID_ERROR, host.ID_ALARM):
                # any error or alarm gives an GrblEventError
                raise host.GrblEventError(ev)
            elif ev.id == host.ID_STATE:
                state = ev.data
                # trigger a status 
                if self.state_callee is not None:
                    delta = now - self.start_time
                    self.state_callee(delta, state)
                self.last_state_update = now
                # is it the final update idle?
                if self.final_update and state.id == host.STATE_IDLE:
                    self.final_update = False
                    return self.is_on_target()

        # command was done
        if not self.cmd_busy:
            # is there anything to do left?
            if self.move_todo != [0.0, 0.0, 0.0]:
                # send a new move command
                m = self.move_todo
                gcode = "G0 X%.3f Y%.3f Z%.3f" % (m[0], m[1], m[2])
                self.host.send_line(gcode)
                self.move_todo = [0.0, 0.0, 0.0]
                self.cmd_busy = True
                self.final_update = False
            # otherwise we are almost done and request final updates
            # until 'idle' state is reched. then we report and return.
            else:
                self.final_update = True
                self.host.request_state()

        # is a state update due?
        delta = now - self.last_state_update
        if delta >= self.state_interval:
            # send a request
            self.host.request_state()
            self.last_state_update = now

        return False
