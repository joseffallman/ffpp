
from enum import IntEnum
import logging
import re
import typing

from .Network import Network

LOG = logging.getLogger(__name__)


class ConnectionStatus(IntEnum):
    DISSCONNECTED = 0
    CONNECTED = 1
    CONTROL = 2


class field(object):
    def __init__(self, name, value, regex, flags=re.I):  # noqa
        self.name = name
        self.value = value

        if type(regex) is not re.Pattern:
            self.regex = re.compile(regex, flags)
        else:
            self.regex = regex

    def __repr__(self):
        return self.name


class temperatures(object):
    def __init__(self, name, temp, target=None):
        self.name = name.lower()
        self.now = int(temp)
        self.target = int(target)


class ToolHandler(object):

    def __init__(self):
        self._tools: dict[str, temperatures] = {}
        pass

    def __iter__(self):
        return iter(self._tools.values())

    def __len__(self):
        return len(self._tools)

    def get(self, name: typing.Union[str, int] = None):
        """Return named temperature or first one.

        Args:
            name (str | int, optional): Named temperature. Defaults to None.

        Returns:
            [temperatures]: Temperature object
        """
        if len(self._tools) <= 0:
            return None

        if not name:
            return list(self._tools.values())[0]

        if type(name) is int:
            return list(self._tools.values())[name]

        try:
            return self._tools[name.lower()]
        except KeyError:
            return None

    def add(self, t: temperatures):
        self._tools[t.name] = t

    def delete(self, name: str):
        return self._tools.pop(name.lower(), None)


