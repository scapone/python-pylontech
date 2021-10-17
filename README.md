# python-pylontech
Python lib to talk to pylontech lithium batteries (US2000, US3000, ...) using RS485

## What is this lib ?
This lib is meant to talk to Pylontech batteries using RS485. Sadly the protocol over RS485 is not some fancy thing like MODBUS but their own crappy protocol.

## How to use this lib ?
First of all, you need a USB to RS485 converter. They are many available online for some bucks.

Then, you simply need to import the lib and start asking values:
```python

>>> import pylontech
>>> p = pylontech.Pylontech()
>>> print(p.get_values())
Container:
    NumberOfModules = 3
    Module = ListContainer:
        Container:
            NumberOfCells = 15
            CellVoltages = ListContainer:
                3.306
                3.307
                3.305
                3.305
                3.306
                3.305
                3.304
                3.305
                3.306
                3.306
                3.307
                3.307
                3.308
                3.307
                3.306
            NumberOfTemperatures = 5
            AverageBMSTemperature = 29.81
            GroupedCellsTemperatures = ListContainer:
                29.61
                29.61
                29.61
                29.61
            Current = -3.5
            Voltage = 49.59
            Power = -173.565
            RemainingCapacity = 39.5
            TotalCapacity = 50.0
            CycleNumber = 5
    -->8-- SNIP -->8--
    TotalPower = -525.8022
    StateOfCharge = 0.79

>>> print(p.get_system_parameters())
Container: 
    CellHighVoltageLimit = 3.7
    CellLowVoltageLimit = 3.05
    CellUnderVoltageLimit = 2.9
    ChargeHighTemperatureLimit = 33.41
    ChargeLowTemperatureLimit = 26.21
    ChargeCurrentLimit = 10.2
    ModuleHighVoltageLimit = 54.0
    ModuleLowVoltageLimit = 46.0
    ModuleUnderVoltageLimit = 44.5
    DischargeHighTemperatureLimit = 33.41
    DischargeLowTemperatureLimit = 26.21
    DischargeCurrentLimit = -10.0
```

## Dependencies
`python-pylontech` needs python 3.5 or greater (but please, use at least 3.7 or more if possible to be future-proof).

This lib depends on `pyserial` and the awesome `construct` lib.

# Hardware wiring
The pylontech modules talk using the RS485 line protocol.
## Pylontech side
The first DIP switch on the pylontech indicates the line speed. It must be off (`0`, down position) so that the speed is set to 115200 Bd.

The RS485 port is exposed on the pins 7 & 8 on the RJ45 connector names `RS485`.

## Client side
Any RS485 to USB (TCP/IP not yet supported) converter should would. You just have to wire the two pins above to the `A` and `B` ports (swap them around if it doesn't work). of your converter.

I personally use cheap chinese "RS485 to USB" converters worth a couple of bucks each.
