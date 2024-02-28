## current work:  add explicit Serial connect/disconnect to avoid quit when programming BK
## added COM dropbox 16NOV2022 ECN
## new scalar selection to conform to Numpy > 1.25  21FEB2024 ECN

# Functional on all parts.
#
# With 3 lines showing in real time, minimum IntTime is 25ms due to extra drawing overhead
# Consider not drawing Base data, see commented lines.
# Strong version dependence on plotting speed:
# Python 3.6.8:  25ms is solid, 24ms is ok but some small random shifts
# Python 3.9.10:  15ms is solid
# Other speed related properties:
#  Plotting point '.' is faster than circle 'o' is faster than line 'lw=1'.  Faster or less resource
#  intensive, doesn't matter, it works better (able to record 90s without time errors).
#  Plotting pixel ',' is even faster, but a little hard to see.
#  With v3.9.10  15ms integration can be plotted with all three wavelengths using
#   a pixel marker using 'markevery=2' for everyother point.

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from tkinter import Scrollbar
from tkinter import Spinbox
from tkinter import Text
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
import tkinter.ttk as ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import style
style.use("ggplot")
plt.rcParams['axes.facecolor']='#F8F8F8'
plt.rcParams['lines.color']='blue'
plt.rcParams['figure.figsize'] = [9.0, 7.0]

import seabreeze.spectrometers as sb
import numpy as np

import time
from time import (perf_counter)
import os #for filename and path handling
import csv  #easier file writing
import gc  #garbage collection
import serial
import serial.tools.list_ports

# Enumerate spectrometer, set a default integration time, get x & y extents
try:
    spec = sb.Spectrometer.from_serial_number()
except:
    messagebox.showerror("Error", "No spectrometer attached")
    #exit()
    
#Serial port setup
try:
    ser = serial.Serial(port=None,#'COM3',
                        baudrate=9600,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout = 1,
                        writeTimeout = 0
                    ) #ensure non-blocking

except serial.SerialException:
    messagebox.showerror("Error", "Error opening serial port. \nIs another connection open?")
    exit()
except:
    messagebox.showerror("Error", "Other problem with serial port communication")
    exit()

# Spectrometer data collectors
def get_wavelengths():
    spec_x = spec.wavelengths()
    return spec_x
def get_intensities():
    spec_y = spec.intensities(correct_dark_counts=False, correct_nonlinearity=False) #dark counts might need to be false
    return spec_y

class App(tk.Frame):
    def __init__(self, master=None, **kwargs):

        tk.Frame.__init__(self, master, **kwargs)
#Spectrometer initial setup
        self.wavelengths = np.around(get_wavelengths(), decimals=3) #round wavelengths to practical limits
        self.ydata = np.array(get_intensities())
        self.max_intensity = 65535
        self.xmin = np.around(min(self.wavelengths), decimals=3)
        self.xminlimit = self.xmin
        self.xmax = np.around(max(self.wavelengths), decimals=3)
        self.xmaxlimit = self.xmax
        self.ymin = np.around(min(self.ydata * 0.8), decimals=3) #ymin is the display limit, data_min*0.8 to give a margin
        self.ymax = np.around(max(self.ydata * 1.1), decimals=3)
        self.waveres = np.around(self.wavelengths[1] - self.wavelengths[0], decimals=3)
        self.IntTime = 25000 #set in microseconds, this is 25ms
        spec.integration_time_micros(self.IntTime)  #send IntTime to spectrograph
        self.IntTimeLimits = spec.integration_time_micros_limits #BIGGER RANGE THAN REALLY EXISTS; this is available if needed;reads as tuple
        self.max_intensity = spec.max_intensity  #fullscale limit
        self.timelimit = 5 # time in SECONDS, default to 5 s for convenience
        
        #preload wavelength values
        self.wavelength1 = tk.StringVar(self, self.wavelengths[int(len(self.wavelengths) * 0.8)])
        self.wavelength2 = tk.StringVar(self, self.wavelengths[int(len(self.wavelengths) * 0.7)])
        self.wavelength3 = tk.StringVar(self, self.wavelengths[int(len(self.wavelengths) * 0.6)])
