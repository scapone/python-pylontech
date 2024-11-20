import serial
import time # Optional (required if using time.sleep() below)
import construct
import pylontech

def send_system_analog_data(adr: int, cid2: int = 0):
    data = p.system_analog_data.build(dict(
        TotalAverageVoltage = 11.859,
        TotalCurrent = 25.0,
        SystemSOC = 98,
        AverageNumberOfCycles = 2516,
        MaximumNumberOfCycles = 2932,
        AverageSOH = 98,
        MinimumSOH = 97,
        SingleCoreMaximumVoltage = 3.512,
        ModuleWithHighestVoltageOfSingleCore = 52,
        SingleCoreMinimumVoltage = 3.259,
        ModuleWithLowestVoltageOfSingleCore = 20,
        SingleCoreAverageTemperature = 25.5,
        SingleCoreMaximumTemperature = 26.8,
        ModuleWithHighestTemperatureOfSingleCore = 53,
        SingleCoreMinimumTemperature = 24.2,
        ModuleWithLowestTemperatureOfSingleCore = 21,
        MOSFETAverageTemperature = 25.5,
        MOSFETMaximumTemperature = 26.9,
        MOSFETHighestTemperatureModule = 54,
        MOSFETMinimumTemperature = 24.1,
        MOSFETLowestTemperatureModule = 22,
        BMSAverageTemperature = 25.5,
        BMSMaximumTemperature = 26.7,
        BMSHighestTemperatureModule = 55,
        BMSMinimumTemperature = 24.3,
        BMSLowestTemperatureModule = 23    
    ))
    
    info = data.hex().upper().encode('ascii')
    response = p._encode_cmd(adr, cid2, info)
    print(response)

def send_system_charge_discharge_management_info(adr: int, cid2: int = 0):
    data = p.system_charge_discharge_management_info.build(dict(
        ChargeVoltageLimit = 56.532,
        DischargeVoltageLimit = 24.0,
        ChargeCurrentLimit = 25.0,
        DischargeCurrentLimit = 20.2,
        Status = dict(
            ChargeEnable = True,
            DischargeEnable = False,
            ChargeImmediately = True,
            FullChargeRequest = True
        )
    ))
    
    info = data.hex().upper().encode('ascii')
    response = p._encode_cmd(adr, cid2, info)
    print(response)

p = pylontech.Pylontech()
raw_frame = b"~201246630000FDA8\r"
frame = p._decode_hw_frame(raw_frame)
parsed = p._decode_frame(frame)

if parsed.cid1 == b'\x46' and parsed.cid2 == b'\x61':
    print("Get system analog data (61h) command received")
    send_system_analog_data(parsed.adr[0])
if parsed.cid1 == b'\x46' and parsed.cid2 == b'\x63':
    print("Get system charge discharge management info (63h) command received")
    send_system_charge_discharge_management_info(parsed.adr[0])
    
# Command = construct.Struct(
#     "SOI" / construct.Const(b"~"),
#     "Frame" / construct.PaddedString(16, "ascii"),
#     "EOI" / construct.Const(b"\r")
# )

# test = Command.parse(b"~200246610000FDAB\r")
# print(test)


ser = serial.Serial(port='COM4', baudrate=9600)

while (ser.is_open):
    # Check if incoming bytes are waiting to be read from the serial input 
    # buffer.
    if (ser.in_waiting > 0):
        # read the bytes and convert from binary array to ASCII
        data_str = ser.read(ser.in_waiting).decode('ascii') 
        print(data_str) 

    # Put the rest of your code you want here
    
    # Optional, but recommended: sleep 10 ms (0.01 sec) once per loop to let 
    # other threads on your PC run during this time. 
    time.sleep(0.01) 