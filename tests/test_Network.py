import unittest
from unittest import mock

from src.ffpp.Network import Network

PRINTER_IP = "192.168.50.64"


class TestNetworkClass(unittest.TestCase):
    """ Class to test the behavior of the Network class
    """
    @mock.patch('src.ffpp.Network.socket')
    def test_printerSendControlBeforeConnect_ConnectFirst(self, mock_socket):
        # Arrange
        net = Network(PRINTER_IP)
        mock_socket.socket().connect.return_value = True

        # Act
        response = net.sendMessage("hej")

        # Assert
        # No exception occurred, test responseData
        mock_socket.socket().connect.assert_called_once()
        self.assertTrue(response)

    @mock.patch('src.ffpp.Network.socket')
    def test_printerSendFailFirst_ReconnectAndResend(self, mock_socket):
        # Arrange
        net = Network(PRINTER_IP)
        # mock_socket.socket().connect.return_value = True
        mock_socket.socket().sendall.side_effect = [OSError, True]

        # Act
        net.connect()
        response = net.sendMessage("hej")

        # Assert
        # No exception occurred, test responseData
        self.assertEqual(mock_socket.socket().connect.call_count, 2)
        self.assertTrue(response)

    @mock.patch('src.ffpp.Network.socket')
    def test_printerSendFailFirst_UnableToReconnectAndResend(self, mock_socket):  # noqa
        # Arrange
        net = Network(PRINTER_IP)
        mock_socket.socket().connect.side_effect = [True, OSError]
        mock_socket.socket().sendall.side_effect = [OSError, True]

        # Act
        net.connect()
        response = net.sendMessage("hej")

        # Assert
        # No exception occurred, test responseData
        self.assertEqual(mock_socket.socket().connect.call_count, 2)
        self.assertFalse(response)


class TestNetworkCommunicateWithPrinter(unittest.TestCase):
    """ Class to test the communication with a real Flashforge printer."""

    def test_printerConnect_noException(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        successfull = net.connect()

        # Assert
        # No exception occurred, test responseData.
        self.assertTrue(successfull, (
            "Unable to connect to printer.",
            "Check Power/IP/ethernet/wlan connection etc. "
        ))

    def test_getInfofromPrinter_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = net.sendInfoRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M115 Received" in response,
                        "Wrong message from printer.")

    def test_getProgress_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = net.sendProgressRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M27 Received" in response,
                        "Wrong message from printer.")

    def test_getTemperature_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = net.sendTempRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M105 Received" in response,
                        "Wrong message from printer.")

    def test_getPosiotion_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = net.sendPositionRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M114 Received" in response,
                        "Wrong message from printer.")

    def test_getStatus_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = net.sendStatusRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M119 Received" in response,
                        "Wrong message from printer.")

    def test_getFileList_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        files = net.sendGetFileNames()

        # Assert
        self.assertIsNotNone(net.responseData, "responseData is None")
        self.assertTrue("CMD M661 Received" in net.responseData,
                        "Wrong message from printer.")
        self.assertTrue(len(files) > 0, "There is no files on printer?")

    def test_setTemperature_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)
        net.sendControlRequest()

        # Act
        response = net.sendSetTemperature(40)
        net.sendTempRequest()
        # response2 = net.responseData
        net.sendSetTemperature(0)  # Restore temperature.

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M104 Received" in response,
                        "Wrong message from printer.")
        # self.assertTrue("T0:40" in response2, "Temperature not set")

    def test_pausePrint_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)
        net.sendControlRequest()

        # Act
        response = net.sendPauseRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M25 Received" in response,
                        "Wrong message from printer.")

    def test_continuePrint_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)
        net.sendControlRequest()

        # Act
        response = net.sendContinueRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M24 Received" in response,
                        "Wrong message from printer.")
