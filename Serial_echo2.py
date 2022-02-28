import serial
import time # Optional (required if using time.sleep() below)

ser = serial.Serial(port='COM1', baudrate=57600)
ser.write(bytes("?\n",'utf-8'))

while (True):
    # Check if incoming bytes are waiting to be read from the serial input 
    # buffer.
    # NB: for PySerial v3.0 or later, use property `in_waiting` instead of
    # function `inWaiting()` below!
    if (ser.in_waiting() > 0):
        # read the bytes and convert from binary array to ASCII
        data_str = ser.read(ser.in_waiting()).decode('ascii') 
        # print the incoming string without putting a new-line
        # ('\n') automatically after every print()
        print(data_str, end='') 

    # Put the rest of your code you want here
    
    # Optional, but recommended: sleep 10 ms (0.01 sec) once per loop to let 
    # other threads on your PC run during this time. 
    time.sleep(0.01) 

# avoids 'readline' in favor of knowning how many bytes are readable.

'''    
while True:
    received_data = ser.read()              #read serial port
    sleep(0.03)
    data_left = ser.inWaiting()             #check for remaining byte
    received_data += ser.read(data_left)
    print (received_data)                   #print received data
    ser.write(received_data)                #transmit data serially 
'''