#GUI entries
        self.menu_left = tk.Frame(self, width=150, bg="#ababab")
        #upper and lower menus are grid arranged
        self.menu_left_upper = tk.Frame(self.menu_left, width=150, height=150, bg="red")
        self.menu_left_lower = tk.Frame(self.menu_left, width=150, bg="blue")

        self.heading = tk.Label(self.menu_left_upper, text="Spectrometer Controls")
        self.heading.grid(column=0, row=0, columnspan=2)
        self.heading = tk.Label(self.menu_left_lower, text="PowerSupply Controls")
        self.heading.grid(column=0, row=0, columnspan=2)
        
        self.menu_left_upper.pack(side="top", fill="both", expand=True)
        self.menu_left_lower.pack(side="top", fill="both", expand=True)
        #upper menu (use Grid placement)
        self.wavelen1boxlabel = tk.Label(self.menu_left_upper, text='Line Wavelength 1:', fg = 'red', relief = 'ridge')
        self.wavelen1boxlabel.grid(column=0, row=1)
        self.wavelen1box = Spinbox(self.menu_left_upper, values = list(self.wavelengths), textvariable=self.wavelength1, width=7, format="%.3f", command=self.wavelenaction)# only valid wavelengths displayed
        self.wavelength1.set(self.wavelengths[int(len(self.wavelengths) * 0.8)]) # using values list sets first index as default, this 'set' inserts preferred initial value; (int(len()) gets index position
        self.wavelen1box.bind('<Return>', self.wavelen_entry) and self.wavelen1box.bind('<Tab>', self.wavelen_entry)
        self.wavelen1box.grid(column=1, row=1)
        self.wavelen2boxlabel = tk.Label(self.menu_left_upper, text=' Bkg Wavelength 2:', fg = 'green', relief = 'ridge')
        self.wavelen2boxlabel.grid(column=0, row=2)
        self.wavelen2box = Spinbox(self.menu_left_upper, values = list(self.wavelengths), textvariable=self.wavelength2, width=7, format="%.3f", command=self.wavelenaction)# only valid wavelengths displayed
        self.wavelength2.set(self.wavelengths[int(len(self.wavelengths) * 0.7)])
        self.wavelen2box.bind('<Return>', self.wavelen_entry) and self.wavelen2box.bind('<Tab>', self.wavelen_entry)
        self.wavelen2box.grid(column=1, row=2)
        self.wavelen3boxlabel = tk.Label(self.menu_left_upper, text='Base Wavelength 3:', fg = 'purple', relief = 'ridge')
        self.wavelen3boxlabel.grid(column=0, row=3)
        self.wavelen3box = Spinbox(self.menu_left_upper, values = list(self.wavelengths), textvariable=self.wavelength3, width=7, format="%.3f", command=self.wavelenaction)# only valid wavelengths displayed
        self.wavelength3.set(self.wavelengths[int(len(self.wavelengths) * 0.6)])
        self.wavelen3box.bind('<Return>', self.wavelen_entry) and self.wavelen3box.bind('<Tab>', self.wavelen_entry)
        self.wavelen3box.grid(column=1, row=3)
        self.wavelength1 = self.wavelen1box.get() #REQUIRED read StringVar as String for passing to next function
        self.wavelength2 = self.wavelen2box.get()
        self.wavelength3 = self.wavelen3box.get()
        # X axis visible range
        self.xminlabel = tk.Label(self.menu_left_upper, text='Minimum Wavelength', relief = 'ridge')
        self.xminlabel.grid(column=0, row=4)
        self.xminentry = tk.Entry(self.menu_left_upper, width = 7)
        self.xminentry.grid(column=1, row=4)
        self.xminentry.insert(0, self.xmin)
        self.xminentry.bind('<Return>', self.Xscale_change) and self.xminentry.bind('<Tab>', self.Xscale_change)
        self.xmaxlabel = tk.Label(self.menu_left_upper, text='Maximum Wavelength', relief = 'ridge')
        self.xmaxlabel.grid(column=0, row=5)
        self.xmaxentry = tk.Entry(self.menu_left_upper, width = 7)
        self.xmaxentry.grid(column=1, row=5)
        self.xmaxentry.insert(0, self.xmax)
        self.xmaxentry.bind('<Return>', self.Xscale_change) and self.xmaxentry.bind('<Tab>', self.Xscale_change)
        # Integration time
        self.integrationlabel = tk.Label(self.menu_left_upper, text='Integration \r time (ms)', relief = 'ridge')
        self.integrationlabel.grid(column=0, row=6)
        self.integrationentry = tk.Entry(self.menu_left_upper, width = 7)
        self.integrationentry.grid(column=1, row=6)
        self.integrationentry.insert(0, int(self.IntTime / 1000))  #display ms value of IntTime
        self.integrationentry.bind('<Return>', self.IntegrationTime) and self.integrationentry.bind('<Tab>', self.IntegrationTime)
        # rescale Y and X buttons
        self.button_rescaleY = tk.Button(self.menu_left_upper, text='Rescale Y')
        self.button_rescaleY.grid(column=0, row=7)
        self.button_rescaleY.bind('<ButtonRelease-1>', self.RescaleY)
        self.button_fullscaleY = tk.Button(self.menu_left_upper, text='Fullscale Y')
        self.button_fullscaleY.grid(column=0, row=8)
        self.button_fullscaleY.bind('<ButtonRelease-1>', self.FullscaleY)
        self.button_fullscaleX = tk.Button(self.menu_left_upper, text='Fullscale X')
        self.button_fullscaleX.grid(column=1, row=8)
        self.button_fullscaleX.bind('<ButtonRelease-1>', self.FullscaleX)
        # Display mode
        self.DisplayCode = 1 #spectrum display
        self.modelabel = tk.Label(self.menu_left_upper, text='Display Mode switch', relief = 'ridge')
        self.modelabel.grid(column=0, row=9)
        self.button_DisplayMode = tk.Button(self.menu_left_upper, text='Spectrum', width=10) #will change text dynamically with use
        self.button_DisplayMode.grid(column=1, row=9)
        self.button_DisplayMode.bind('<ButtonRelease-1>', self.DisplayMode)
        # Time Series length
        self.timelimitlabel = tk.Label(self.menu_left_upper, text='Time series \rlength (s)', relief = 'ridge')
        self.timelimitlabel.grid(column=0, row=10)
        self.timelimitentry = tk.Entry(self.menu_left_upper, width = 7)
        self.timelimitentry.grid(column=1, row=10)
        self.timelimitentry.insert(0, self.timelimit)
        self.timelimitentry.bind('<Return>', self.TimeLimit_change) and self.timelimitentry.bind('<Tab>', self.TimeLimit_change)
                
        #lower menu (use Grid placement)
        self.PSscroll = Scrollbar(self.menu_left_lower)
        self.PSscroll.grid(column=1, row=1, sticky='ns')
        self.PStext = Text(self.menu_left_lower, width =25, height = 12)
        self.PStext.insert(tk.END, "Some text here \n")
        self.PStext.grid(column=0, row=1) #, columnspan=2)
        self.PStext.config(yscrollcommand=self.PSscroll.set)
        self.PSscroll.config(command=self.PStext.yview)
        #self.PSentrylabel = tk.Label(self.menu_left_lower, text='PS command:', relief = 'ridge')
        #self.PSentrylabel.grid(column=0, row=2)
        #self.PSentry = tk.Entry(self.menu_left_lower, width='10')
        #self.PSentry.bind('<Return>', self.writeSerial)
        #self.PSentry.grid(column=1, row=2)
        self.PSconnect = tk.Button(self.menu_left_lower, text='Connect/Disconnect', bg = "pink", font='bold')
        self.PSconnect.grid(column=0, row=2)#, columnspan=1)
        self.PSconnect.bind('<ButtonRelease-1>', self.Connect_PS)

        self.PS_go_label = tk.Label(self.menu_left_lower, text='Start PS and spectro', relief = 'ridge')
        self.PS_go_label.grid(column=0, row=3)
        self.PS_go_button = tk.Button(self.menu_left_lower, text='Measure')
        self.PS_go_button.grid(column=1, row=3)
        self.PS_go_button.bind('<ButtonRelease-1>', self.PS_go)

        self.PS_name_label = tk.Label(self.menu_left_lower, text='BK Precision', font='bold')
        self.PS_name_label.grid(column=0, row=4)
        self.PS_emergencystop_button = tk.Button(self.menu_left_lower, text='Stop PS', bg='red', fg='white', font='bold')
        self.PS_emergencystop_button.grid(column=1, row=4)
        self.PS_emergencystop_button.bind('<ButtonRelease-1>', self.PS_EmergencyStop)

        tk.Label(self.menu_left_lower, text = "COM port", relief = 'sunken').grid(column=0, row=5, pady=10)
        self.ports_box = ttk.Combobox(self.menu_left_lower, values = scanSerial())
        self.ports_box.grid(column = 1, row = 5)
        self.ports_box.bind('<<ComboboxSelected>>', self.on_selectComm)

        # right display area -- Spectrograph Plot Area
        self.some_title_frame = tk.Frame(self, bg="#dfdfdf")
        self.some_title = tk.Label(self.some_title_frame, text="Spectrograph Window", bg="#dfdfdf")
        self.some_title.pack()
        #buttons at top of Spectrum region        
        self.btn = tk.Button(self.some_title_frame, text='Start', command=self.on_click)
        self.btn.pack(side=tk.RIGHT)
        
        #first two lines give a functioning empty box
        self.canvas_area = tk.Canvas(self, width=700, height=500, background="#ffffff")
        self.canvas_area.grid(row=1, column=1)
        
        #lower status bar
        self.status_frame = tk.Frame(self)
        self.status = tk.Label(self.status_frame, text=spec)
        self.status.pack(fill="both", expand=True)

        #set locations of the major areas to the corners of the box
        self.menu_left.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.some_title_frame.grid(row=0, column=1, sticky="ew")
        self.canvas_area.grid(row=1, column=1, sticky="nsew") 
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
#End GUI entries
        
