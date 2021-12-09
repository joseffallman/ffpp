import socket
import logging
import re

LOG = logging.getLogger(__name__)


class mock_Network(object):
    def __init__(self, ip, port=8899):
        self.ip = ip
        self.port = port
        self.connection = None
        self.responseData = None

    def __del__(self):
        self.connection.close()

    def connect(self):
        # Don't communicate with printer in this MOCK class.

        self.connection = socket.socket()
        self.connection.settimeout(5)
        try:
            # self.connection.connect((self.ip, self.port))
            pass
        except socket.error:
            LOG.info("Unable to connect")
            self.connection = None
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

        # Don't communicate with the printer in this MOCK class

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
        self.responseData = (
            'CMD M601 Received.\r\n'
            'Control Success V2.1.\r\n'
            'ok\r\n'
        )

        return self.responseData

    def sendControlRelease(self):
        self.sendMessage('~M602\r\n')
        self.responseData = 'CMD 602 Received.\r\nok\r\n'

        return self.responseData

    def sendInfoRequest(self):
        self.sendMessage('~M115\r\n')
        self.responseData = (
            'CMD M115 Received.\r\n'
            'Machine Type: Flashforge Adventurer 4\r\n'
            'Machine Name: Adventurer4\r\n'
            'Firmware: v2.0.9\r\n'
            'SN: SNADVA9501174\r\n'
            'X: 220 Y: 200 Z: 250\r\n'
            'Tool Count: 1\r\n'
            'Mac Address:88:A9:A7:93:86:F8\n \r\n'
            'ok\r\n'
        )

        return self.responseData

    def sendProgressRequest(self):
        self.sendMessage('~M27\r\n')
        self.responseData = (
            'CMD M27 Received.\r\nSD printing byte 0/100\r\nok\r\n'
        )

        return self.responseData

    def sendTempRequest(self):
        self.sendMessage('~M105\r\n')
        self.responseData = 'CMD M105 Received.\r\nT0:22/0 B:14/0\r\nok\r\n'

        temps = re.findall(r'([TB]\d?):(\d+)/(\d+)', self.responseData)

        ret = []
        for temp in temps:
            ret.append({
                'Object': temp[0],
                'Temperature': temp[1],
                'TargetTemp': temp[2]
            })
        return self.responseData

    def sendPositionRequest(self):
        self.sendMessage('~M114\r\n')
        self.responseData = (
            'CMD M114 Received.\r\n'
            'X:19.3861 Y:54.3 Z:194.44 A:0 B:0\r\n'
            'ok\r\n'
        )

        return self.responseData

    def sendStatusRequest(self):
        self.sendMessage('~M119\r\n')
        self.responseData = (
            'CMD M119 Received.\r\n'
            'Endstop: X-max:0 Y-max:0 Z-max:0\r\n'
            'MachineStatus: READY\r\n'
            'MoveMode: READY\r\n'
            'Status: S:1 L:0 J:0 F:0\r\n'
            'LED: 0\r\n'
            'CurrentFile: \r\n'
            'ok\r\n'
        )

        return self.responseData

    def sendSetTemperature(self, temp):
        self.sendMessage(f'~M104 S{temp} T0')
        self.responseData = 'CMD 104 Received.\r\nok\r\n'

        return self.responseData

    def sendSetLedState(self, state):
        if state:
            self.sendMessage('~M146 r255 g255 b255 F0\r\n')
        else:
            self.sendMessage('~M146 r0 g0 b0 F0\r\n')
        self.responseData = 'CMD 146 Received.\r\nok\r\n'

        return self.responseData

    def sendGetFileNames(self):
        self.sendMessage('~M661\r\n', False)

        self.responseData = 'CMD 661 Received.\r\nok\r\n'

        fileNames = []

        return fileNames

    def getCameraStream(self):
        """
        Returns:
            [string]: Return camera feed string.
        """
        return f"http://{self.ip}:8080/?action=stream"

    def sendPauseRequest(self):
        self.sendMessage('~M25\r\n')
        self.responseData = 'CMD M25 Received.\r\nok\r\n'

        return self.responseData

    def sendContinueRequest(self):
        self.sendMessage('~M24\r\n')
        self.responseData = 'CMD M24 Received.\r\nok\r\n'

        return self.responseData

    def sendPrintRequest(self, file):
        self.sendMessage(f'~M23 0:/user/{file}\r\n')
        self.responseData = ('CMD M23 Received.\r\n'
                             'File opened: My Box.gx Size: 1613086\r\n'
                             'File selected\r\nok\r\n')

        return self.responseData

    def sendAbortRequest(self, file):
        self.sendMessage('~M26\r\n')
        self.responseData = 'CMD M26 Received.\r\n'

        return self.responseData


class mock_Network_control_as_observer(mock_Network):
    def __init__(self, ip, port=8899):
        super().__init__(ip, port=port)

    def connect(self):
        # Don't communicate with printer in this MOCK class.
        # This will simulate a connection timeout.

        self.connection = socket.socket()
        self.connection.settimeout(5)
        try:
            # self.connection.connect((self.ip, self.port))
            raise socket.timeout
        except socket.error:
            LOG.info("Unable to connect")
            self.connection = None
            return False
        return True

    def sendControlRequest(self):
        """Send Control message to printer.

        Response from printer is something like
            'CMD M601 Received.\r\nControl failed.\r\nok\r\n'
        or
            'CMD M601 Received.\r\nControl Success V2.1.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        # self.sendMessage('~M601 S1\r\n')
        self.responseData = (
            'CMD M601 Received.\r\n'
            'Control failed.\r\n'
            'ok\r\n'
        )

        return self.responseData
