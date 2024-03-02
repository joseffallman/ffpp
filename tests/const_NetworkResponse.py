
# ControlRequest
RESPONSE_sendControlRequestTrue = (
    'CMD M601 Received.\r\nControl Success V2.1.\r\nok\r\n'
)
RESPONSE_sendControlRequestFalse = (
    'CMD M601 Received.\r\nControl failed.\r\nok\r\n'
)

# ControlRelease
RESPONSE_sendControlRelease = (
    'CMD 602 Received.\r\nok\r\n'
)

# InfoRequest
RESPONSE_sendInfoRequest = (
    'CMD M115 Received.\r\n'
    'Machine Type: Flashforge Adventurer 4\r\n'
    'Machine Name: Adventurer4\r\n'
    'Firmware: v2.0.9\r\n'
    'SN: SNADVA9501174\r\n'
    'X: 220 Y: 200 Z: 250\r\n'
    'Tool Count: 1\r\n'
    'Mac Address:88:A9:A7:93:86:F8\n \r\n'
    'ok\r\n'
)

# ProgressRequest
RESPONSE_sendProgressRequest = (
    'CMD M27 Received.\r\nSD printing byte 0/100\r\nok\r\n'
)
RESPONSE_sendProgressRequest2 = (
    'CMD M27 Received.\r\nSD printing byte 11/100\r\nLayer: 44/419\r\nok\r\n'
)

# TempRequest
RESPONSE_sendTempRequest = (
    'CMD M105 Received.\r\nT0:22/0 B:14/0\r\nok\r\n'
)

# TempRequest2
RESPONSE_sendTempRequest2 = (
    'CMD M105 Received.\r\nT0:104.5/225.0 T1:0.0/0.0 B:51.3/50.0\r\nok\r\n'
)

# PositionRequest
RESPONSE_sendPositionRequest = (
    'CMD M114 Received.\r\n'
    'X:19.3861 Y:54.3 Z:194.44 A:0 B:0\r\n'
    'ok\r\n'
)

# StatusRequest
RESPONSE_sendStatusRequest = (
    'CMD M119 Received.\r\n'
    'Endstop: X-max:0 Y-max:0 Z-max:0\r\n'
    'MachineStatus: READY\r\n'
    'MoveMode: READY\r\n'
    'Status: S:1 L:0 J:0 F:0\r\n'
    'LED: 0\r\n'
    'CurrentFile: \r\n'
    'ok\r\n'
)

RESPONSE_sendStatusRequest2 = (
    'CMD M119 Received.\r\n'
    'Endstop: X-max:0 Y-max:0 Z-max:0\r\n'
    'MachineStatus: BUILDING_FROM_SD\r\n'
    'MoveMode: MOVING\r\n'
    'Status: S:1 L:0 J:0 F:0\r\n'
    'LED: 1\r\n'
    'CurrentFile: RussianDollMazeModels.gx\r\n'
    'ok\r\n'
)

# SetTemperature
RESPONSE_sendSetTemperature = (
    'CMD 104 Received.\r\nok\r\n'
)

# SetLedState
RESPONSE_sendsetLedState = (
    'CMD 146 Received.\r\nok\r\n'
)

# GetFileNamesRequest
RESPONSE_sendGetFileNames = (
    'CMD 661 Received.\r\nok\r\n'
)

# SendPauseRequest
RESPONSE_sendPauseRequest = (
    'CMD M25 Received.\r\nok\r\n'
)

# SendContinueRequest
RESPONSE_sendContinueRequest = (
    'CMD M24 Received.\r\nok\r\n'
)

# SendContinueRequest
RESPONSE_sendPrintRequest = (
    'CMD M23 Received.\r\n'
    'File opened: My Box.gx Size: 1613086\r\n'
    'File selected\r\nok\r\n'
)

# SendContinueRequest
RESPONSE_sendAbortRequest = (
    'CMD M26 Received.\r\n'
)