#Create plot area
        #create plot object and draw it with empty data before starting matplotlib line artists
        # 'ax1' is ax"one" not a letter
        self.fig = plt.Figure()
        self.ax1 = self.fig.add_subplot(111)
        self.line, = self.ax1.plot([], [], lw=1, color='blue') #creates empty line !! comma is important for Blit
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1)

#Axis limits. Get from the spectrograph data
        self.ax1.set_ylim(self.ymin, self.ymax)
        self.ax1.set_xlim(self.xmin, self.xmax) 
        self.ax1.set_xlabel('Wavelength (nm)')
        self.ax1.grid(True, color='0.3', ls='dotted')  # places dark grid on spectrum display
#Create the line artist objects for Blit
        self.waveline1, = self.ax1.plot([], [], lw=2, color='red', alpha = 0.5)  #create empty objects because these lines are Blit artists
        self.waveline2, = self.ax1.plot([], [], lw=2, color='green', alpha = 0.5)
        self.waveline3, = self.ax1.plot([], [], lw=2, color='purple', alpha = 0.5)
        self.linedata, = self.ax1.plot([], [], '.', color='red', markevery=5)
        self.bkgdata, = self.ax1.plot([], [], '.', color='green', markevery=5)
        #self.basedata, = self.ax1.plot([], [], '.', color='purple', markevery=5)  #not usually displayed
        self.bm = BlitManager(self.fig.canvas, [self.line, self.waveline1, self.waveline2, self.waveline3]) #remember to send all lines to the Class !! set bm because the first screen is always a spectrum
