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
    RESPONSE_sendProgressRequest2,
    RESPONSE_sendSetTemperature,
    RESPONSE_sendStatusRequest,
    RESPONSE_sendStatusRequest2,
    RESPONSE_sendTempRequest,
    RESPONSE_sendTempRequest2,
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
            self.printer.connected == ConnectionStatus.DISCONNECTED,
            f"{self.printer.connected}"
        )

    async def test_updateMachineInfoTimeoutToPrinter_Exception(self):
        # Arrange
        self.mock_net().connect.side_effect = TimeoutError

        # Act
        with self.assertRaises(TimeoutError):
            await self.printer.updateMachineInfo()

        # Assert
        self.assertTrue(
            self.printer.connected == ConnectionStatus.DISCONNECTED,
            f"{self.printer.connected}"
        )

    async def test_updateTimeoutToPrinter_Exception(self):
        # Arrange
        self.mock_net().connect.side_effect = TimeoutError

        # Act
        with self.assertRaises(TimeoutError):
            await self.printer.update()

        # Assert
        self.assertTrue(
            self.printer.connected == ConnectionStatus.DISCONNECTED,
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
        self.mock_net().sendStatusRequest. \
            return_value = RESPONSE_sendStatusRequest
        self.mock_net().sendProgressRequest. \
            return_value = RESPONSE_sendProgressRequest

        # Act
        await self.printer.connect()

        # Assert
        self.assertEqual(self.printer.machine_status, "READY")
        self.assertEqual(self.printer.move_mode, "READY")
        self.assertEqual(self.printer.status, "S:1 L:0 J:0 F:0")
        self.assertEqual(self.printer.led, "0")
        self.assertEqual(self.printer.job_file, "")
        self.assertEqual(self.printer.print_percent, "0")

    async def test_getUpdateProgress_getCorrectInfo(self):
        # Arrage
        self.mock_net().sendStatusRequest. \
            return_value = RESPONSE_sendStatusRequest2
        self.mock_net().sendProgressRequest. \
            return_value = RESPONSE_sendProgressRequest2

        # Act
        await self.printer.connect()

        # Assert
        self.assertEqual(
            self.printer.machine_status,
            "BUILDING_FROM_SD", "Machine status gave wrong response"
        )
        self.assertEqual(
            self.printer.move_mode, "MOVING",
            "Move mode gave wrong response"
        )
        self.assertEqual(
            self.printer.status, "S:1 L:0 J:0 F:0",
            "Status gave wrong response"
        )
        self.assertEqual(
            self.printer.led, "1",
            "Led gave wrong response"
        )
        self.assertEqual(
            self.printer.job_file, "RussianDollMazeModels.gx",
            "Current file gave wrong response"
        )
        self.assertEqual(
            self.printer.print_percent, "11",
            "Percent gave wrong response"
        )
        self.assertEqual(
            self.printer.print_layer, "44",
            "Print layer gave wrong response"
        )
        self.assertEqual(
            self.printer.job_layers, "419",
            "Total layer gave wrong response"
        )

    async def test_getExtrudersAndBedsTempAM5_getTemp(self):
        # Arrage
        self.mock_net().sendTempRequest. \
            return_value = RESPONSE_sendTempRequest2

        # Act
        await self.printer.update()
        extruder = self.printer.extruder_tools.get()
        bed = self.printer.bed_tools.get()

        # Assert
        self.assertTrue(len(self.printer.extruder_tools) == 1)
        self.assertTrue(extruder.now == 104.5)
        self.assertTrue(extruder.target == 225.0)
        self.assertTrue(len(self.printer.bed_tools) == 1)
        self.assertTrue(bed.now == 51.3)
        self.assertTrue(bed.target == 50.0)

    async def test_getExtrudersAndBedsTemp_getTemp(self):
        # Arrage

        # Act
        await self.printer.update()
        extruder = self.printer.extruder_tools.get()
        bed = self.printer.bed_tools.get()

        # Assert
        self.assertTrue(len(self.printer.extruder_tools) == 1)
        self.assertTrue(extruder.now == 22)
        self.assertTrue(extruder.target == 0)
        self.assertTrue(len(self.printer.bed_tools) == 1)
        self.assertTrue(bed.now == 14)
        self.assertTrue(bed.target == 0)

    async def test_toolHandlerAddsameName_CorrectCount(self):
        # Arrange
        from src.ffpp.Printer import ToolHandler, temperatures
        th = ToolHandler()

        # Act
        th.add(temperatures("extruder", "5", "210"))
        th.add(temperatures("extruder", "15", "210"))

        # Assert
        self.assertTrue(
            len(th) == 1, f"Toolhandler is only {len(th)}, expected 1")

    async def test_toolHandlerAdd_CorrectCount(self):
        # Arrange
        from src.ffpp.Printer import ToolHandler, temperatures
        th = ToolHandler()

        # Act
        th.add(temperatures("extruder", "5", "210"))
        th.add(temperatures("extruder2", "15", "210"))

        # Assert
        self.assertTrue(
            len(th) == 2, f"Toolhandler is only {len(th)}, expected 2")

    async def test_toolHandlerGet_CorrectReturn(self):
        # Arrange
        from src.ffpp.Printer import ToolHandler, temperatures
        th = ToolHandler()
        extruder1 = temperatures("exTruder1", "5", "210")
        extruder2 = temperatures("exTruder2", "15", "210")
        th.add(extruder1)
        th.add(extruder2)

        # Act
        ret_extruder1 = th.get()  # Return first
        ret_extruder2 = th.get("Extruder2")  # Return extruder2
        ret_extruder3 = th.get(1)  # Return extruder2
        ret_extruder85 = th.get("Extruder85")  # Return None

        # Assert
        self.assertTrue(
            ret_extruder1 == extruder1,
            "Toolhandler did'nt return first extruder."
        )
        self.assertTrue(
            ret_extruder2 == extruder2,
            "Toolhandler did'nt return specific extruder."
        )
        self.assertTrue(
            ret_extruder3 == extruder2,
            "Toolhandler did'nt return correct index."
        )
        self.assertIsNone(ret_extruder85)

    async def test_toolHandlerDelete_deleteCorrect(self):
        # Arrange
        from src.ffpp.Printer import ToolHandler, temperatures
        th = ToolHandler()
        extruder1 = temperatures("exTruder1", "5", "210")
        extruder2 = temperatures("exTruder2", "15", "210")
        extruder3 = temperatures("exTruder3", "15", "210")
        th.add(extruder1)
        th.add(extruder2)
        th.add(extruder3)

        # Act
        ret_extruder2 = th.delete("extruder2")  # Delete and return extruder2
        ret_extruder85 = th.delete("extruder85")  # retrun None

        # Assert
        self.assertTrue(
            ret_extruder2 == extruder2,
            "Toolhandler did'nt return specific extruder."
        )
        self.assertTrue(
            len(th) == 2,
            f"Toolhandler is only {len(th)}, expected 2"
        )
        self.assertIsNone(ret_extruder85)

    async def test_toolHandlerIter_CorrectIter(self):
        # Arrange
        from src.ffpp.Printer import ToolHandler, temperatures
        th = ToolHandler()
        extruder1 = temperatures("exTruder1", "5", "210")
        extruder2 = temperatures("exTruder2", "15", "210")
        assert_obj = [extruder1, extruder2]
        temp_obj = []

        # Act
        th.add(extruder1)
        th.add(extruder2)
        for t in th:
            temp_obj.append(t)

        # Assert
        self.assertTrue(
            len(temp_obj) == 2, f"Toolhandler is only {len(th)}, expected 2")
        self.assertListEqual(temp_obj, assert_obj)
