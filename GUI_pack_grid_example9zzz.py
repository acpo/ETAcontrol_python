# Functional.  Correctly uses spectrometer values for variables.
# To do:  serial comms.
# With 3 lines showing in real time, minimum IntTime is 25ms due to extra drawing overhead
# Reduced to 2 drawn lines (not drawing Base).  25ms is solid, 24ms is ok but some small random shifts

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from tkinter import scrolledtext
from tkinter import Spinbox
from tkinter import Text
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib import style
style.use("ggplot")
plt.rcParams['axes.facecolor']='#F8F8F8'
plt.rcParams['lines.color']='blue'
plt.rcParams['figure.figsize'] = [9.0, 7.0]

import seabreeze.spectrometers as sb
import numpy as np

import time
from time import (process_time, perf_counter)
import os #for filename and path handling
import csv  #easier file writing
import gc  #garbage collection

# Enumerate spectrometer, set a default integration time, get x & y extents
try:
    spec = sb.Spectrometer.from_serial_number()
except:
    messagebox.showerror("Error", "No spectrometer attached")
    exit()

# Spectrometer data collectors
def get_wavelengths():
    spec_x = spec.wavelengths()
    return spec_x
def get_intensities():
    spec_y = spec.intensities(correct_dark_counts=True, correct_nonlinearity=False) #dark counts might need to be false
    return spec_y

class App(tk.Frame):
    def __init__(self, master=None, **kwargs):

        tk.Frame.__init__(self, master, **kwargs)

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
        self.IntTime = 25000 #set in microseconds, this is 10ms
        spec.integration_time_micros(self.IntTime)  #send IntTime to spectrograph
        self.IntTimeLimits = spec.integration_time_micros_limits #BIGGER RANGE THAN REALLY EXISTS; this is available if needed;reads as tuple
        self.max_intensity = spec.max_intensity  #fullscale limit
        self.timelimit = 5 # time in SECONDS

        #preload wavelength values
        self.wavelength1 = tk.StringVar(self, self.wavelengths[int(len(self.wavelengths) * 0.8)])
        self.wavelength2 = tk.StringVar(self, self.wavelengths[int(len(self.wavelengths) * 0.7)])
        self.wavelength3 = tk.StringVar(self, self.wavelengths[int(len(self.wavelengths) * 0.6)])
#GUI entries
        self.menu_left = tk.Frame(self, width=150, bg="#ababab")
        #upper menu is grid controlled
        self.menu_left_upper = tk.Frame(self.menu_left, width=150, height=150, bg="red")
        #lower menu is pack controlled
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
                
        #lower menu (use Pack placement)
        self.PStext = Text(self.menu_left_lower, width =25, height = 10)
        #self.PStext = scrolledtext.ScrolledText(self.menu_left_lower, width =20, height = 15)
        self.PStext.insert(tk.END, "Some text here \n")
        self.PStext.grid(column=0, row=1, columnspan=2)
        
        self.PSentrylabel = tk.Label(self.menu_left_lower, text='PS command:')
        self.PSentrylabel.grid(column=0, row=2)
        self.PSentry = tk.Entry(self.menu_left_lower, width='12')
        #will need: self.menu_left_lower.bind('<Return>', self.PSentry_return)
        self.PSentry.grid(column=1, row=2)
        self.PS_go_label = tk.Label(self.menu_left_lower, text='Start PS and spectro')
        self.PS_go_label.grid(column=0, row=3)
        self.PS_go_button = tk.Button(self.menu_left_lower, text='Measure')
        self.PS_go_button.grid(column=1, row=3)
        self.PS_go_button.bind('<ButtonRelease-1>', self.PS_go)
        self.PSslot = 1
        self.PS_slot_label = tk.Label(self.menu_left_lower, text='Power Supply memory slot')
        self.PS_slot_label.grid(column=0, row=4)
        self.PS_slot = tk.Spinbox(self.menu_left_lower, from_=0, to=7, textvariable=self.PSslot, width=3)
        self.PS_slot.grid(column=1, row=4)
        
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
        #self.status = tk.Label(self.status_frame, text="this is the status bar")
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
        self.ax1.set_xlim(self.xmin, self.xmax)  # max and min wavelengths from reported (self.xmin, self.xmax)
        self.ax1.set_xlabel('Wavelength (nm)')
#Create the line artist objects for Blit
        self.waveline1, = self.ax1.plot([], [], lw=2, color='red', alpha = 0.5)  #create empty objects because these lines are Blit artists
        self.waveline2, = self.ax1.plot([], [], lw=2, color='green', alpha = 0.5)
        self.waveline3, = self.ax1.plot([], [], lw=2, color='purple', alpha = 0.5)
        #self.linedata, = self.ax1.plot([], [], lw=1, color='red')
        #self.bkgdata, = self.ax1.plot([], [], lw=1, color='green')
        # !!! plotting every X points is less system intensive
        # 80 seconds at 25ms integration was ok (points) if I don't touch the computer (4 bad points out of 3200).
        self.linedata, = self.ax1.plot([], [], 'o', color='red', markevery=20)
        self.bkgdata, = self.ax1.plot([], [], 'o', color='green', markevery=20)
        #self.basedata, = self.ax1.plot([], [], lw=1, color='purple')  #not usually displayed
        self.bm = BlitManager(self.fig.canvas, [self.line, self.waveline1, self.waveline2, self.waveline3]) #remember to send all lines to the Class !! set bm because the first screen is always a spectrum