#end artist creation

    def on_click(self):
        # Start button will start infinite cycle on whole spectrum or start an individual time series.
        gc.collect()
        self.bm = BlitManager(self.fig.canvas, [self.line, self.waveline1, self.waveline2, self.waveline3]) #reset blit to spectrum mode
        self.btn.config(text='Running')
        return self.update_graph()

    def update_graph(self):
        # if DisplayCode = 1 then do spectrum;  else do timeseries as below
        self.canvas.draw()  # guarantees that all lines and scaling get reset
        
        while self.DisplayCode == 1:
            self.line.set_data(self.wavelengths, get_intensities()) # update matplotlib line data
            self.bm.update()  #redraw with blit manager call
 
        else:
            self.bm = BlitManager(self.fig.canvas, [self.linedata, self.bkgdata])#, self.basedata])
            gc.collect()
            xdata = []
            linedata = []
            bkgdata = []
            basedata = []  # base data is calculated but not drawn to save on drawing overhead and gain speed
            self.linedata.set_data(xdata, linedata)
            self.bkgdata.set_data(xdata, bkgdata)
            #self.basedata.set_data(xdata, basedata)  #not usually displayed
            self.canvas.draw() # this draw and the lines above blank the display area before a repeat cycle
            index1 = np.where(self.wavelengths == float(self.wavelength1))[0]  #array index of the chosen wavelength
            index2 = np.where(self.wavelengths == float(self.wavelength2))[0]
            index3 = np.where(self.wavelengths == float(self.wavelength3))[0]
            starttime = perf_counter()  # better quality time counter
            for zzz in range(self.timelimit * int(1000/self.IntTime*1000) + 2):  # 2 extra cycles to catch end of process
                ydata = np.array(get_intensities()) # gets full data
                xdata.append(perf_counter() - starttime) # appends elapsed time on each cycle
                linedata.append(np.ndarray.item(ydata[index1]))  ### NEW scalar extraction conforms to Numpy > 1.25
                bkgdata.append(np.ndarray.item(ydata[index2]))   # deprecated use of float to get a scalar
                basedata.append(np.ndarray.item(ydata[index3]))
                self.linedata.set_data(xdata, linedata)  # update matplotlib line data
                self.bkgdata.set_data(xdata, bkgdata)
                #self.basedata.set_data(xdata, basedata)  # not usually displayed
                self.bm.update()  # blit manager call
        #diagnostics printed to terminal, can be removed ----
            #print("per point = ", str((perf_counter()-starttime)/(self.timelimit * int(1000/self.IntTime*1000))))
            #print("std dev = ", str(np.std(np.diff(xdata))))
            #print("max = ", str(np.amax(np.diff(xdata))))
            #print("# over inttime = ", sum(i>(1.05*self.IntTime/1000000) for i in np.diff(xdata)))
            #print(np.where(np.asarray(xdata)>(self.IntTime/1000)))
            #print(np.diff(xdata))
            #fig2, ax2 = plt.subplots()
            #ax2.plot(xdata[0:len(xdata)-1], np.diff(xdata), 'o')
            #fig2.canvas.manager.show()
        #end diagnostics -----
            self.btn.config(text='Start')
            gc.collect()  # garbage collector
        # save data
            xdata=np.asarray(xdata)
            linedata=np.asarray(linedata)
            bkgdata=np.asarray(bkgdata)
            basedata=np.asarray(basedata)
            saveFile(xdata, linedata, bkgdata, basedata, self.wavelength1, self.wavelength2, self.wavelength3)

    def wavelenaction(self):
        self.wavelength1 = self.wavelen1box.get()
        self.wavelength2 = self.wavelen2box.get()
        self.wavelength3 = self.wavelen3box.get()
        self.waveline1.set_data([float(self.wavelength1), float(self.wavelength1)], [self.ymin, self.ymax]) #update line position here to make data loop faster
        self.waveline2.set_data([float(self.wavelength2), float(self.wavelength2)], [self.ymin, self.ymax])
        self.waveline3.set_data([float(self.wavelength3), float(self.wavelength3)], [self.ymin, self.ymax])
        self.bm.update()   # update the line locations with self.bm.update()

    def wavelen_entry(self, event):
        tempwavelen1 = self.wavelen1box.get()
        if self.check_valid_wavelength(tempwavelen1) == True:
            index_wavelen1 = int(np.searchsorted(self.wavelengths, float(tempwavelen1), side='left'))
            self.wavelength1 = self.wavelengths[index_wavelen1]
            self.wavelen1box.delete(0, 'end')
            self.wavelen1box.insert(0, self.wavelength1)  #set text in wavelength1 box
            self.wavelenaction()
        else:
            self.wavelen1box.delete(0, 'end')
            self.wavelen1box.insert(0, self.wavelength1)

        tempwavelen2 = self.wavelen2box.get()
        if self.check_valid_wavelength(tempwavelen2) == True:
            index_wavelen2 = int(np.searchsorted(self.wavelengths, float(tempwavelen2), side='left'))
            self.wavelength2 = self.wavelengths[index_wavelen2]
            self.wavelen2box.delete(0, 'end')
            self.wavelen2box.insert(0, self.wavelength2)  #set text in wavelength2 box
            self.wavelenaction()
        else:
            self.wavelen2box.delete(0, 'end')
            self.wavelen2box.insert(0, self.wavelength2)

        tempwavelen3 = self.wavelen3box.get()
        if self.check_valid_wavelength(tempwavelen3) == True:
            index_wavelen3 = int(np.searchsorted(self.wavelengths, float(tempwavelen3), side='left'))
            self.wavelength3 = self.wavelengths[index_wavelen3]
            self.wavelen3box.delete(0, 'end')
            self.wavelen3box.insert(0, self.wavelength3)  #set text in wavelength3 box
            self.wavelenaction()
        else:
            self.wavelen3box.delete(0, 'end')
            self.wavelen3box.insert(0, self.wavelength3)
        
    def check_valid_wavelength(self, wave_to_check):
        try:
            float(wave_to_check)  #can string be converted to float?
            if (float(wave_to_check) < self.xmax) and (float(wave_to_check) > self.xmin): #entry is within current bounds
              return(True)
            else:
                return(False)
        except:
            return(False)
        
    def RescaleY(self, event):
        index_xmin = np.searchsorted(self.wavelengths, self.xmin, side='left')
        index_xmax = np.searchsorted(self.wavelengths, self.xmax, side='left')
        ydata = np.around(get_intensities(), decimals=2)
        self.ymin = np.around(min(ydata[index_xmin:index_xmax])*0.8, decimals=2)
        self.ymax = np.around(max(ydata[index_xmin:index_xmax])*1.1, decimals=2)
        self.ax1.set_ylim(self.ymin, self.ymax)
        self.waveline1.set_data([float(self.wavelength1), float(self.wavelength1)], [self.ymin, self.ymax])
        self.waveline2.set_data([float(self.wavelength2), float(self.wavelength2)], [self.ymin, self.ymax])
        self.waveline3.set_data([float(self.wavelength3), float(self.wavelength3)], [self.ymin, self.ymax])
        self.canvas.draw() # guarantees that axes redraw too

    def FullscaleY(self, event):
        self.ymin = -10
        self.ymax = self.max_intensity
        self.ax1.set_ylim(self.ymin, self.ymax)
        self.waveline1.set_data([float(self.wavelength1), float(self.wavelength1)], [self.ymin, self.ymax])
        self.waveline2.set_data([float(self.wavelength2), float(self.wavelength2)], [self.ymin, self.ymax])
        self.waveline3.set_data([float(self.wavelength3), float(self.wavelength3)], [self.ymin, self.ymax])
        self.canvas.draw() # guarantees that axes redraw too

    def DisplayMode(self, event):
        if self.DisplayCode == 1:  # handles change to time series (time series is code 0)
            self.DisplayCode = 0
            self.button_DisplayMode.configure(text='Time Series')
            self.ax1.set_ylim(self.ymin*0.8, self.ymax*2)  # generous upper limit for signals
            self.ax1.set_xlim(-1, self.timelimit*1.05) #testing limits
            self.ax1.set_xlabel('Time (s)')
            self.ax1.grid(True, color='1', ls='solid')  # places negative space grid on spectrum display
            self.canvas.draw()
            # DisplayCode is also in the 'def update_graph()'
        else:
            self.DisplayCode = 1  # handles change to spectrum
            self.button_DisplayMode.configure(text='Spectrum')
            self.ax1.set_ylim(self.ymin*0.8, self.ymax*1.1)
            self.ax1.set_xlim(self.xmin, self.xmax)  # max and min wavelengths from reported (self.xmin, self.xmax)
            self.ax1.set_xlabel('Wavelength (nm)')
            self.ax1.grid(True, color='0.3', ls='dotted')  # places dark grid on spectrum display
            self.canvas.draw()

    def Xscale_change(self, event):  #always do both xmin and xmax on change of either
        xmintemp = self.xminentry.get()
        xmaxtemp = self.xmaxentry.get()
        try:  
            float(xmintemp)
            xmintemp = float(self.xminentry.get())
            float(xmaxtemp)
            xmaxtemp = float(self.xmaxentry.get())
            if (xmintemp < self.xmax) and (xmaxtemp > self.xmin) and (xmintemp >= self.xminlimit) and (xmaxtemp <= self.xmaxlimit):
                self.xmin = xmintemp
                self.xminentry.delete(0, 'end')
                self.xminentry.insert(0, self.xmin)  #set text in xmin box
                self.xmax = xmaxtemp
                self.xmaxentry.delete(0, 'end')
                self.xmaxentry.insert(0, self.xmax)  #set text in xmax box
                self.ax1.set_xlim(self.xmin, self.xmax)  # set the new value on plot area
                self.canvas.draw()
            else:
                msg = "Minimum wavelength must be greater than " + str(self.xminlimit) + "nm and maximum smaller than " + str(self.xmaxlimit) + "nm.  Also, max greater than min.  You entered: min = " + str(xmintemp) + " nm and max = " + str(xmaxtemp) + " nm."
                self.xminentry.delete(0, 'end')
                self.xminentry.insert(0, self.xmin)  #reset original xmin in box
                self.xmaxentry.delete(0, 'end')
                self.xmaxentry.insert(0, self.xmax)  #reset original xmax in box
                messagebox.showerror("Entry error", msg)
        except:
            self.xminentry.delete(0, 'end')
            self.xminentry.insert(0, self.xmin)  #reset original xmin in box
            self.xmaxentry.delete(0, 'end')
            self.xmaxentry.insert(0, self.xmax)  #reset original xmax in box

    def FullscaleX(self, event):
        self.xmin = self.xminlimit  # get wavelength limit from instrument data
        self.xminentry.delete(0, 'end')
        self.xminentry.insert(0, self.xmin)  #set text in xmin box
        self.xmax = self.xmaxlimit
        self.xmaxentry.delete(0, 'end')
        self.xmaxentry.insert(0, self.xmax)  #set text in xmax box
        self.ax1.set_xlim(self.xmin, self.xmax)
        self.canvas.draw()

    def IntegrationTime(self, event):
        #typically OO spectrometers can't read faster than 4 ms
        #and we don't want integration times too long on accident 
        IntTimeTemp = self.integrationentry.get()
        if IntTimeTemp.isdigit() == True:
            if int(IntTimeTemp) > 5000: # maxIntTime may be up to 60 seconds depending on spectrometer model
                msg = "The integration time must be 5000 ms or smaller.  You set " +(IntTimeTemp)
                self.integrationentry.delete(0, "end")
                self.integrationentry.insert(0, int(self.IntTime / 1000))
                messagebox.showerror("Entry error", msg)
            elif int(IntTimeTemp) < 4:  # minIntTime may be for shutter mode and much smaller free-running mode limits
                msg = "The integration time must be greater than 4 ms.  You set " +(IntTimeTemp)
                self.integrationentry.delete(0, "end")
                self.integrationentry.insert(0, int(self.IntTime / 1000))
                messagebox.showerror("Entry error", msg)
            else:
                self.IntTime = int(IntTimeTemp) * 1000  #convert ms to microseconds
                spec.integration_time_micros(self.IntTime)  #send IntTime to spectrograph
                self.integrationentry.delete(0, "end")
                self.integrationentry.insert(0, int(self.IntTime / 1000)) #write in ms, but IntTime is in microseconds

        else:
            msg = "Integration time must be an integer between 4 and 5000 ms.  You set " +str(IntTimeTemp)
            self.integrationentry.delete(0, "end")
            self.integrationentry.insert(0, int(self.IntTime / 1000))
            messagebox.showerror("Entry error", msg)
            self.canvas.draw()

    def TimeLimit_change(self, event):
        timelimittemp = self.timelimitentry.get()
        try:
            int(timelimittemp)
            timelimittemp = int(self.timelimitentry.get())
            if timelimittemp > 0 and timelimittemp < 300:   # arbitrary upper limit of 5 minutes (can be changed)
                self.timelimit = timelimittemp
                self.timelimitentry.delete(0, 'end')
                self.timelimitentry.insert(0, self.timelimit) # set new text in time limit box
            else:
                self.timelimitentry.delete(0, 'end')
                self.timelimitentry.insert(0, self.timelimit) # reset original time limit to box
                
        except:  #non numerical entry handler
            self.timelimitentry.delete(0, 'end')
            self.timelimitentry.insert(0, self.timelimit) # reset original time limit to box
            
        if self.DisplayCode == 0:
            self.ax1.set_xlim(-1, self.timelimit*1.05)
            self.canvas.draw()

    def Connect_PS(self, event):
        #print("start of def")
        #print(ser.isOpen())
        #print(ser)
        if (ser.isOpen() == True):  #checks if serial port is open
            try:
                self.PSconnect.configure(background = 'pink')
                self.PStext.insert(tk.END, "disconnected serial \n")
                ser.close()
            except:
                print("exception")
                self.PSconnect.configure(background = 'pink')
        else:
            try:
                self.PSconnect.configure(background = 'light green')
                self.PStext.insert(tk.END, "connected serial \n")
                ser.open()
                maxvalues = getMaxVoltCurr(ser)
                self.PStext.insert(tk.END, str(maxvalues[1]) + " amps maximum \n")
                self.PStext.insert(tk.END, str(maxvalues[0]) + " volts maximum \n")
            except:
                self.PStext.insert(tk.END, "Is another program using the serial port? Or no port selected? \n")
                self.PSconnect.configure(background = 'pink')
        #print("after def")
        #print(ser.isOpen())
            
                
    def on_selectComm(self, event):
        global ser
        #print (ser)
        port = self.ports_box.get()
        ser.port = port
        #print("after get")
        #print(ser)

    def PS_go(self, event):  # runs power supply and starts time-based data collection in one click
        gc.collect()
        self.DisplayCode = 1 # simulates button press to go to time series mode
        self.DisplayMode(event)
        self.btn.config(text='Running')
        address = 0
        times = 1
        GO_string = "RUNP"+"%02d"%address+"%03d\r"%times  # sends 'R' as in Run and the slot number formatted for MasTech powersupply
        
        #send serial command to start power supply
        if (ser.isOpen() == True):  #checks for True
            self.PStext.insert(tk.END, "sent: ")
            self.PStext.insert(tk.END, GO_string)
            self.PStext.insert(tk.END, "\n")
            sdpWrite("SOUT"+"%02d"%address+"0\r", serial) # connects outputs on BK 1696
            sdpWrite("RUNP"+"%02d"%address+"%04d\r"%times, serial)
            return self.update_graph()  #start recording data
        else:
            self.PStext.insert(tk.END, "no connection")
            self.PStext.insert(tk.END, "\n")
            pass



    def PS_EmergencyStop(self, event):
        if(ser.isOpen() == False):  # check if serial port is open
            ser.open()
        address = 0
        self.PStext.insert(tk.END, "sent: ")
        self.PStext.insert(tk.END, "STOP"+"%02d\r"%address)
        self.PStext.insert(tk.END, "\n")  # echos line feed
        sdpWrite("STOP"+"%02d\r"%address, ser)
        ser.flush()  # avoids accidental stray instructions

