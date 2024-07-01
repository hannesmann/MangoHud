import time

TIMEOUT = 1.0 # seconds

class MsgParser:
    MSGBEGIN = bytes(':', 'utf-8')[0]
    MSGEND = bytes(';', 'utf-8')[0]
    MSGSEP = bytes('=', 'utf-8')[0]

    def __init__(self, conn):
        self.cmdpos = 0
        self.parampos = 0
        self.bufferpos = 0
        self.reading_cmd = False
        self.reading_param = False
        self.buffer = None
        self.cmd = bytearray(4096)
        self.param = bytearray(4096)

        self.conn = conn

    def readCmd(self, ncmds, timeout=TIMEOUT):
        '''
        returns:
            - None on error or disconnection
            - bytes() (empty) on timeout
        '''

        parsed = []

        remaining = timeout

        while remaining > 0 and ncmds > 0:
            now = time.monotonic()

            if self.buffer == None:
                self.buffer = self.conn.recv(remaining)
                self.bufferpos = 0

            # disconnected or error
            if self.buffer == None:
                return None

            for i in range(self.bufferpos, len(self.buffer)):
                c = self.buffer[i]
                self.bufferpos += 1
                if c == self.MSGBEGIN:
                    self.cmdpos = 0
                    self.parampos = 0
                    self.reading_cmd = True
                    self.reading_param = False
                elif c == self.MSGEND:
                    if not self.reading_cmd:
                        continue
                    self.reading_cmd = False
                    self.reading_param = False

                    cmd = self.cmd[0:self.cmdpos]
                    param = self.param[0:self.parampos]
                    self.reading_cmd = False
                    self.reading_param = False

                    parsed.append((cmd, param))
                    ncmds -= 1
                    if ncmds == 0:
                        break
                elif c == self.MSGSEP:
                    if self.reading_cmd:
                        self.reading_param = True
                else:
                    if self.reading_param:
                        self.param[self.parampos] = c
                        self.parampos += 1
                    elif self.reading_cmd:
                        self.cmd[self.cmdpos] = c
                        self.cmdpos += 1

            # if we read the entire buffer and didn't finish the command,
            # throw it away
            self.buffer = None

            # check if we have time for another iteration
            elapsed = time.monotonic() - now
            remaining = max(0, remaining - elapsed)

        # timeout
        return parsed
