from modbus_crc import add_crc
import serial
import time

ser = serial.Serial(port='COM6', baudrate=9600, timeout=1, exclusive=True)


while ser.is_open:
    #signed_package = add_crc(package)
    #package = bytearray(b'~200246610000FDAB\r');
    package = bytearray(b'~200246630000FDA9\r');
    
    print(f"Command: {package}")
    ser.write(package)

    res = ser.read(200)
    print(f"Response: {res}")

    time.sleep(5)
    #if res != b'\r':
    #    break