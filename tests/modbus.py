from modbus_crc import add_crc
import serial

ser = serial.Serial(port='COM4', baudrate=9600, timeout=1, exclusive=True)

#package = bytearray(b'\x01\x03\x00\x13\x00\x01')
package = bytearray(b'\x01\x03\x00\x10\x00\x10')

for i in range(1, 2):
    #package[0] = i
    signed_package = add_crc(package)
    print(f"Command: {signed_package}")

    ser.write(signed_package)

    res = ser.read(37)
    print(f"Response: {res}")

    if res != b'':
        break