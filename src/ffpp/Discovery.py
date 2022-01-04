import asyncio
import socket
import struct
import logging

LOG = logging.getLogger(__name__)


class ffDiscoveryDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        message: str,
        on_con_lost: asyncio.Future,
        interface_addr: str,
        limit: int
    ):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None
        self.interface_addr = interface_addr
        self.limit = limit
        self.data = []
        self.received = 0

    def connection_made(self, transport):
        self.transport = transport
        sock = self.transport.get_extra_info('socket')
        sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("B", 4)
        )
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(self.interface_addr)
        )
        # print('Send:', self.message)
        self.transport.sendto(self.message.encode(), ("225.0.0.9", 19000))

    def datagram_received(self, data: bytes, addr):
        self.received += 1
        try:
            end = data.find(b'\x00')
            name = data[:end].decode('utf-8', "ignore")
            ip = addr[0]
        except Exception:
            return

        self.data.append((name, ip))

        if self.received == self.limit:
            self.transport.close()

    def error_received(self, exc):
        pass
        # print('Error received:', exc)

    def connection_lost(self, exc):
        try:
            self.on_con_lost.set_result(True)
        except asyncio.exceptions.InvalidStateError:
            pass


def find_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


async def getPrinters(loop: asyncio.BaseEventLoop, limit: int = None, host_ip: str = None) -> tuple():
    """Search network for connected printers.

    Args:
        loop (asyncio.BaseEventLoop): EventLoop
        limit ([int], optional): Stop search when limit is reached. Defaults to None.

    Returns:
        [tuple(str, str)]: return a list of available printers, as (name, ip)
    """
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    # loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = "Hello World!"

    if not host_ip:
        host_ip = find_host_ip()

    transport, ffDiscovery = await loop.create_datagram_endpoint(
        lambda: ffDiscoveryDatagramProtocol(
            message, on_con_lost, host_ip, limit),
        local_addr=(host_ip, 8002)
    )
    try:
        # Wait until limit or timeout is reached.
        await asyncio.wait_for(
            on_con_lost,
            timeout=15
        )
    except Exception:  # CancelError and TimeoutError
        LOG.debug("FlashForge printer search timeout.")
        # raise TimeoutError(e) from e
    finally:
        transport.close()

    printers = ffDiscovery.data
    for printer in printers:
        LOG.debug("Printer online: %s - %s", printer[0], printer[1])

    return printers
