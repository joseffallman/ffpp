import unittest
from unittest import mock

from src.ffpp.Printer import ConnectionStatus, Printer
# from src.ffpp.Network import Network
from mock_NetworkClass import mock_Network as Network
from tests.mock_NetworkClass import mock_Network_control_as_observer

PRINTER_IP = "192.168.50.64"


class test_PrinterClass(unittest.TestCase):
    """ All test will have a self printer with its mock network ready.
    """

    def setUp(self):
        self.printer = Printer(PRINTER_IP)
        self.printer.network = Network(PRINTER_IP, 8899)
        self.patch_socket = mock.patch('src.ffpp.Network.socket')
        self.patch_socket.start()

    def tearDown(self):
        self.patch_socket.stop()

    def test_ConnectionToPrinter_ConnectionStatusAsController(self):
        # Arrange

        # Act
        self.printer.connect()
        self.printer.requestControl()

        # Assert
        self.assertTrue(self.printer.connected == ConnectionStatus.CONTROL,
                        f"{self.printer.connected}")

    def test_ConnectionToPrinter_ConnectionStatusAsObserver(self):
        # Arrange
        self.printer.network = mock_Network_control_as_observer(
            PRINTER_IP, 8899
        )

        # Act
        self.printer.requestControl()

        # Assert
        self.assertTrue(self.printer.connected == ConnectionStatus.OBSERVER,
                        f"{self.printer.connected}")

    def test_ConnectionToPrinter_ConnectionFail(self):
        # Arrange
        self.printer.network = mock_Network_control_as_observer(
            PRINTER_IP, 8899
        )

        # Act
        self.printer.connect()

        # Assert
        self.assertTrue(
            self.printer.connected == ConnectionStatus.DISSCONNECTED,
            (
                f"Connected is {self.printer.connected},"
                f" expected 'OBSERVER'."
            )
        )

    def test_getBasicInfoAtConnect_getBasicInfo(self):
        # Arrage
        dataField = [
            self.printer.machine_type,
            self.printer.machine_name,
            self.printer.firmware,
            self.printer.machine_SN,
            self.printer.maxX,
            self.printer.maxY,
            self.printer.maxZ,
            self.printer.extruder_count,
            self.printer.mac_address
        ]

        # Act
        self.printer.connect()

        # Assert
        for data in dataField:
            self.assertIsNotNone(data.value, f"{data} is {data.value}")

    def test_getExtendedInfoAtConnect_getExtendedInfo(self):
        # Arrage
        dataField = [
            self.printer.machine_status,
            self.printer.move_mode,
            self.printer.status,
            self.printer.led,
            self.printer.current_file,
            self.printer.extruder_temp,
            self.printer.extruder_target_temp,
            self.printer.bed_temp,
            self.printer.bed_target_temp,
            self.printer.print_percent
        ]

        # Act
        self.printer.connect()

        # Assert
        for data in dataField:
            self.assertIsNotNone(data.value, f"{data} is {data.value}")
