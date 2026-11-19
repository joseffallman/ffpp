import socket
import unittest
from unittest import mock
import asyncio

from src.ffpp.Network import Network
from tests.const_NetworkResponse import (
    RESPONSE_sendGetFileNamesWithFiles,
    RESPONSE_sendProgressRequestPerMille,
    RESPONSE_sendTempRequestTwoExtruders,
)

PRINTER_IP = "192.168.20.41"
PRINTER_PORT = 8899


def segments(response: bytes, size: int = 7):
    """Split a response like the printer could do over TCP."""
    return [response[i:i + size] for i in range(0, len(response), size)]


class FakePrinter(object):
    """Fake connection that answers commands, one segment per loop cycle."""

    def __init__(self):
        self.answer = True
        self.connections = 0
        self.writers = []
        self.responses = {
            '~M105\r\n': segments(
                RESPONSE_sendTempRequestTwoExtruders.encode()),
            '~M27\r\n': segments(
                RESPONSE_sendProgressRequestPerMille.encode()),
            # The file names are sent after the "ok".
            '~M661\r\n': RESPONSE_sendGetFileNamesWithFiles,
        }

    async def open_connection(self, *args, **kwargs):
        self.connections += 1
        reader = asyncio.StreamReader()
        writer = FakeWriter(self, reader)
        self.writers.append(writer)
        return reader, writer


class FakeWriter(object):

    def __init__(self, printer: FakePrinter, reader: asyncio.StreamReader):
        self.printer = printer
        self.reader = reader
        self.closed = False

    def write(self, data: bytes):
        if not self.printer.answer or self.reader.at_eof():
            return
        pending = list(self.printer.responses[data.decode()])
        loop = asyncio.get_running_loop()

        def feed_next_segment():
            self.reader.feed_data(pending.pop(0))
            if pending:
                loop.call_soon(feed_next_segment)

        loop.call_soon(feed_next_segment)

    async def drain(self):
        pass

    def close(self):
        self.closed = True


class TestNetworkClass(unittest.IsolatedAsyncioTestCase):
    """ Class to test the behavior of the Network class
    """

    def setUp(self):
        self.printer = FakePrinter()
        patch_connection = mock.patch(
            'src.ffpp.Network.asyncio.open_connection',
            new=self.printer.open_connection,
        )
        patch_connection.start()
        self.addCleanup(patch_connection.stop)
        self.network = Network(PRINTER_IP, PRINTER_PORT)

    async def test_sendMessageUnconnectedConnectionTimeout_exceptionTimeoutError(self):  # noqa
        # Arrange
        async def no_connection(*args, **kwargs):
            raise OSError("Host is unreachable")

        # Act & Assert
        with mock.patch(
            'src.ffpp.Network.asyncio.open_connection', new=no_connection
        ):
            with self.assertRaises(TimeoutError):
                await self.network.sendMessage("msg_to_send")

    async def test_splitResponse_readCompletely(self):
        # Act
        temp = await self.network.sendTempRequest(disconnect=False)
        progress = await self.network.sendProgressRequest()

        # Assert
        self.assertEqual(temp, RESPONSE_sendTempRequestTwoExtruders)
        self.assertEqual(progress, RESPONSE_sendProgressRequestPerMille)
        self.assertEqual(self.printer.connections, 1)
        self.assertTrue(self.printer.writers[0].closed)

    async def test_concurrentRequests_dontInterleave(self):
        # Act
        temp, progress = await asyncio.gather(
            self.network.sendTempRequest(),
            self.network.sendProgressRequest(),
        )

        # Assert
        self.assertEqual(temp, RESPONSE_sendTempRequestTwoExtruders)
        self.assertEqual(progress, RESPONSE_sendProgressRequestPerMille)

    async def test_noAnswer_exceptionTimeoutErrorAndReconnect(self):
        # Arrange
        self.printer.answer = False

        # Act
        with mock.patch('src.ffpp.Network.RESPONSE_TIMEOUT', 0.01):
            with self.assertRaises(TimeoutError):
                await self.network.sendTempRequest(disconnect=False)

        # Assert, the broken connection isn't reused.
        self.assertTrue(self.printer.writers[0].closed)
        self.printer.answer = True
        temp = await self.network.sendTempRequest()
        self.assertEqual(temp, RESPONSE_sendTempRequestTwoExtruders)
        self.assertEqual(self.printer.connections, 2)

    async def test_connectionClosedByPrinter_exceptionConnectionError(self):
        # Arrange
        await self.network.sendTempRequest(disconnect=False)
        self.printer.writers[0].reader.feed_eof()

        # Act
        with self.assertRaises(ConnectionError):
            await self.network.sendTempRequest(disconnect=False)

        # Assert, the closed connection isn't reused.
        self.assertTrue(self.printer.writers[0].closed)
        temp = await self.network.sendTempRequest()
        self.assertEqual(temp, RESPONSE_sendTempRequestTwoExtruders)
        self.assertEqual(self.printer.connections, 2)

    async def test_getFileNames_readAfterOk(self):
        # Act
        with mock.patch('src.ffpp.Network.IDLE_TIMEOUT', 0.05):
            files = await self.network.sendGetFileNames()

        # Assert
        self.assertEqual(files, ['/data/box.gx', '/data/cube.gx'])


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
        await net.sendControlRequest()

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
        #success = await net.sendMessage('~M129\r\n')
        success = await net.sendSetLedState(0)
        response = net.responseData

        # Assert
        self.assertTrue(success)
        self.assertIsNotNone(response, "responseData is None")
