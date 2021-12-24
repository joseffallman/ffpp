import asyncio
import logging


from ffpp.Printer import Printer
from ffpp.Discovery import getPrinters


# Activate module logger to output.
LOG = logging.getLogger("ffpp")
LOG.setLevel(logging.DEBUG)
out_handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(levelname)s : %(name)s : %(message)s'
)
out_handler.setFormatter(formatter)
LOG.addHandler(out_handler)


myPrinter: Printer


async def main():
    # Run until CTRL+C i pressed
    print("FlashForge Printer Protocol demo.")
    print("press ctrl+c to exit.")
    print("")
    ip = None
    loop = asyncio.get_running_loop()
    printers = await getPrinters(loop, limit=1)
    for name, host in printers:
        ip = host
        break

    if ip is None:
        print("Enter your printer ip:")
        ip = input()
    myPrinter = Printer(ip)
    try:
        await myPrinter.connect()
    except TimeoutError:
        print("Could'nt connect")
        return

    while True:
        try:
            await update_and_print(myPrinter)
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            return
        except RuntimeError:
            pass


async def update_and_print(myPrinter: Printer):
    # Connect and updates Printer object.
    try:
        await myPrinter.update()
    except ConnectionError:
        print("Write or read error.")
        return
    except TimeoutError:
        print("Connection Timeout.")
        return

    # Get the first extruder tool available
    extruder = myPrinter.extruder_tools.get()
    bed = myPrinter.bed_tools.get()

    # Print some information about printer and temperature.
    print("==================================================")
    print(f"{myPrinter.machine_type} is {myPrinter.machine_status}")
    print(
        f"Printer name {myPrinter.machine_name} is now {myPrinter.move_mode}")
    print(f"Status {myPrinter.status} print percent {myPrinter.print_percent}")
    print(f"Extruder {extruder.name} is now {extruder.now}")
    print(f"Bed {bed.name} is now {bed.now}")

if __name__ == "__main__":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
