import unittest
from unittest import mock

from src.ffpp.Printer import ConnectionStatus
from src.ffpp.Printer import Printer
from tests.const_NetworkResponse import (
    RESPONSE_sendAbortRequest,
    RESPONSE_sendContinueRequest,
    RESPONSE_sendControlRelease,
    RESPONSE_sendControlRequestTrue,
    # RESPONSE_sendGetFileNames,
    RESPONSE_sendInfoRequest,
    RESPONSE_sendPauseRequest,
    RESPONSE_sendPositionRequest,
    RESPONSE_sendPrintRequest,
    RESPONSE_sendProgressRequest,
    RESPONSE_sendSetTemperature,
    RESPONSE_sendStatusRequest,
    RESPONSE_sendTempRequest,
    RESPONSE_sendsetLedState
)

PRINTER_IP = "192.168.50.64"


class test_PrinterClass(unittest.IsolatedAsyncioTestCase):
    """ All test will have a self printer with its mock network ready.
    """

    def setUp(self):
        # Patch the Network class in Printer.py
        self.patch_net = mock.patch(
            'src.ffpp.Printer.Network',
            spec=True,
        )
        self.mock_net = self.patch_net.start()
        self.mock_net().connect.return_value = True
        self.mock_net().sendMessage.return_value = True
        self.setResponse()
        self.printer = Printer(PRINTER_IP)

    def tearDown(self):
        self.patch_net.stop()

    def setResponse(self):
        self.mock_net().sendControlRequest. \
            return_value = RESPONSE_sendControlRequestTrue

        self.mock_net().sendControlRelease. \
            return_value = RESPONSE_sendControlRelease

        self.mock_net().sendInfoRequest. \
            return_value = RESPONSE_sendInfoRequest

        self.mock_net().sendProgressRequest. \
            return_value = RESPONSE_sendProgressRequest

        self.mock_net().sendTempRequest. \
            return_value = RESPONSE_sendTempRequest

        self.mock_net().sendPositionRequest. \
            return_value = RESPONSE_sendPositionRequest

        self.mock_net().sendStatusRequest. \
            return_value = RESPONSE_sendStatusRequest

        self.mock_net().sendSetTemperature. \
            return_value = RESPONSE_sendSetTemperature

        self.mock_net().sendSetLedState. \
            return_value = RESPONSE_sendsetLedState

        self.mock_net().sendGetFileNames. \
            return_value = []

        self.mock_net().sendPauseRequest. \
            return_value = RESPONSE_sendPauseRequest

        self.mock_net().sendContinueRequest. \
            return_value = RESPONSE_sendContinueRequest

        self.mock_net().sendPrintRequest. \
            return_value = RESPONSE_sendPrintRequest

        self.mock_net().sendAbortRequest. \
            return_value = RESPONSE_sendAbortRequest

    # @mock.patch.object(Network, "connect", mock.AsyncMock(return_value=True))
    async def test_ConnectionToPrinter_Connected(self):
        # Arrange

        # Act
        await self.printer.connect()

        # Assert
        self.assertTrue(self.printer.connected == ConnectionStatus.CONNECTED,
                        f"{self.printer.connected}")

    async def test_ConnectTimeoutToPrinter_Exception(self):
        # Arrange
        self.mock_net().connect.side_effect = TimeoutError

        # Act
        with self.assertRaises(TimeoutError):
            await self.printer.connect()

        # Assert
        self.assertTrue(
            self.printer.connected == ConnectionStatus.DISSCONNECTED,
            f"{self.printer.connected}"
        )

    async def test_getBasicInfoAtConnect_getBasicInfo(self):
        # Arrage

        # Act
        await self.printer.connect()
        dataField = [
            self.printer.machine_type,
            self.printer.machine_name,
            self.printer.firmware,
            self.printer.serial,
            self.printer.maxX,
            self.printer.maxY,
            self.printer.maxZ,
            self.printer.extruder_count,
            self.printer.mac_address
        ]

        # Assert
        for data in dataField:
            self.assertIsNotNone(data, f"{data} is {data}")

    async def test_getExtendedInfoAtConnect_getExtendedInfo(self):
        # Arrage

        # Act
        await self.printer.connect()
        dataField = [
            self.printer.machine_status,
            self.printer.move_mode,
            self.printer.status,
            self.printer.led,
            self.printer.current_file,
            # self.printer.extruder_temp,
            # self.printer.extruder_target_temp,
            # self.printer.bed_temp,
            # self.printer.bed_target_temp,
            self.printer.print_percent
        ]

        # Assert
        for data in dataField:
            self.assertIsNotNone(data, f"{data} is {data}")

    async def test_getExtrudersAndBedsTemp_getTemp(self):
        # Arrage

        # Act
        await self.printer.update()
        extruder = list(self.printer.extruders.values())[0]
        bed = list(self.printer.beds.values())[0]

        # Assert
        self.assertTrue(len(self.printer.extruders) == 1)
        self.assertTrue(extruder.now == 22)
        self.assertTrue(extruder.target == 0)
        self.assertTrue(len(self.printer.beds) == 1)
        self.assertTrue(bed.now == 14)
        self.assertTrue(bed.target == 0)
