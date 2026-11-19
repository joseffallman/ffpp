import asyncio
import contextlib
import logging
import typing

LOG = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
# Max time to wait for the printer to start answering a command.
RESPONSE_TIMEOUT = 5
# Once the printer started to answer, a response without a trailing "ok" is
# considered complete when no more data arrives within this time.
IDLE_TIMEOUT = 0.5
RESPONSE_END = b'ok\r\n'


class Network(object):
    def __init__(self, ip, port=8899):
        self.ip = ip
        self.port = port
        self.connection = None
        self.responseData: typing.Union[list[bytes], None] = None
        self._reader = None
        self._writer = None
        self._lock = None

    @property
    def lock(self) -> asyncio.Lock:
        """Lock that makes each sendMessage call exclusive.

        Created on first use, so it belongs to the running event loop.
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def connect(self):
        """Open a new connection to the printer.

        Raises:
            TimeoutError: Unable to connect.
        """
        async with self.lock:
            await self._connect()
        return True

    async def disconnect(self):
        async with self.lock:
            self._close()
        return True

    async def sendMessage(
        self,
        messages: typing.Union[typing.List[str], str],
        disconnect=True,
        wait_for_idle=False,
    ):
        """Send messages and store one complete response per message.

        The messages are sent as one exclusive sequence, other calls wait
        until it is done. On any error the connection is closed, so the next
        call starts with a new connection.

        Args:
            messages: Message or list of messages to send.
            disconnect: Close the connection when done.
            wait_for_idle: Read until the printer stops sending, for
                responses that continue after the "ok".

        Raises:
            TimeoutError: The printer didn't answer.
            ConnectionError: Unable to send or the printer closed the
                connection.
        """
        if type(messages) is not list:
            messages = [messages]

        async with self.lock:
            self.responseData = []
            try:
                if self.connection is None:
                    await self._connect()
                for message in messages:
                    self._writer.write(message.encode())
                    await self._writer.drain()  # Wait for it to be sent.
                    self.responseData.append(
                        await self._readResponse(wait_for_idle)
                    )
            except (TimeoutError, ConnectionError, asyncio.CancelledError):
                LOG.debug("Unable to send.")
                self._close()
                raise
            except OSError as e:
                LOG.debug("Unable to send.")
                self._close()
                raise ConnectionError(e) from e

            if disconnect:
                self._close()

        return len(self.responseData) > 0

    async def _connect(self):
        self._close()
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=CONNECT_TIMEOUT
            )
        except (OSError, asyncio.TimeoutError) as e:
            LOG.debug("Unable to connect")
            raise TimeoutError(e) from e
        self.connection = self._writer

    def _close(self):
        if self._writer is not None:
            with contextlib.suppress(OSError, RuntimeError):
                self._writer.close()
        self._reader = None
        self._writer = None
        self.connection = None

    async def _readResponse(self, wait_for_idle=False) -> bytes:
        """Read until the response ends with "ok" or the printer goes quiet."""
        response = b''
        timeout = RESPONSE_TIMEOUT
        while True:
            try:
                chunk = await asyncio.wait_for(
                    self._reader.read(4096), timeout=timeout
                )
            except asyncio.TimeoutError:
                if response:
                    return response
                raise TimeoutError("No response from printer")
            if not chunk:
                if response:
                    return response
                raise ConnectionError("Connection closed by printer")
            response += chunk
            if not wait_for_idle and response.endswith(RESPONSE_END):
                return response
            timeout = IDLE_TIMEOUT

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
        state = 255 if state else 0
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
        # The file names are sent after the "ok".
        await self.sendMessage('~M661\r\n', disconnect, wait_for_idle=True)

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
