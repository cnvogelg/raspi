import time

import host

class GrblSend:
    """send multi lines of GCode to Grbl.

        correctly handles send result checking and allows
        regular state updates
    """

    def __init__(self, host, 
                 update=0.3, max_cmd=60, poll=0.1,
                 start_reset=True, end_wait=True):
        """setup sender by associating a GrblHost instance

            host -- grbl host

            update -- update interval for state infos (s)
            max_cmd -- max time to wait for command reply
            poll -- internal interval to poll for incoming event data

            start_reset -- send a soft_reset before each send operation
            end_wait -- wait for idle at end of transfer
        """
        self.host = host
        self.update = update
        self.max_cmd = max_cmd
        self.poll = poll

        self.start_reset = start_reset
        self.end_wait = end_wait

        self.line_no = 0
        self.total_time = 0

    def send(self, source, state_update=None, check_mode=False):
        """send all string lines returned by source's iterator
           report status in regular intervals to call'able state_update:

            state_update(run_time, grbl_state)

           return last received event or None if command timed out
           if event is not ID_OK then send was aborted
        """
        # nothing to send
        if source is None:
            raise RuntimeError("no source given")
        src_iter = source.__iter__()
        if src_iter is None:
            raise RuntimeError("no iterator in source")

        # first reset Grbl
        if self.start_reset:
            self.host.soft_reset()

        # enable check mode
        if check_mode:
            self.host.toggle_check_mode()

        run_start = time.time()
        last_time = run_start
        last_event = None
        ok = True
        try:
            while True:
                # main loop of sender
                line = src_iter.next()
                # send line to host
                self.host.send_line(line)
                self.line_no += 1
                cmd_start_time = time.time()

                # now loop until result is here or we have to update status
                while True:
                    # try to grab an event
                    while True:
                        # check for state update?
                        now = time.time()
                        delta = now - last_time
                        if delta >= self.update:
                            # send a state request
                            last_time = now
                            self.host.request_state()                            

                        # check total command time
                        delta = now - cmd_start_time
                        if delta >= self.max_cmd:
                            last_event = None
                            ok = False
                            raise StopIteration()

                        # got an event?
                        if self.host.has_event():
                            break

                        # do a poll sleep
                        time.sleep(self.poll)

                    # event is ready -> read it
                    e = self.host.get_event()
                    last_event = e
                    if e.id == host.ID_OK:
                        # ready for next command
                        break
                    elif e.id in (host.ID_ERROR, host.ID_ALARM):
                        # abort send
                        ok = False
                        raise StopIteration()
                    elif e.id == ID_STATE:
                        # an incoming state update
                        if state_update != None:
                            state_update(last_time - run_start, e.data)

        except StopIteration:
            # end wait
            if self.end_wait and ok:
                while True:
                    # get update
                    s = self.host.get_state()
                    if s.id == host.STATE_IDLE:
                        break

                    # check for state update
                    if state_update != None:
                        now = time.time()
                        delta = now - last_time
                        if delta >= self.update:
                            state_update(last_time - run_start, s)
                            last_time = now

                    # poll sleep
                    time.sleep(self.poll)

            # update total time
            now = time.time()
            self.total_time = now - run_start

            # get final status
            if state_update != None:
                s = self.host.get_state()
                state_update(self.total_time, s)

            # disable check mode
            if check_mode:
                self.host.toggle_check_mode()

            return last_event
