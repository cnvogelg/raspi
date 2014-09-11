import time

import host

class GrblSendError(host.GrblBaseError):
    def __init__(self, msg, event=None):
        self.msg = msg
        self.event = event

    def __str__(self):
        if self.event is None:
            return "GrblSendError: " + self.msg
        else:
            return "GrblSendError: " + self.msg + " event: " + self.event


class GrblSend:
    """send multi lines of GCode to Grbl.

        correctly handles send result checking and allows
        regular state updates
    """

    def __init__(self, host, line_source,
                 state_callee=None,
                 update=0.3, max_cmd=0, poll=0.1,
                 start_reset=True, end_wait=True, check_mode=False):
        """setup sender by associating a GrblHost instance

            host -- grbl host
            source -- iterable object that provides gcode lines

            state_callee -- callable to get state updates (ts, state)

            update -- update interval for state infos (s)
            max_cmd -- max time to wait for command reply (0=off)
            poll -- internal interval to poll for incoming event data

            start_reset -- send a soft_reset before each send operation
            end_wait -- wait for idle at end of transfer
            check_mode -- enable check mode before sending
        """
        self.host = host
        self.line_source = line_source
        self.state_callee = state_callee

        self.update = update
        self.max_cmd = max_cmd
        self.poll = poll

        self.start_reset = start_reset
        self.end_wait = end_wait
        self.check_mode = check_mode

    def __iter__(self):
        """return the iterator for this send operation"""
        return GrblSendIter(self)

    def send(self):
        """convenience function to call the iter"""
        for wait in self:
            time.sleep(wait)


class GrblSendIter:
    def __init__(self, send):
        self.send = send
        self.host = send.host
        self.state_callee = send.state_callee
        self.line_iter = send.line_source.__iter__()
        self.line_no = 0
        self.last_update_time = 0
        self.start_run = time.time()
        self.start_cmd = 0
        self.need_line = True
        self.got_all_lines = False
        self._setup()

    def get_lines(self):
        return self.line_no

    def _setup(self):
        # begin with reset
        if self.send.start_reset:
            self.host.soft_reset()
        # check mode?
        if self.send.check_mode:
            self.host.toggle_check_mode()

    def _teardown(self):
        # update total time
        now = time.time()
        self.total_time = now - self.start_run
        # get final status
        if self.state_callee != None:
            s = self.host.get_state()
            self.state_callee(self.total_time, s)
        # disbale check mode?
        if self.send.check_mode:
            self.host.toggle_check_mode()

    def _get_next_line(self):
        """return the next line of the source iterator or None"""
        if self.got_all_lines:
            return None
        try:
            return self.line_iter.next()
        except StopIteration:
            self.got_all_lines = True
            return None

    def _process_line(self):
        line = self._get_next_line()
        if line is not None:
            self.need_line = False
            self.host.send_line(line)
            self.line_no += 1
            self.start_cmd = time.time()

    def next(self):
        """main iterator entrance point. 

           returns the minimum amount of time before you should
           call this method again.

           you can call this method later or earlier, but if you 
           call it too late then you might get state calls later
        """
        now = time.time()

        # do we need to send a new line?
        if self.need_line and not self.got_all_lines:
            self._process_line()

        # all lines were sent - wait for finish
        if self.got_all_lines:
            # poll state
            state = self.host.get_state()
            if state.id == host.STATE_IDLE:
                # idle again -> tear down and end iteration
                self._teardown()
                raise StopIteration()

            # check for state update
            if self.state_callee is not None:
                delta = now - self.last_update_time
                if delta >= self.send.update:
                    self.state_callee(now - self.start_run, state)
                    self.last_update_time = now

            # calc poll time
            return self._calc_poll_time(now)

        # still sending lines...
        # do we need a state update?
        if self.state_callee is not None:
            delta = now - self.last_update_time
            if delta >= self.send.update:
                # send a state request
                self.host.request_state()
                self.last_update_time = now

        # a command time out?
        mc = self.send.max_cmd
        if mc > 0:
            delta = now - self.start_cmd
            if delta >= mc:
                self._teardown()
                raise GrblSendError("Command time out")

        # is an event waiting?
        if self.host.has_event():
            # event is ready -> read it
            ev = self.host.get_event()
            if ev.id == host.ID_OK:
                # ready for next line
                self._process_line()
            elif ev.id in (host.ID_ERROR, host.ID_ALARM):
                # abort send
                self._teardown()
                raise GrblSendError("Command failed", ev)
            elif ev.id == host.ID_STATE:
                # an incoming state update
                if self.state_callee != None:
                    delta = now - self.start_run
                    self.state_callee(delta, ev.data)

        # calc sleep time
        return self._calc_poll_time(time.time())

    def _calc_poll_time(self, now):
        """use either poll time or time to next status update for sleep"""
        poll_time = self.send.poll
        if self.state_callee is None:
            return poll_time
        next_update = self.last_update_time + self.send.update
        delta_update = max(next_update - now, 0)
        return min(poll_time, delta_update)

