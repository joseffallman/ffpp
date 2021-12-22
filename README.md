# FlashForge 3D Printer Protocol

Async python protocol for flashforge printers.
A simple way to connect and interact with your 3D printer.

Tested on FlashForge Adventure 4, most likly to be working with other FlashForge printers.

## How to use
```
from ffpp.Printer import Printer
myPrinter = Printer('192.168.0.1', 8899) # Change to the ip of your printer.
await myPrinter.connect()

print(f"{myPrinter.machine_type} is {myPrinter.machine_status}")
```
Check out example to learn more.

## Important note
You need to call the `update()` to get the current status, temperature and print percent from printer.
```
await myPrinter.update()
print(myPrinter.print_percent)
await myPrinter.update()
print(myPrinter.print_percent)
```

## Information from 3D printer
This is the information collected from the printer.
- myPrinter.machine_type
- myPrinter.machine_name
- myPrinter.firmware
- myPrinter.machine_SN
- myPrinter.maxX
- myPrinter.maxY
- myPrinter.maxZ
- myPrinter.extruder_count
- myPrinter.mac_address
- myPrinter.machine_status
- myPrinter.move_mode
- myPrinter.status
- myPrinter.led
- myPrinter.current_file
- myPrinter.print_percent

## To get some temperature you need to get right tool. 
Run this line to return the extruder tool:
```
extruder = myPrinter.extruder_tools.get()
# or by index
extruder2 = myPrinter.extruder_tools.get(1)
```
You can do the same for your bed in myPrinter.bed_tools

Then you can do:
```
extruder.now # Current temperature.
extruder.target # Target temperature.
```