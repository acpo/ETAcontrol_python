import serial
import time
import tkinter as tk
from tkinter import messagebox

COMports = ['COM1','COM2','COM3','COM4']
for device in COMports:
    print(device)
    try:
        ser = serial.Serial(port=device,
                            baudrate=57600,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS,
                            timeout = 0,
                            writeTimeout = 0
                        ) #ensure non-blocking
        break
    except serial.SerialException:
        messagebox.showerror("Error", "Error opening serial port.")

    except:
        messagebox.showerror("Error", "Other problem with serial port communication")

connected = False

time.sleep(0.1)
ser.flushInput()
time.sleep(1)

while True:  #this could be the Serial Read 
    if ser.in_waiting():
        line = ser.readline()
        data = line.decode("utf-8").split('\t') #ser.readline returns a binary, convert to string
        print (data[0] + '\t' + data[1])
        #output_file.write(line)

        
'''    
while True:
    received_data = ser.read()              #read serial port
    sleep(0.03)
    data_left = ser.inWaiting()             #check for remaining byte
    received_data += ser.read(data_left)
    print (received_data)                   #print received data
    ser.write(received_data)                #transmit data serially 
'''