def sdpWrite(cmd, serial):
    ser.write(cmd.encode())
    #return ser.read_until(terminator=b'\r')  #prior to v3.5 of BK Precision vendor software
    return ser.read_until(expected=b'\r')

def remoteMode(state, address=0):
    """Enable or Disable Remote mode. Other commands over usb automatically set PS to remote"""
    """state - True/False = Enable/Disable"""
    if state == True:
        sdpWrite("SESS"+"%02d"%address+"\r", serial)
        print(state)
    else:
        sdpWrite("ENDS"+"%02d"%address+"\r", serial)
        print(state)

def getMaxVoltCurr(serial, address=0):
    """Get the maximum voltage and current from the supply. The response is an array: [0] = voltage, [1] = current"""
    #print("GMAX"+"%02d"%address+"\r", serial)
    resp = sdpQuery("GMAX"+"%02d"%address+"\r", serial)
    #return [int(resp[0:3])/10., int(resp[0][3:5])/10.]  #had to edit the parsing for Python 3, see next line
    return [int(str(int(resp))[0:3])/10., int(str(int(resp))[3:6])/100.]

def sdpQuery(cmd, serial):
    resp = []
    notDone = True
    ser.write(cmd.encode())
    while(notDone):
        #r = ser.read_until(terminator=b'\r')  #prior to v3.5
        r = ser.read_until(expected=b'\r')
        if(not(len(r) > 0)):
           notDone = False
        else:
            resp.append(r)
    return resp[0]