class Printer(object):

    def __init__(self, ip, port=8899):
        # Instance Variables
        self.connected: ConnectionStatus = ConnectionStatus.DISSCONNECTED
        self.network = Network(ip, port)

        # Machine info fields
        self._machine_type = field(
            "Machine Type", None, "Machine Type\s?:\s?(.*?)\\r\\n")  # noqa
        self._machine_name = field(
            "Machine Name", None, "Machine Name\s?:\s?(.*?)\\r\\n")  # noqa
        self._firmware = field(
            "Firmware", None, "Firmware\s?:\s?(.*?)\\r\\n")  # noqa
        self._machine_SN = field(
            "Machine SN", None, "SN\s?:\s?(.*?)\\r\\n")  # noqa
        self._maxX = field(
            "MaxX", None, "X\s?:\s?(\d+)(?:\s|\\r\\n)")  # noqa
        self._maxY = field(
            "MaxY", None, "Y\s?:\s?(\d+)(?:\s|\\r\\n)")  # noqa
        self._maxZ = field(
            "MaxZ", None, "Z\s?:\s?(\d+)(?:\s|\\r\\n)")  # noqa
        self._extruder_count = field(
            "Extruder Count", None, "Tool Count\s?:\s?(.*?)\\r\\n")  # noqa
        self._mac_address = field(
            "Mac Address", None, "Mac Address\s?:\s?([0-9a-fA-F:]+)")  # noqa
        self._machine_status = field(
            "Machine Status", None, "MachineStatus\s?:\s?(.*?)\\r\\n")  # noqa
        self._move_mode = field(
            "Move Mode", None, "MoveMode\s?:\s?(.*?)\\r\\n")  # noqa
        self._status = field(
            "Status", None, "Status\s?:\s?(.*?)\\r\\n")  # noqa
        self._led = field(
            "LED", None, "LED\s?:\s?(.*?)\\r\\n")  # noqa
        self._current_file = field(
            "Current File", None, "CurrentFile\s?:\s?(.*?)\\r\\n")  # noqa
        self._extruder_temp = field(
            "Extruder Temp", None, "(T0)\s?:\s?(\d+)/(\d*)")  # noqa
        self._bed_temp = field(
            "Bed Temp", None, "(B)\s?:\s?(\d+)/(\d*)")  # noqa
        self._print_percent = field(
            "Print Percent", None, "byte\s?(\d+)/\d+")  # noqa

        self.extruder_tools = ToolHandler()

        self.bed_tools = ToolHandler()

    async def connect(self):
        if self.connected is ConnectionStatus.DISSCONNECTED:
            connected = False
            try:
                connected = await self.network.connect()
            except TimeoutError:
                raise

            if connected:
                self.connected = ConnectionStatus.CONNECTED

                await self.updateMachineInfo(dissconnect=False)
                await self.update(dissconnect=True)

        return True

    @property
    def machine_type(self):
        return self._machine_type.value

    @property
    def machine_name(self):
        return self._machine_name.value

    @property
    def firmware(self):
        return self._firmware.value

    @property
    def serial(self):
        return self._machine_SN.value

    @property
    def maxX(self):
        return self._maxX.value

    @property
    def maxY(self):
        return self._maxY.value

    @property
    def maxZ(self):
        return self._maxZ.value

    @property
    def extruder_count(self):
        return self._extruder_count.value

    @property
    def mac_address(self):
        return self._mac_address.value

    @property
    def machine_status(self):
        return self._machine_status.value

    @property
    def move_mode(self):
        return self._move_mode.value

    @property
    def status(self):
        return self._status.value

    @property
    def led(self):
        return self._led.value

    @property
    def current_file(self):
        return self._current_file.value

    @property
    def print_percent(self):
        return self._print_percent.value

    async def updateMachineInfo(self, dissconnect=True):
        if not self.connected:
            LOG.info("Machine is not connected")
            await self.connect()

        response = await self.network.sendInfoRequest(dissconnect=False)
        if not response:
            return

        dataField = [
            self._machine_type,
            self._machine_name,
            self._firmware,
            self._machine_SN,
            self._maxX,
            self._maxY,
            self._maxZ,
            self._extruder_count,
            self._mac_address
        ]

        for field in dataField:
            re_result = field.regex.search(response)
            if re_result:
                field.value = re_result.group(1)

        if dissconnect:
            await self.network.dissconnect()

    async def update(self, dissconnect=True):
        if not self.connected:
            LOG.info("Machine is not connected")
            await self.connect()

        # Update current status etc.
        """
        'CMD M119 Received.\r\n
        Endstop: X-max:0 Y-max:0 Z-max:0\r\n
        MachineStatus: READY\r\n
        MoveMode: READY\r\n
        Status: S:1 L:0 J:0 F:0\r\n
        LED: 0\r\n
        CurrentFile: \r\n
        ok\r\n'
        """
        response = await self.network.sendStatusRequest(dissconnect=False)
        if not response:
            return

        dataField = [
            self._machine_status,
            self._move_mode,
            self._status,
            self._led,
            self._current_file
        ]

        for field in dataField:
            re_result = field.regex.search(response)
            if re_result:
                field.value = re_result.group(1)

        # Update temperatures.
        """
        'CMD M105 Received.\r\nT0:22/0 B:14/0\r\nok\r\n'
        """
        response = await self.network.sendTempRequest(dissconnect=False)
        if not response:
            return

        re_result = self._extruder_temp.regex.search(response)
        if re_result:
            name = re_result.group(1)
            now = re_result.group(2)
            target = re_result.group(3)
            t = temperatures(name, now, target)
            self.extruder_tools.add(t)

        re_result = self._bed_temp.regex.search(response)
        if re_result:
            name = re_result.group(1)
            now = re_result.group(2)
            target = re_result.group(3)
            t = temperatures(name, now, target)
            self.bed_tools.add(t)
            # self._bed_temp.value = re_result.group(2)
            # self._bed_target_temp.value = re_result.group(3)

        # Update print progress.
        """
        'CMD M27 Received.\r\nSD printing byte 0/100\r\nok\r\n'
        """
        response = await self.network.sendProgressRequest(dissconnect=False)
        if not response:
            return

        re_result = self._print_percent.regex.search(response)
        if re_result:
            self._print_percent.value = re_result.group(1)

        if dissconnect:
            await self.network.dissconnect()
