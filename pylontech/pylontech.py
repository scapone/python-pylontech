from typing import Dict
import logging
import serial
import construct

logger = logging.getLogger(__name__)
construct.setGlobalPrintFullStrings(True)

class HexToByte(construct.Adapter):
    def _decode(self, obj, context, path) -> bytes:
        hexstr = ''.join([chr(x) for x in obj])
        return bytes.fromhex(hexstr)


class JoinBytes(construct.Adapter):
    def _decode(self, obj, context, path) -> bytes:
        return ''.join([chr(x) for x in obj]).encode('latin1')

class DivideBy1000(construct.Adapter):
    def _decode(self, obj, context, path) -> float:
        return obj / 1000
    def _encode(self, obj, context, path):
        return int(obj * 1000)

class DivideBy100(construct.Adapter):
    def _decode(self, obj, context, path) -> float:
        return obj / 100
    def _encode(self, obj, context, path):
        return int(obj * 100)

class DivideBy10(construct.Adapter):
    def _decode(self, obj, context, path) -> float:
        return obj / 10

class ToVolt(construct.Adapter):
    def _decode(self, obj, context, path) -> float:
        return obj / 1000
    def _encode(self, obj, context, path):
        return int(obj * 1000)

class ToAmp(construct.Adapter):
    def _decode(self, obj, context, path) -> float:
        return obj / 10

class ToCelsius(construct.Adapter):
    def _decode(self, obj, context, path) -> float:
        return (obj - 2731) / 10.0  # in Kelvin*10
    def _encode(self, obj, context, path):
        return int(obj * 10 + 2731)

