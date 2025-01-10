from modbus_crc import add_crc
import serial
import time

ser = serial.Serial(port='COM4', baudrate=9600, timeout=1, exclusive=True)

package = bytearray(b'\x01\x03\x00\x13\x00\x01') #ANG
#package = bytearray(b'\x01\x03\x00\x00\x00)') #AGH
#package = bytearray(b'\x01\x03\x00\x10\x00\x10')
#package = bytearray(b'\x01\x03\x02\x04\x00\x1f')
#package = bytearray(b'\x01\x03\x00\x0C\x00\x08')
#package = bytearray(b'\x01\x03\x00\x14\x00\x04')
#package = bytearray(b'\x01\x03\x00\x13\x00\x01')

for i in range(1, 254):
    package[0] = i
    signed_package = add_crc(package)
    print(f"Command: {signed_package}")

    ser.write(signed_package)

    if (ser.in_waiting > 0):
        res = ser.read(ser.in_waiting)
        print(f"Response: {res}")

    time.sleep(0.01)
    #if res != b'\r':
    #    break