#end artist creation

    def on_click(self):
        # Start button will start infinite cycle on whole spectrum or start an individual time series.
        gc.collect()
        self.bm = BlitManager(self.fig.canvas, [self.line, self.waveline1, self.waveline2, self.waveline3])#reset blit to spectrum mode
        self.btn.config(text='Running')
        return self.update_graph()

    def update_graph(self):
        #if DisplayCode = 1 then do spectrum;  else do timeseries as below
        self.canvas.draw()  # might be needed to reset lines?
        
        while self.DisplayCode == 1:
            self.line.set_data(self.wavelengths, get_intensities()) # update graph
            self.bm.update()  #redraw with blit manager call
 
        else:
            self.bm = BlitManager(self.fig.canvas, [self.linedata, self.bkgdata])#, self.basedata])
            gc.collect()
            xdata = []
            linedata = []
            bkgdata = []
            basedata = []  #base data is calculated but not drawn to save on drawing overhead and gain speed
            self.linedata.set_data(xdata, linedata)
            self.bkgdata.set_data(xdata, bkgdata)
            #self.basedata.set_data(xdata, basedata)  #not usually displayed
            self.canvas.draw() # this draw and the lines above blank the display before a repeat cycle
            index1 = np.where(self.wavelengths == float(self.wavelength1))[0]  #array index of the chosen wavelength
            index2 = np.where(self.wavelengths == float(self.wavelength2))[0]
            index3 = np.where(self.wavelengths == float(self.wavelength3))[0]
            starttime = perf_counter()
            for zzz in range(self.timelimit * int(1000/self.IntTime*1000)):
                ydata = np.array(get_intensities()) # gets full data
                #xdata.append(time.time() - starttime) #correctly appends on each cycle
                xdata.append(perf_counter() - starttime) #correctly appends on each cycle
                linedata.append(float(ydata[index1]))  #append doesn't work on np.arrays
                bkgdata.append(float(ydata[index2]))
                basedata.append(float(ydata[index3]))
                self.linedata.set_data(xdata, linedata)
                self.bkgdata.set_data(xdata, bkgdata)
                #self.basedata.set_data(xdata, basedata)
                self.bm.update()  #replaced "return" with blit manager call
            print("per point = ", str((perf_counter()-starttime)/(self.timelimit * int(1000/self.IntTime*1000))))
            print("std dev = ", str(np.std(np.diff(xdata))))
            print("max = ", str(np.amax(np.diff(xdata))))
            print("# over inttime = ", sum(i>(1.05*self.IntTime/1000000) for i in np.diff(xdata)))
            #print(np.where(np.asarray(xdata)>(self.IntTime/1000)))
            print(np.diff(xdata))
            fig2, ax2 = plt.subplots()
            ax2.plot(xdata[0:len(xdata)-1], np.diff(xdata), 'o')
            fig2.canvas.manager.show() 
            self.btn.config(text='Start')
            gc.collect()
