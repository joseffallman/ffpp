import unittest

from src.ffpp.Network import Network

PRINTER_IP = "192.168.50.64"


class TestNetwork(unittest.TestCase):
    """ Class to test the communication with a real Flashforge printer."""

    def test_printerConnect_noException(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        try:
            net.connect()
        except Exception:
            self.fail("Network.connect() throw an exception.")

        # Assert
        # No exception occurred, test responseData.
        self.assertIsNone(net.responseData, "responseData is None")

    def test_printerSendControlBeforeConnect_noException(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        try:
            response = net.sendControlRequest()
        except Exception:
            self.fail("sendControlMessage throw an exception.")

        # Assert
        # No exception occurred, test responseData.
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M601 Received" in response,
                        "Wrong message from printer.")

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
