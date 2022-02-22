'''
@ author: summer
@ tools: pycharm 
@ content: Serial Communication Implementation Class
@ date: 2020.2.12
'''
import serial
import serial.tools.list_ports

class SerialFunctions:
    def __init__(self,band=115200,check="No Check Bit",data=8,stop=1):
        self.port = None
        # Get Available Serial Ports
        self.port_list = list(serial.tools.list_ports.comports())
        assert (len(self.port_list) != 0),"No Serial Port Available"

        self.bandRate = band
        self.checkbit = check
        self.databit = data
        self.stopbit = stop

        # Read and write data
        self.read_data = None
        self.write_data = None

        pass
    def show_port(self):
        for i in range(0,len(self.port_list)):
            print(self.port_list[i])

    def show_other(self):
        print("Baud rate:"+self.bandRate)
        print("Check digit:" + self.checkbit)
        print("Data bits:" + self.databit)
        print("Stop bits:" + self.stopbit)
    # Return to Serial Port
    def get_port(self):
        return self.port_list
    # Open Serial Port
    def open_port(self,port):
        self.port = serial.Serial(port, self.bandRate,timeout = None)

    def delete_port(self):
        if self.port != None:
            self.port.close()
            print("Close Serial Port Complete")
        else:
            pass

    def Read_data(self):   # Self.port.read (self.port.in_wait) indicates that all data in the receiving serial port is received
        self.read_data = self.port.read(self.port.in_waiting)   # Read data
        return self.read_data.decode("utf-8")

    def Write_data(self,data):
        if self.port.isOpen() == False:
            print("Serial port open error")
        else:
            self.port.write(data.encode("utf-8"))  # Returns the number of bytes written

if __name__ == '__main__':
    myser = SerialFunctions()
    myser.open_port("COM1")
    myser.delete_port()
    myser.show_port()
