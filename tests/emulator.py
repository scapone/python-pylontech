import time # Optional (required if using time.sleep() below)
import pylontech

p = pylontech.Pylontech()

def send_system_analog_data(adr: int, cid2: int = 0):
    data = p.system_analog_data.build(dict(
        TotalAverageVoltage = 52.6,
        TotalCurrent = 25.0,
        SystemSOC = 99,
        AverageNumberOfCycles = 3,
        MaximumNumberOfCycles = 4,
        AverageSOH = 98,
        MinimumSOH = 97,
        SingleCoreMaximumVoltage = 3.512,
        ModuleWithHighestVoltageOfSingleCore = 52,
        SingleCoreMinimumVoltage = 3.509,
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
    return response

def send_system_charge_discharge_management_info(adr: int, cid2: int = 0):
    data = p.system_charge_discharge_management_info.build(dict(
        ChargeVoltageLimit = 53,
        DischargeVoltageLimit = 45.0,
        ChargeCurrentLimit = 25,
        DischargeCurrentLimit = 25,
        Status = dict(
            ChargeEnable = True,
            DischargeEnable = True,
            ChargeImmediately = False,
            FullChargeRequest = False
        )
    ))
    
    info = data.hex().upper().encode('ascii')
    response = p._encode_cmd(adr, cid2, info)
    print(response)
    return response

def create_response(command: bytes):
    frame = p._decode_hw_frame(command)
    parsed = p._decode_frame(frame)

    if parsed.adr != b'\x02':
        print(f"Module address mismatch ({parsed.adr.hex()}h) - ignoring")
        return None
    if parsed.cid2 == b'\x61':
        print("Get system analog data (61h) command received")
        return send_system_analog_data(parsed.adr[0])
    if parsed.cid2 == b'\x63':
        print("Get system charge discharge management info (63h) command received")
        return send_system_charge_discharge_management_info(parsed.adr[0])
    
ser = p.s

while (ser.is_open):
    # Check if incoming bytes are waiting to be read from the serial input 
    # buffer.
    if (ser.in_waiting > 0):
        # read the bytes and convert from binary array to ASCII
        command = ser.read(ser.in_waiting) 
        print(command)

        response = create_response(command)
        if (response != None):
            ser.write(response)
    
    # Optional, but recommended: sleep 10 ms (0.01 sec) once per loop to let 
    # other threads on your PC run during this time. 
    time.sleep(0.01) 
