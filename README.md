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
print(myPrinter.extruder_temp.value)
myPrinter.update()
print(myPrinter.extruder_temp.value)
```

# Information from 3D printer
This is the information collected from the printer.
You'll find the value in the 'value' attribute of each field.
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
- myPrinter.extruder_temp
- myPrinter.extruder_target_temp
- myPrinter.bed_temp
- myPrinter.bed_target_temp
- myPrinter.print_percent