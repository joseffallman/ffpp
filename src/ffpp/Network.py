import logging
import asyncio
import typing

LOG = logging.getLogger(__name__)


class Network(object):
    def __init__(self, ip, port=8899):
        self.ip = ip
        self.port = port
        self.connection = None
        self.responseData: typing.Union[list[bytes], None] = None

    async def connect(self):
        self.connection = asyncio.open_connection(
            self.ip,
            self.port,
        )
        try:
            self._reader, self._writer = await asyncio.wait_for(
                self.connection,
                timeout=3
            )
        except Exception as e:  # CancelError and TimeoutError
            LOG.debug("Unable to connect")
            self.connection = None
            raise TimeoutError(e) from e

        return True

    async def disconnect(self):
        try:
            self._writer.close()
        except Exception:
            pass
        self.connection = None
        return True

    async def sendMessage(self, messages: typing.List[str], disconnect=True):
        self.responseData = []

        if type(messages) is not list:
            messages = [messages]

        if self.connection is None:
            await self.connect()

        # Send all messages.
        try:
            while len(messages) > 0:
                send = messages.pop(0)
                self._writer.write(send.encode())
                await self._writer.drain()  # Wait for it to be sent.
                data = await self._reader.read(1024)
                if data:
                    self.responseData.append(data)
        except Exception as e:
            LOG.debug("Unable to send.")
            await self.disconnect()
            raise ConnectionError(e) from e

        if disconnect:
            await self.disconnect()

        if self.responseData and len(self.responseData) > 0:
            return True
        return False

    async def sendControlRequest(self, disconnect=True):
        """Send Control message to printer.

        Response from printer is something like
            'CMD M601 Received.\r\nControl failed.\r\nok\r\n'
        or
            'CMD M601 Received.\r\nControl Success V2.1.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        await self.sendMessage(self._getControlRequestMessage, disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return None

    @property
    def _getControlRequestMessage(self):
        return '~M601 S1\r\n'

    async def sendControlRelease(self, disconnect=True):
        """ Release control of printer. You will only
        be able to watch printer status when you dont have
        the control.

        Returns:
            [string]: Return response from printer.
        """
        await self.sendMessage(self._getControlReleaseMessage, disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return None

    @property
    def _getControlReleaseMessage(self):
        return '~M602\r\n'

    async def sendInfoRequest(self, disconnect=True):
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
        await self.sendMessage('~M115\r\n', disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return ""

    async def sendProgressRequest(self, disconnect=True):
        """ Request progress data. Response will contain work progress.

        Response from printer:
        'CMD M27 Received.\r\nSD printing byte 0/100\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        await self.sendMessage('~M27\r\n', disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return ""

    async def sendTempRequest(self, disconnect=True):
        """ Request temperature data.

        Response from printer:
        'CMD M105 Received.\r\nT0:22/0 B:14/0\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        await self.sendMessage('~M105\r\n', disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return ""

    async def sendPositionRequest(self, disconnect=True):
        """ Request position data.

        Response from printer:
        'CMD M114 Received.\r\nX:19.3861 Y:54.3 Z:194.44 A:0 B:0\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        await self.sendMessage('~M114\r\n', disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return ""

    async def sendStatusRequest(self, disconnect=True):
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
        await self.sendMessage('~M119\r\n', disconnect)

        if self.responseData and len(self.responseData) > 0:
            return self.responseData[0].decode('utf8', 'ignore')
        return ""

    async def sendSetTemperature(self, temp, disconnect=True):
        """[summary]

        Args:
            temp ([int]): Temperature of extruder

        Returns:
            [string]: Return response from printer.
        """
        messages = [
            self._getControlRequestMessage,
            f'~M104 S{temp} T0',
            self._getControlReleaseMessage,
        ]
        await self.sendMessage(messages, disconnect)

        if len(self.responseData) > 1:
            return self.responseData[1].decode('utf8', 'ignore')
        return ""

    async def sendSetLedState(self, state, disconnect=True):
        """ Turn led on or off

        Args:
            state ([bool]): Led on (True) or off (False)

        Returns:
            [string]: Return response from printer.
        """
        messages = [
            self._getControlRequestMessage,
            f'~M146 r{state} g{state} b{state} F0\r\n',
            self._getControlReleaseMessage,
        ]
        await self.sendMessage(messages, disconnect)

        if len(self.responseData) > 1:
            return self.responseData[1].decode('utf8', 'ignore')
        return ""

    async def sendGetFileNames(self, disconnect=True):
        """ Get the filenames stored on the printer.
        Response will be left decoded in the responseData variable.

        Returns:
            [list]: Filenames as string
        """
        # Don't decode this strait away.
        await self.sendMessage('~M661\r\n', disconnect)

        if self.responseData and len(self.responseData) > 0:
            response = self.responseData[0]
        else:
            return None
        bytefileNames = response.split(b'::\xa3\xa3\x00\x00\x00')
        self.responseData = bytefileNames.pop(0).decode('utf8', 'ignore')

        fileNames = []
        for name in bytefileNames:
            name = name.decode('utf8', 'ignore')
            if name.find('/') not in [-1, 0]:
                name = name[name.find('/'):]
            fileNames.append(name)

        return fileNames

    async def getCameraStream(self):
        """
        Returns:
            [string]: Return camera feed string.
        """
        return f"http://{self.ip}:8080/?action=stream"

    async def sendPauseRequest(self, disconnect=True):
        """ Pause current print.

        Response from printer:
        'CMD M25 Received.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        messages = [
            self._getControlRequestMessage,
            '~M25\r\n',
            self._getControlReleaseMessage,
        ]
        await self.sendMessage(messages, disconnect)

        if len(self.responseData) > 1:
            return self.responseData[1].decode('utf8', 'ignore')
        return ""

    async def sendContinueRequest(self, disconnect=True):
        """ Continue current print.

        Response from printer:
        'CMD M24 Received.\r\nok\r\n'

        Returns:
            [string]: Return response from printer.
        """
        messages = [
            self._getControlRequestMessage,
            '~M24\r\n',
            self._getControlReleaseMessage,
        ]
        await self.sendMessage(messages, disconnect)

        if len(self.responseData) > 1:
            return self.responseData[1].decode('utf8', 'ignore')
        return ""

    async def sendPrintRequest(self, file, disconnect=True):
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
        messages = [
            self._getControlRequestMessage,
            f'~M23 0:/user/{file}\r\n',
            self._getControlReleaseMessage,
        ]
        await self.sendMessage(messages, disconnect)

        if len(self.responseData) > 1:
            return self.responseData[1].decode('utf8', 'ignore')
        return ""

    async def sendAbortRequest(self, disconnect=True):
        """ Abort file print.

        Response from printer:
        'CMD M26 Received.\r\n'

        Returns:
            [string]: Return response from printer.
        """
        messages = [
            self._getControlRequestMessage,
            '~M26\r\n',
            self._getControlReleaseMessage,
        ]
        await self.sendMessage(messages, disconnect)

        if len(self.responseData) > 1:
            return self.responseData[1].decode('utf8', 'ignore')
        return ""