class Pylontech:
    manufacturer_info_fmt = construct.Struct(
        "DeviceName" / JoinBytes(construct.Array(10, construct.Byte)),
        "SoftwareVersion" / construct.Array(2, construct.Byte),
        "ManufacturerName" / JoinBytes(construct.Array(20, construct.Byte)),
    )

    system_parameters_fmt = construct.Struct(
        "CellHighVoltageLimit" / ToVolt(construct.Int16ub),
        "CellLowVoltageLimit" / ToVolt(construct.Int16ub),
        "CellUnderVoltageLimit" / ToVolt(construct.Int16sb),
        "ChargeHighTemperatureLimit" / ToCelsius(construct.Int16sb),
        "ChargeLowTemperatureLimit" / ToCelsius(construct.Int16sb),
        "ChargeCurrentLimit" / DivideBy10(construct.Int16sb),
        "ModuleHighVoltageLimit" / ToVolt(construct.Int16ub),
        "ModuleLowVoltageLimit" / ToVolt(construct.Int16ub),
        "ModuleUnderVoltageLimit" / ToVolt(construct.Int16ub),
        "DischargeHighTemperatureLimit" / ToCelsius(construct.Int16sb),
        "DischargeLowTemperatureLimit" / ToCelsius(construct.Int16sb),
        "DischargeCurrentLimit" / DivideBy10(construct.Int16sb),
    )

    management_info_fmt = construct.Struct(
        "ChargeVoltageLimit" / DivideBy1000(construct.Int16ub),
        "DischargeVoltageLimit" / DivideBy1000(construct.Int16ub),
        "ChargeCurrentLimit" / ToAmp(construct.Int16sb),
        "DischargeCurrentLimit" / ToAmp(construct.Int16sb),
        "status"
        / construct.BitStruct(
            "ChargeEnable" / construct.Flag,
            "DischargeEnable" / construct.Flag,
            "ChargeImmediately2" / construct.Flag,
            "ChargeImmediately1" / construct.Flag,
            "FullChargeRequest" / construct.Flag,
            "ShouldCharge"
            / construct.Computed(
                lambda this: this.ChargeImmediately2
                | this.ChargeImmediately1
                | this.FullChargeRequest
            ),
            "_padding" / construct.BitsInteger(3),
        ),
    )

    module_serial_number_fmt = construct.Struct(
        "CommandValue" / construct.Byte,
        "ModuleSerialNumber" / JoinBytes(construct.Array(16, construct.Byte)),
    )

    get_values_fmt = construct.Struct(
        "NumberOfModules" / construct.Byte,
        "Module" / construct.Array(1, construct.Struct(
            "NumberOfCells" / construct.Int8ub,
            "CellVoltages" / construct.Array(construct.this.NumberOfCells, ToVolt(construct.Int16sb)),
            "NumberOfTemperatures" / construct.Int8ub,
            "AverageBMSTemperature" / ToCelsius(construct.Int16sb),
            "GroupedCellsTemperatures" / construct.Array(construct.this.NumberOfTemperatures - 1, ToCelsius(construct.Int16sb)),
            "Current" / ToAmp(construct.Int16sb),
            "Voltage" / ToVolt(construct.Int16ub),
            "Power" / construct.Computed(construct.this.Current * construct.this.Voltage),
            "_RemainingCapacity1" / DivideBy1000(construct.Int16ub),
            "_UserDefinedItems" / construct.Int8ub,
            "_TotalCapacity1" / DivideBy1000(construct.Int16ub),
            "CycleNumber" / construct.Int16ub,
            "_OptionalFields" / construct.If(construct.this._UserDefinedItems > 2,
                                           construct.Struct("RemainingCapacity2" / DivideBy1000(construct.Int24ub),
                                                            "TotalCapacity2" / DivideBy1000(construct.Int24ub))),
            "RemainingCapacity" / construct.Computed(lambda this: this._OptionalFields.RemainingCapacity2 if this._UserDefinedItems > 2 else this._RemainingCapacity1),
            "TotalCapacity" / construct.Computed(lambda this: this._OptionalFields.TotalCapacity2 if this._UserDefinedItems > 2 else this._TotalCapacity1),
        )),
        "TotalPower" / construct.Computed(lambda this: sum([x.Power for x in this.Module])),
        "StateOfCharge" / construct.Computed(lambda this: sum([x.RemainingCapacity for x in this.Module]) / sum([x.TotalCapacity for x in this.Module])),

    )
    get_values_single_fmt = construct.Struct(
        "NumberOfModule" / construct.Byte,
        "NumberOfCells" / construct.Int8ub,
        "CellVoltages" / construct.Array(construct.this.NumberOfCells, ToVolt(construct.Int16sb)),
        "NumberOfTemperatures" / construct.Int8ub,
        "AverageBMSTemperature" / ToCelsius(construct.Int16sb),
        "GroupedCellsTemperatures" / construct.Array(construct.this.NumberOfTemperatures - 1, ToCelsius(construct.Int16sb)),
        "Current" / ToAmp(construct.Int16sb),
        "Voltage" / ToVolt(construct.Int16ub),
        "Power" / construct.Computed(construct.this.Current * construct.this.Voltage),
        "_RemainingCapacity1" / DivideBy1000(construct.Int16ub),
        "_UserDefinedItems" / construct.Int8ub,
        "_TotalCapacity1" / DivideBy1000(construct.Int16ub),
        "CycleNumber" / construct.Int16ub,
        "_OptionalFields" / construct.If(construct.this._UserDefinedItems > 2,
                                       construct.Struct("RemainingCapacity2" / DivideBy1000(construct.Int24ub),
                                                        "TotalCapacity2" / DivideBy1000(construct.Int24ub))),
        "RemainingCapacity" / construct.Computed(lambda this: this._OptionalFields.RemainingCapacity2 if this._UserDefinedItems > 2 else this._RemainingCapacity1),
        "TotalCapacity" / construct.Computed(lambda this: this._OptionalFields.TotalCapacity2 if this._UserDefinedItems > 2 else this._TotalCapacity1),
        "TotalPower" / construct.Computed(construct.this.Power),
        "StateOfCharge" / construct.Computed(construct.this.RemainingCapacity / construct.this.TotalCapacity),
    )

    alarm_info = construct.Struct(
        "NumberOfModule" / construct.Byte,
        "NumberOfCells" / construct.Byte,
        "CellVoltages" / construct.Array(construct.this.NumberOfCells, construct.Byte),
        "NumberOfTemperatures" / construct.Byte,
        "Temperatures" / construct.Array(construct.this.NumberOfTemperatures, construct.Byte),
        "ChargeCurrent" / construct.Byte,
        "PackVoltage" / construct.Byte,
        "DischargeCurrent" / construct.Byte,
        "Status1" / construct.BitStruct(
            "PackUnderVoltage" / construct.Flag,
            "ChargeTemperatureProtection" / construct.Flag,
            "DischargeTemperatureProtection" / construct.Flag,
            "DischargeOvercurrent" / construct.Flag,
            construct.Padding(1),
            "ChargeOvercurrent" / construct.Flag,
            "CellLowerLimitVoltage" / construct.Flag,
            "OverVoltage" / construct.Flag
        ),
        "Status2" / construct.BitStruct(
            construct.Padding(4),
            "UseThePackPower" / construct.Flag,
            "DFET" / construct.Flag,
            "CFET" / construct.Flag,
            "PreFET" / construct.Flag
        ),
        "Status3" / construct.BitStruct(
            "EffectiveChargeCurrent" / construct.Flag,
            "EffectiveDischargeCurrent" / construct.Flag,
            "StartUpHeater" / construct.Flag,
            construct.Padding(1),
            "FullyCharged" / construct.Flag,
            construct.Padding(2),
            "Buzzer" / construct.Flag
        ),
        "Status4" / construct.BitStruct(
            "CheckCell_8_1" / construct.Array(8, construct.Flag)
        ),
        "Status5" / construct.BitStruct(
            "CheckCell_16_9" / construct.Array(8, construct.Flag)
        )
    )

    system_analog_data = construct.Struct(
        "TotalAverageVoltage" / ToVolt(construct.Int16ub),
        "TotalCurrent" / DivideBy1000(construct.Int16sb),
        "SystemSOC" / construct.Byte,
        "AverageNumberOfCycles" / construct.Int16ub,
        "MaximumNumberOfCycles" / construct.Int16ub,
        "AverageSOH" / construct.Byte,
        "MinimumSOH" / construct.Byte,
        "SingleCoreMaximumVoltage" / ToVolt(construct.Int16ub),
        "ModuleWithHighestVoltageOfSingleCore" / construct.Short,
        "SingleCoreMinimumVoltage" / ToVolt(construct.Int16ub),
        "ModuleWithLowestVoltageOfSingleCore" / construct.Short,
        "SingleCoreAverageTemperature" / ToCelsius(construct.Int16sb),
        "SingleCoreMaximumTemperature" / ToCelsius(construct.Int16sb),
        "ModuleWithHighestTemperatureOfSingleCore" / construct.Short,
        "SingleCoreMinimumTemperature" / ToCelsius(construct.Int16sb),
        "ModuleWithLowestTemperatureOfSingleCore" / construct.Short,
        "MOSFETAverageTemperature" / ToCelsius(construct.Int16sb),
        "MOSFETMaximumTemperature" / ToCelsius(construct.Int16sb),
        "MOSFETHighestTemperatureModule" / construct.Short,
        "MOSFETMinimumTemperature" / ToCelsius(construct.Int16sb),
        "MOSFETLowestTemperatureModule" / construct.Short,
        "BMSAverageTemperature" / ToCelsius(construct.Int16sb),
        "BMSMaximumTemperature" / ToCelsius(construct.Int16sb),
        "BMSHighestTemperatureModule" / construct.Short,
        "BMSMinimumTemperature" / ToCelsius(construct.Int16sb),
        "BMSLowestTemperatureModule" / construct.Short
    )

    system_charge_discharge_management_info = construct.Struct(
        "ChargeVoltageLimit" / ToVolt(construct.Int16ub),
        "DischargeVoltageLimit" / ToVolt(construct.Int16ub),
        "ChargeCurrentLimit" / DivideBy100(construct.Int16sb),
        "DischargeCurrentLimit" / DivideBy100(construct.Int16sb),
        "Status" / construct.BitStruct(
            "ChargeEnable" / construct.Flag,
            "DischargeEnable" / construct.Flag,
            "ChargeImmediately" / construct.Flag,
            "FullChargeRequest" / construct.Flag,
            construct.Padding(4)
        )
    )

    def __init__(self, serial_port='\\\\.\\COM4', baudrate=9600):
        self.s = serial.Serial(serial_port, baudrate, bytesize=8, parity=serial.PARITY_NONE, stopbits=1, timeout=2, exclusive=True)


    @staticmethod
    def get_frame_checksum(frame: bytes):
        assert isinstance(frame, bytes)

        sum = 0
        for byte in frame:
            sum += byte
        sum = ~sum
        sum %= 0x10000
        sum += 1
        return sum

    @staticmethod
    def get_info_length(info: bytes) -> int:
        lenid = len(info)
        if lenid == 0:
            return 0

        lenid_sum = (lenid & 0xf) + ((lenid >> 4) & 0xf) + ((lenid >> 8) & 0xf)
        lenid_modulo = lenid_sum % 16
        lenid_invert_plus_one = 0b1111 - lenid_modulo + 1

        return (lenid_invert_plus_one << 12) + lenid


    def send_cmd(self, address: int, cmd, info: bytes = b''):
        raw_frame = self._encode_cmd(address, cmd, info)
        print(f"Command: {raw_frame}")
        self.s.write(raw_frame)


    def _encode_cmd(self, address: int, cid2: int, info: bytes = b''):
        cid1 = 0x46

        info_length = Pylontech.get_info_length(info)

        frame = "{:02X}{:02X}{:02X}{:02X}{:04X}".format(0x20, address, cid1, cid2, info_length).encode()
        frame += info

        frame_chksum = Pylontech.get_frame_checksum(frame)
        whole_frame = (b"~" + frame + "{:04X}".format(frame_chksum).encode() + b"\r")
        return whole_frame


    def _decode_hw_frame(self, raw_frame: bytes) -> bytes:
        # XXX construct
        frame_data = raw_frame[1:len(raw_frame) - 5]
        frame_chksum = raw_frame[len(raw_frame) - 5:-1]

        got_frame_checksum = Pylontech.get_frame_checksum(frame_data)
        assert got_frame_checksum == int(frame_chksum, 16)

        return frame_data

    def _decode_frame(self, frame):
        format = construct.Struct(
            "ver" / HexToByte(construct.Array(2, construct.Byte)),
            "adr" / HexToByte(construct.Array(2, construct.Byte)),
            "cid1" / HexToByte(construct.Array(2, construct.Byte)),
            "cid2" / HexToByte(construct.Array(2, construct.Byte)),
            "infolength" / HexToByte(construct.Array(4, construct.Byte)),
            "info" / HexToByte(construct.GreedyRange(construct.Byte)),
        )

        return format.parse(frame)

    def read_frame(self):
        raw_frame = self.s.readline()
        print(f'Response: {raw_frame}')
        f = self._decode_hw_frame(raw_frame=raw_frame)
        parsed = self._decode_frame(f)
        return parsed

    def scan_for_batteries(self, start=0, end=255) -> Dict[int, str]:
        """ Returns a map of the batteries id to their serial number """
        batteries = {}
        for adr in range(start, end, 1):
            bdevid = "{:02X}".format(adr).encode()
            self.send_cmd(adr, 0x93, bdevid) # Probe for serial number
            raw_frame = self.s.readline()

            if raw_frame:
                sn = self.get_module_serial_number(adr)
                sn_str = sn["ModuleSerialNumber"].decode('latin1')

                batteries[adr] = sn_str
                logger.debug("Found battery at address " + str(adr) + " with serial " + sn_str)
            else:
                logger.debug("No battery found at address " + str(adr))

        return batteries


    def get_protocol_version(self):
        self.send_cmd(0, 0x4f)
        return self.read_frame()


    def get_manufacturer_info(self):
        self.send_cmd(0, 0x51)
        f = self.read_frame()
        return self.manufacturer_info_fmt.parse(f.info)


    def get_system_parameters(self, dev_id=None):
        if dev_id is not None:
            bdevid = "{:02X}".format(dev_id).encode()
            self.send_cmd(dev_id, 0x47, bdevid)
        else:
            self.send_cmd(2, 0x47)

        f = self.read_frame()
        return self.system_parameters_fmt.parse(f.info[1:])

    def get_management_info(self, dev_id):
        bdevid = "{:02X}".format(dev_id).encode()
        self.send_cmd(dev_id, 0x92, bdevid)
        f = self.read_frame()

        print(f.info)
        print(len(f.info))
        ff = self.management_info_fmt.parse(f.info[1:])
        return ff

    def get_module_serial_number(self, dev_id=None):
        if dev_id is not None:
            bdevid = "{:02X}".format(dev_id).encode()
            self.send_cmd(dev_id, 0x93, bdevid)
        else:
            self.send_cmd(2, 0x93)

        f = self.read_frame()
        # infoflag = f.info[0]
        return self.module_serial_number_fmt.parse(f.info[0:])

    def get_values(self):
        self.send_cmd(2, 0x42, b'FF')
        f = self.read_frame()

        # infoflag = f.info[0]
        d = self.get_values_fmt.parse(f.info[1:])
        return d

    def get_values_single(self, dev_id):
        bdevid = "{:02X}".format(dev_id).encode()
        self.send_cmd(dev_id, 0x42, bdevid)
        f = self.read_frame()
        # infoflag = f.info[0]
        d = self.get_values_single_fmt.parse(f.info[1:])
        return d

    def get_alarm_info(self, dev_id = None):
        if dev_id is None:
            dev_id = 2
        
        bdevid = "{:02X}".format(dev_id).encode()
        self.send_cmd(dev_id, 0x44, bdevid)
        f = self.read_frame()
        #dataflag = f.info[0]
        d = self.alarm_info.parse(f.info[1:])
        return d

    def get_system_analog_data(self, dev_id = None):
        if dev_id is None:
            dev_id = 2
        
        self.send_cmd(dev_id, 0x61)
        f = self.read_frame()
        #dataflag = f.info[0]
        d = self.system_analog_data.parse(f.info[0:])
        return d

    def get_system_charge_discharge_management_info(self, dev_id = None):
        if dev_id is None:
            dev_id = 2
        self.send_cmd(dev_id, 0x63)
        f = self.read_frame()
        #dataflag = f.info[0]
        d = self.system_charge_discharge_management_info.parse(f.info[0:])
        return d 

if __name__ == '__main__':
    p = Pylontech()
    #print("get_protocol_version")
    #print(p.get_protocol_version())

    #print("get_manufacturer_info")
    #print(p.get_manufacturer_info())

    #print("get_manufacturer_info")
    #print(p.get_system_parameters())

    #print("get_management_info")
    #print(p.get_management_info(0))

    #print("get_module_serial_number")
    #print(p.get_module_serial_number())

    #print("get_values")
    #print(p.get_values())

    #print("get_values_single")
    #print(p.get_values_single(2))

    #p.scan_for_batteries(0, 4)

    #print("get_alarm_info")
    #print(p.get_alarm_info())

    #print("Get system analog data")
    #print(p.get_system_analog_data())

    #print("Get system charge discharge management info")
    #print(p.get_system_charge_discharge_management_info())
