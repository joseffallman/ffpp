
from enum import IntEnum
import logging
import re

from .Network import Network

LOG = logging.getLogger(__name__)


class ConnectionStatus(IntEnum):
    DISSCONNECTED = 0
    OBSERVER = 1
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


class Printer(object):
    def __init__(self, ip, port=8899):
        # Instance Variables
        self.connected = ConnectionStatus.DISSCONNECTED
        self.network = Network(ip, port)

        # Machine info fields
        self.machine_type = field(
            "Machine Type", None, "Machine Type\s?:\s?(.*?)\\r\\n")  # noqa
        self.machine_name = field(
            "Machine Name", None, "Machine Name\s?:\s?(.*?)\\r\\n")  # noqa
        self.firmware = field(
            "Firmware", None, "Firmware\s?:\s?(.*?)\\r\\n")  # noqa
        self.machine_SN = field(
            "Machine SN", None, "SN\s?:\s?(.*?)\\r\\n")  # noqa
        self.maxX = field(
            "MaxX", None, "X\s?:\s?(\d+)(?:\s|\\r\\n)")  # noqa
        self.maxY = field(
            "MaxY", None, "Y\s?:\s?(\d+)(?:\s|\\r\\n)")  # noqa
        self.maxZ = field(
            "MaxZ", None, "Z\s?:\s?(\d+)(?:\s|\\r\\n)")  # noqa
        self.extruder_count = field(
            "Extruder Count", None, "Tool Count\s?:\s?(.*?)\\r\\n")  # noqa
        self.mac_address = field(
            "Mac Address", None, "Mac Address\s?:\s?([0-9a-fA-F:]+)")  # noqa
        self.machine_status = field(
            "Machine Status", None, "MachineStatus\s?:\s?(.*?)\\r\\n")  # noqa
        self.move_mode = field(
            "Move Mode", None, "MoveMode\s?:\s?(.*?)\\r\\n")  # noqa
        self.status = field(
            "Status", None, "Status\s?:\s?(.*?)\\r\\n")  # noqa
        self.led = field(
            "LED", None, "LED\s?:\s?(.*?)\\r\\n")  # noqa
        self.current_file = field(
            "Current File", None, "CurrentFile\s?:\s?(.*?)\\r\\n")  # noqa
        self.extruder_temp = field(
            "Extruder Temp", None, "T0\s?:\s?(\d+)/(\d*)")  # noqa
        self.extruder_target_temp = field(
            "Extruder Target Temp", None, "T0\s?:\s?\d+/(\d*)")  # noqa
        self.bed_temp = field(
            "Bed Temp", None, "B\s?:\s?(\d+)/(\d*)")  # noqa
        self.bed_target_temp = field(
            "Bed Target Temp", None, "B\s?:\s?\d+/(\d*)")  # noqa
        self.print_percent = field(
            "Print Percent", None, "byte\s?(\d)/\d+")  # noqa

    def connect(self):
        if self.connected is ConnectionStatus.DISSCONNECTED:
            if self.network.connect():
                self.connected = ConnectionStatus.OBSERVER

                self.updateMachineInfo()
                self.update()

                return True
        return False

    def requestControl(self):
        response = self.network.sendControlRequest()
        if "Control Success" in response:
            self.connected = ConnectionStatus.CONTROL
        elif "Control failed" in response:
            self.connected = ConnectionStatus.OBSERVER

    def updateMachineInfo(self):
        if not self.connected:
            LOG.info("Machine is not connected")
            if not self.connect():
                return

        response = self.network.sendInfoRequest()
        dataField = [
            self.machine_type,
            self.machine_name,
            self.firmware,
            self.machine_SN,
            self.maxX,
            self.maxY,
            self.maxZ,
            self.extruder_count,
            self.mac_address
        ]

        for field in dataField:
            re_result = field.regex.search(response)
            if re_result:
                field.value = re_result.group(1)

    def update(self):
        if not self.connected:
            LOG.info("Machine is not connected")
            self.connect()

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
        response = self.network.sendStatusRequest()

        dataField = [
            self.machine_status,
            self.move_mode,
            self.status,
            self.led,
            self.current_file
        ]

        for field in dataField:
            re_result = field.regex.search(response)
            if re_result:
                field.value = re_result.group(1)

        # Update temperatures.
        """
        'CMD M105 Received.\r\nT0:22/0 B:14/0\r\nok\r\n'
        """
        response = self.network.sendTempRequest()

        dataField = [
            self.extruder_temp,
            self.extruder_target_temp,
            self.bed_temp,
            self.bed_target_temp
        ]

        re_result = self.extruder_temp.regex.search(response)
        if re_result:
            self.extruder_temp.value = re_result.group(1)
            self.extruder_target_temp.value = re_result.group(2)

        re_result = self.extruder_temp.regex.search(response)
        if re_result:
            self.bed_temp.value = re_result.group(1)
            self.bed_target_temp.value = re_result.group(2)

        # Update print progress.
        """
        'CMD M27 Received.\r\nSD printing byte 0/100\r\nok\r\n'
        """
        response = self.network.sendProgressRequest()

        re_result = self.print_percent.regex.search(response)
        if re_result:
            self.print_percent.value = re_result.group(1)