#demo of a workable data saving routine
            xdata=np.asarray(xdata)
            linedata=np.asarray(linedata)
            bkgdata=np.asarray(bkgdata)
            basedata=np.asarray(basedata)
            #saveFile(xdata, linedata, bkgdata, basedata)

    def wavelenaction(self):
        self.wavelength1 = self.wavelen1box.get()
        self.wavelength2 = self.wavelen2box.get()
        self.wavelength3 = self.wavelen3box.get()
        self.waveline1.set_data([float(self.wavelength1), float(self.wavelength1)], [self.ymin, self.ymax]) #update line position here to make data loop faster
        self.waveline2.set_data([float(self.wavelength2), float(self.wavelength2)], [self.ymin, self.ymax])
        self.waveline3.set_data([float(self.wavelength3), float(self.wavelength3)], [self.ymin, self.ymax])
        self.bm.update()
        # update the line locations with self.bm.update()

    def wavelen_entry(self, event):
        tempwavelen1 = self.wavelen1box.get()
        if self.check_valid_wavelength(tempwavelen1) == True:
            index_wavelen1 = int(np.searchsorted(self.wavelengths, float(tempwavelen1), side='left'))
            self.wavelength1 = self.wavelengths[index_wavelen1]
            self.wavelen1box.delete(0, 'end')
            self.wavelen1box.insert(0, self.wavelength1)  #set text in xmin box
            self.wavelenaction()
        else:
            self.wavelen1box.delete(0, 'end')
            self.wavelen1box.insert(0, self.wavelength1)

        tempwavelen2 = self.wavelen2box.get()
        if self.check_valid_wavelength(tempwavelen2) == True:
            index_wavelen2 = int(np.searchsorted(self.wavelengths, float(tempwavelen2), side='left'))
            self.wavelength2 = self.wavelengths[index_wavelen2]
            self.wavelen2box.delete(0, 'end')
            self.wavelen2box.insert(0, self.wavelength2)  #set text in xmin box
            self.wavelenaction()
        else:
            self.wavelen2box.delete(0, 'end')
            self.wavelen2box.insert(0, self.wavelength2)

        tempwavelen3 = self.wavelen3box.get()
        if self.check_valid_wavelength(tempwavelen3) == True:
            index_wavelen3 = int(np.searchsorted(self.wavelengths, float(tempwavelen3), side='left'))
            self.wavelength3 = self.wavelengths[index_wavelen3]
            self.wavelen3box.delete(0, 'end')
            self.wavelen3box.insert(0, self.wavelength3)  #set text in xmin box
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
            self.canvas.draw()
            # DisplayCode is also in the 'def update_graph'
        else:
            self.DisplayCode = 1  # handles change to spectrum
            self.button_DisplayMode.configure(text='Spectrum')
            self.ax1.set_ylim(self.ymin*0.8, self.ymax*1.1)
            self.ax1.set_xlim(self.xmin, self.xmax)  # max and min wavelengths from reported (self.xmin, self.xmax)
            self.ax1.set_xlabel('Wavelength (nm)')
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
                self.ax1.set_xlim(self.xmin, self.xmax)         # Actually succeed in setting the new value
                self.canvas.draw()
            else:
                print("out of limits")
                msg = "Minimum wavelength must be greater than " + str(self.xmin) + "nm and maximum smaller than " + str(self.xmax) + "nm.  Also, max greater than min.  You entered: min = " + str(xmintemp) + " nm and max = " + str(xmaxtemp) + " nm."
                self.xminentry.delete(0, 'end')
                self.xminentry.insert(0, self.xmin)  #reset original xmin in box
                self.xmaxentry.delete(0, 'end')
                self.xmaxentry.insert(0, self.xmax)  #reset original xmax in box
                messagebox.showerror("Entry error", msg)
        except:
            print("not a number")
            self.xminentry.delete(0, 'end')
            self.xminentry.insert(0, self.xmin)  #reset original xmin in box
            self.xmaxentry.delete(0, 'end')
            self.xmaxentry.insert(0, self.xmax)  #reset original xmax in box

    def FullscaleX(self, event):
        self.xmin = self.xminlimit
        self.xminentry.delete(0, 'end')
        self.xminentry.insert(0, self.xmin)  #set text in xmin box
        self.xmax = self.xmaxlimit
        self.xmaxentry.delete(0, 'end')
        self.xmaxentry.insert(0, self.xmax)  #set text in xmax box
        self.ax1.set_xlim(self.xmin, self.xmax)
        self.canvas.draw()

    def IntegrationTime(self, event):
        #typically OO spectrometers cant read faster than 4 ms
        IntTimeTemp = self.integrationentry.get()
        if IntTimeTemp.isdigit() == True:
            if int(IntTimeTemp) > 5000: # maxIntTime may be much larger than we would ever want
                msg = "The integration time must be 5000 ms or smaller.  You set " +(IntTimeTemp)
                self.integrationentry.delete(0, "end")
                self.integrationentry.insert(0, int(self.IntTime / 1000))
                messagebox.showerror("Entry error", msg)
            elif int(IntTimeTemp) < 4:  # minIntTime may be for shutter mode and much smaller than practical
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
            if timelimittemp > 0 and timelimittemp < 300:
                self.timelimit = timelimittemp
                self.timelimitentry.delete(0, 'end')
                self.timelimitentry.insert(0, self.timelimit) # set new text in time limit box
            else:
                self.timelimitentry.delete(0, 'end')
                self.timelimitentry.insert(0, self.timelimit) # reset original time limit to box
                
        except:  #non numerical entry handler
            self.timelimitentry.delete(0, 'end')
            self.timelimitentry.insert(0, self.timelimit) # reset original time limit to box

    def PS_go(self, event):
        gc.collect()
        self.DisplayCode = 1 #simulates button press to go to time series mode
        self.DisplayMode(event)
        self.btn.config(text='Running')
        self.PStext.insert(tk.END, self.PS_slot.get())
        self.PStext.insert(tk.END, "\n")
        #send serial command to start power supply
        return self.update_graph()

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

def saveFile(data_time, data_line, data_bkg, data_base):
    filenameforWriting = asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"),("All files", "*.*")])
    if not filenameforWriting:
        pass
    else:
        path_ext = os.path.splitext(filenameforWriting)
        linefile = str(path_ext[0] + "line" + path_ext[1])
        bkgfile = str(path_ext[0] + "bkg" + path_ext[1])
        basefile = str(path_ext[0] + "base" + path_ext[1])
        np.savetxt(linefile, (data_time, data_line), delimiter=',')
        np.savetxt(bkgfile, (data_time, data_bkg), delimiter=',')
        np.savetxt(basefile, (data_time, data_base), delimiter=',')
    
def main():
    root = tk.Tk()
    app = App(root)
    app.pack()
    root.mainloop()

if __name__ == '__main__':
    main()