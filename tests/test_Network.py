import socket
import typing
import unittest
from unittest import mock
import asyncio

from src.ffpp.Network import Network

PRINTER_IP = "192.168.50.64"
PRINTER_PORT = 8899


class TestNetworkClass(unittest.IsolatedAsyncioTestCase):
    """ Class to test the behavior of the Network class
    """

    def setUp(self):
        self.network = Network(PRINTER_IP, 8899)
        self.patch_con = mock.patch(
            'src.ffpp.Network.asyncio',
            new_callable=mock.AsyncMock
        )
        self.mock_con = self.patch_con.start()
        self.mockReturnValue()

    def tearDown(self):
        self.patch_con.stop()

    def mockReturnValue(
        self,
        returnMessage: typing.Union[typing.List[str], str] = []
    ):
        # Mock socket connection.
        reader = mock.AsyncMock()
        # reader.read.return_value = returnMessage.encode('utf-8')

        if type(returnMessage) is not list:
            returnMessage = [returnMessage]

        ret = []
        for msg in returnMessage:
            ret.append(msg.encode('utf-8'))

        reader.read.side_effect = ret  # returnMessage.encode('utf-8')
        self.mock_con.wait_for.return_value = (
            reader,  # reader
            mock.AsyncMock(),  # writer
        )

    # @mock.patch('src.ffpp.Network.asyncio', new=mock.AsyncMock)
    async def test_sendMessageUnconnectedConnectionTimeout_exceptionTimeoutError(self):  # noqa
        # Arrange
        net = Network("")
        self.mockReturnValue(["Hej", "Två"])
        self.mock_con.wait_for.side_effect = TimeoutError

        # Act
        with self.assertRaises(TimeoutError):
            await net.sendMessage("msg_to_send")

        # Assert
        # No exception occurred, test responseData
        # self.assertEqual(mock_socket.socket().connect.call_count, 2)
        # self.assertFalse(response)


class TestNetworkCommunicateWithPrinter(unittest.IsolatedAsyncioTestCase):
    """ Class to test the communication with a real Flashforge printer."""

    @classmethod
    def setUpClass(cls):
        # Test if response, else skip TestCase
        try:
            with socket.socket() as s:
                s.settimeout(5)
                s.connect((PRINTER_IP, PRINTER_PORT))
                s.close()
        except Exception:
            cls.skipTest(
                cls,
                f"There is no printer at this ip: {PRINTER_IP}:{PRINTER_PORT}"
            )

    async def test_printerConnect_noException(self):
        # Arrange
        net = Network("192.168.0.32")

        # Act & Assert...
        with self.assertRaises(TimeoutError):
            await net.connect()
# ("Unable to connect to printer.",
#              "Check Power/IP/ethernet/wlan connection etc. ")

    async def test_getInfofromPrinter_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendInfoRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M115 Received" in response,
                        "Wrong message from printer.")

    async def test_getProgress_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendProgressRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M27 Received" in response,
                        "Wrong message from printer.")

    async def test_getTemperature_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendTempRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M105 Received" in response,
                        "Wrong message from printer.")

    async def test_getPosiotion_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendPositionRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M114 Received" in response,
                        "Wrong message from printer.")

    async def test_getStatus_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendStatusRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M119 Received" in response,
                        "Wrong message from printer.")

    async def test_getFileList_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        files = await net.sendGetFileNames()

        # Assert
        self.assertIsNotNone(net.responseData, "responseData is None")
        self.assertTrue("CMD M661 Received" in net.responseData,
                        "Wrong message from printer.")
        self.assertTrue(len(files) > 0, "There is no files on printer?")

    async def test_setTemperature_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)
        net.sendControlRequest()

        # Act
        response = await net.sendSetTemperature(40)
        response2 = await net.sendTempRequest()
        # response2 = net.responseData
        await asyncio.sleep(5)
        await net.sendSetTemperature(0)  # Restore temperature.

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M104 Received" in response,
                        "Wrong message from printer.")
        self.assertIsNotNone(response2, "responseData is None")
        # self.assertTrue("T0:40" in response2, "Temperature not set")

    async def test_pausePrint_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendPauseRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M25 Received" in response,
                        "Wrong message from printer.")

    async def test_continuePrint_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendContinueRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M24 Received" in response,
                        "Wrong message from printer.")

    async def test_abortPrint_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        response = await net.sendAbortRequest()

        # Assert
        self.assertIsNotNone(response, "responseData is None")
        self.assertTrue("CMD M26 Received" in response,
                        "Wrong message from printer.")

    @unittest.skip("Only run this test manually")
    async def test_testNewCommand_expectedResult(self):
        # Arrange
        net = Network(PRINTER_IP)

        # Act
        success = await net.sendMessage('~M129\r\n')
        response = net.responseData

        # Assert
        self.assertTrue(success)
        self.assertIsNotNone(response, "responseData is None")
