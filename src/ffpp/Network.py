import socket
import logging

LOG = logging.getLogger(__name__)


class Network(object):
    def __init__(self, ip, port=8899):
        self.ip = ip
        self.port = port
        self.connection = None
        self.responseData = None

    def __del__(self):
        self.dissconnect()

    def connect(self):
        self.connection = socket.socket()
        self.connection.settimeout(5)
        try:
            self.connection.connect((self.ip, self.port))
        except OSError:
            LOG.info("Unable to connect")
            self.dissconnect()
            return False
        return True
        # self.sendControlMessage()

    def dissconnect(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def sendMessage(self, message, decode=True):
        self.responseData = None

        # Make sure we are connected first.
        if self.connection is None:
            self.connect()

        if type(message) is not bytes:
            message = message.encode()

        try:
            self.connection.sendall(message)
        except OSError:
            LOG.info("Unable to send message. Reconnecting...")

            if self.connect():
                try:
                    self.connection.sendall(message)
                except socket.error:
                    LOG.info("Printer seems to be unavailable.")
                    return False
            else:
                LOG.info("Printer seems to be unavailable.")
                return False

        # Update responseData
        self.responseData = self.connection.recv(1024)
        if decode:
            self.responseData = self.responseData.decode()

        if self.responseData is not None:
            return True
        return False

    def sendControlRequest(self):
        """Send Control message to printer.

        Response from printer is something like
            'CMD M601 Received.\r\nControl failed.\r\nok\r\n'
        or
            'CMD M601 Received.\r\nControl Success V2.1.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M601 S1\r\n')

        return self.responseData

    def sendControlRelease(self):
        """ Release control of printer. You will only
        be able to watch printer status when you dont have
        the control.

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M602\r\n')

        return self.responseData

    def sendInfoRequest(self):
        """ Send a request for basic information about printer

        Response from printer is something like:
        'CMD M115 Received.\r\n
        Machine Type: Flashforge Adventurer 4\r\n
        Machine Name: Adventurer4\r\n
        Firmware: v2.0.9\r\n
        SN: SNADVA9501174\r\n
        X: 220 Y: 200 Z: 250\r\n
        Tool Count: 1\r\n
        Mac Address:88:A9:A7:93:86:F8\n \r\n
        ok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M115\r\n')

        return self.responseData

    def sendProgressRequest(self):
        """ Request progress data. Response will contain work progress.

        Response from printer:
        'CMD M27 Received.\r\nSD printing byte 0/100\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M27\r\n')

        return self.responseData

    def sendTempRequest(self):
        """ Request temperature data.

        Response from printer:
        'CMD M105 Received.\r\nT0:22/0 B:14/0\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M105\r\n')

        return self.responseData

    def sendPositionRequest(self):
        """ Request position data.

        Response from printer:
        'CMD M114 Received.\r\nX:19.3861 Y:54.3 Z:194.44 A:0 B:0\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M114\r\n')

        return self.responseData

    def sendStatusRequest(self):
        """ Get current status from printer.

        Response from printer:
        'CMD M119 Received.\r\n
        Endstop: X-max:0 Y-max:0 Z-max:0\r\n
        MachineStatus: READY\r\n
        MoveMode: READY\r\n
        Status: S:1 L:0 J:0 F:0\r\n
        LED: 0\r\n
        CurrentFile: \r\n
        ok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M119\r\n')

        return self.responseData

    def sendSetTemperature(self, temp):
        """[summary]

        Args:
            temp ([int]): Temperature of extruder

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage(f'~M104 S{temp} T0')

        return self.responseData

    def sendSetLedState(self, state):
        """ Turn led on or off

        Args:
            state ([bool]): Led on (True) or off (False)

        Returns:
            [string]: Return response from printer.
        """
        if state:
            self.sendMessage('~M146 r255 g255 b255 F0\r\n')
        else:
            self.sendMessage('~M146 r0 g0 b0 F0\r\n')

        return self.responseData

    def sendGetFileNames(self):
        """ Get the filenames stored on the printer.
        Response will be left decoded in the responseData variable.

        Returns:
            [list]: Filenames as string
        """
        # Don't decode this strait away.
        self.sendMessage('~M661\r\n', False)

        bytefileNames = self.responseData.split(b'::\xa3\xa3\x00\x00\x00')
        self.responseData = bytefileNames.pop(0).decode('utf8', 'ignore')

        fileNames = []
        for name in bytefileNames:
            name = name.decode('utf8', 'ignore')
            if name.find('/') not in [-1, 0]:
                name = name[name.find('/'):]
            fileNames.append(name)

        return fileNames

    def getCameraStream(self):
        """
        Returns:
            [string]: Return camera feed string.
        """
        return f"http://{self.ip}:8080/?action=stream"

    def sendPauseRequest(self):
        """ Pause current print.

        Response from printer:
        'CMD M25 Received.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M25\r\n')

        return self.responseData

    def sendContinueRequest(self):
        """ Continue current print.

        Response from printer:
        'CMD M24 Received.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M24\r\n')

        return self.responseData

    def sendPrintRequest(self, file):
        """ Print file print.

        Example command to send:
        '~M23 0:/user/My Box.gx\r\n'

        Response from printer:
        'CMD M23 Received.\r\n
        File opened: My Box.gx Size: 1613086\r\n
        File selected\r\nok\r\n'

        Args:
            file ([string]): Filename without /data/ prefix!

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage(f'~M23 0:/user/{file}\r\n')

        return self.responseData

    def sendAbortRequest(self, file):
        """ Abort file print.

        Response from printer:
        'CMD M26 Received.\r\n'

        Returns:
            [string]: Return response from printer.
        """
        self.sendMessage('~M26\r\n')

        return self.responseData
