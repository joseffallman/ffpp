FlashForge 3D Printer Protocol

A simple way to connect and interact with your 3D printer.

Tested on FlashForge Adventure 4, most likly to be working with other FlashForge printers.

# How to use
```
import ffpp
myPrinter = ffpp.Printer(192.168.0.1, 8899) # Change to the ip of your printer.
myPrinter.connect()

print(f"{myPrinter.machine_status} is {myPrinter.machine_status.value}")
```

# Important note
You need to call the `update()` to get the current status, temperature and print percent from printer.
```
myPrinter.update()
myPrinter.extruder_temp.value
```