def scanSerial():
    ports = serial.tools.list_ports.comports()
    com_list = []
    for p in ports:
        com_list.append(p.name)
    return com_list

class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for sub-classes of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        #...let's try removing the paranoia??
#        if self._bg is None:
#            self.on_draw(None)
#        else:
        # restore the background
        cv.restore_region(self._bg)
        # draw all of the animated artists
        self._draw_animated()
        # update the GUI state
        cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()

def saveFile(data_time, data_line, data_bkg, data_base, linewave, bkgwave, basewave):
    filenameforWriting = asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"),("All files", "*.*")])
    if not filenameforWriting:
        pass  #exits on Cancel
    else:
        path_ext = os.path.splitext(filenameforWriting)
        linefile = str(path_ext[0] + "line" + path_ext[1])
        bkgfile = str(path_ext[0] + "bkg" + path_ext[1])
        basefile = str(path_ext[0] + "base" + path_ext[1])
        specmodel = spec.model
        lineheader = "# Spectrometer = " + specmodel + "\n# Wavelength (nm) = " + linewave + "\n# Analytical Line data \n# Time (s), Count"
        bkgheader = "# Spectrometer = " + specmodel + "\n# Wavelength (nm) = " + bkgwave + "\n# Background data \n# Time (s), Count"
        baseheader = "# Spectrometer = " + specmodel + "\n# Wavelength (nm) = " + basewave + "\n# Baseline data \n# Time (s), Count"
        np.savetxt(linefile, np.transpose([data_time, data_line]), delimiter=',', newline='\n', header=lineheader, comments='')
        np.savetxt(bkgfile, np.transpose([data_time, data_bkg]), delimiter=',', newline='\n', header=bkgheader, comments='')
        np.savetxt(basefile, np.transpose([data_time, data_base]), delimiter=',', newline='\n', header=baseheader, comments='')

def processData():
    pass
    # processing is in a separate program file
    # we could call that module with a button here but separating data collection
    # from processing is a reasonable separation

def main():
    root = tk.Tk()
    root.wm_title("Tungsten ETA Data Collection")
    app = App(root)
    app.pack()
    root.mainloop()

if __name__ == '__main__':
    main()
