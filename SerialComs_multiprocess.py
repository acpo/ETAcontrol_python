import threading, multiprocessing
import time
import serial
import sys


def OpenSerialPort(port=""):
    print ("Open port %s" % port)

    fio2_ser = None

    try:
        fio2_ser = serial.Serial(port,
                    baudrate=2400,
                    bytesize=serial.EIGHTBITS,
                    parity =serial.PARITY_ODD)

    except serial.SerialException as msg:
        print( "Error opening serial port %s" % msg)

    except:
        exctype, errorMsg = sys.exc_info()[:2]
        print ("%s  %s" % (errorMsg, exctype))

    return fio2_ser


def Read_Data(queue, serialPort, stopped):
    print ("Start reading data.")

    serialPort.timeout = 1.0
    while not stopped.is_set(): 
        fio2_data = ''       
        try:                    
            #print "Reading port..."
            fio2_data = serialPort.readline()

        except:
            exctype, errorMsg = sys.exc_info()[:2]
            print ("Error reading port - %s" % errorMsg)
            stopped.set()
            break

        if len(fio2_data) > 0:
            fio2_data = fio2_data.decode('utf-8')
            fio2_data = str(fio2_data).replace("\r\n","")
            fio2_data = fio2_data.replace("\x000","")
            queue.put(fio2_data)
        else:
            queue.put("Read_Data() no Data")

    serialPort.close()
    print ("Read_Data finished.")

def Disp_Data(queue, stopped):
    print ("Disp_Data started")
    while not stopped.is_set():
        #print "Check message queue."
        if queue.empty() == False:        
            fio2_data = queue.get()
            print(fio2_data)

    print ("Disp_Data finished")

if __name__ == "__main__":


    #serialPort = OpenSerialPort('/dev/ttyUSB0')  for Linux style ports
    serialPort = OpenSerialPort('COM1')
    if serialPort == None: sys.exit(1)

    queue = multiprocessing.Queue()  #create queue for moving data between processes
    stopped = threading.Event()
    p1 = threading.Thread(target=Read_Data, args=(queue, serialPort, stopped,))
    p2 = threading.Thread(target=Disp_Data, args=(queue, stopped,))

    p1.start()
    p2.start()

    loopcnt = 20
    while (loopcnt > 0) and (not stopped.is_set()):
        loopcnt -= 1
        print ("main() %d" % loopcnt)
        try:
            time.sleep(1)

        except KeyboardInterrupt: #Capture Ctrl-C
            print ("Captured Ctrl-C")
            loopcnt=0
            stopped.set()

    stopped.set()
    loopcnt=0        

    print ("Stopped")
    p1.join()
    p2.join()

    serialPort.close()
    print ("Done")
