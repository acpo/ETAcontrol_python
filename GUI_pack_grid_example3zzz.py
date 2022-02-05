# Animated Matplotlib inside a GUI
# This shows how to separate out getting the data from the GUI

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from tkinter import scrolledtext
from tkinter import Spinbox
from tkinter import Text
from tkinter import messagebox

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
## place the initialization in the Class init?
# Enumerate spectrometer, set a default integration time, get x & y extents
#spec = sb.Spectrometer.from_serial_number()
#IntTime = 25000  #25 ms, set default integration time to a reasonable value
#spec.integration_time_micros(IntTime)
#x = spec.wavelengths()
#data = spec.intensities(correct_dark_counts=True, correct_nonlinearity=False)
#xmin = np.around(min(x), decimals=2)
#xmax = np.around(max(x), decimals=2)
#ymin = np.around(min(data), decimals=2)
#ymax = np.around(max(data), decimals=2)
#minIntTime =spec.minimum_integration_time_micros

#for testing purposes
import random
#end testing

def get_data():
    '''replace this function with whatever you want to provide the data
    for now, we just return soem random data'''
    rand_x = list(range(200, 300, 1))
    rand_y = [random.randrange(100) for _ in range(100)]
    return rand_x, rand_y

class App(tk.Frame):
    def __init__(self, master=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        self.running = False
        self.ani = None

        #needed for the example
        self.points_ent = 50
        self.xmin = 200
        self.xmax = 300
        #done example requirements
        self.timelimit = 60 # time in SECONDS

#my stuff starts here
        #preload wavelength values
        self.wavelength1 = tk.StringVar(self, 273.43)  #change to XX% of max wavelength to initially place them
        self.wavelength2 = tk.StringVar(self, 278.35)
        self.wavelength3 = tk.StringVar(self, 250.35)

        self.menu_left = tk.Frame(self, width=150, bg="#ababab")
        #upper menu is grid controlled
        self.menu_left_upper = tk.Frame(self.menu_left, width=150, height=150, bg="red")
        #lower menu is pack controlled
        self.menu_left_lower = tk.Frame(self.menu_left, width=150, bg="blue")

        self.heading = tk.Label(self.menu_left_upper, text="Spectrometer Controls")
        self.heading.grid(column=0, row=0, columnspan=2)
        self.heading = tk.Label(self.menu_left_lower, text="PowerSupply Controls")
        self.heading.pack()
        
        self.menu_left_upper.pack(side="top", fill="both", expand=True)
        self.menu_left_lower.pack(side="top", fill="both", expand=True)
        #upper menu (use Grid placement)
        self.wavelen1boxlabel = tk.Label(self.menu_left_upper, text='Line Wavelength 1:', fg = 'red', relief = 'ridge')
        self.wavelen1boxlabel.grid(column=0, row=1)
        self.wavelen1box = Spinbox(self.menu_left_upper, from_=200, to=300, textvariable=self.wavelength1, width=7, format="%.2f", command=self.wavelenaction)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen1box.grid(column=1, row=1)
        self.wavelen2boxlabel = tk.Label(self.menu_left_upper, text=' Bkg Wavelength 2:', fg = 'green', relief = 'ridge')
        self.wavelen2boxlabel.grid(column=0, row=2)
        self.wavelen2box = Spinbox(self.menu_left_upper, from_=200, to=300, textvariable=self.wavelength2, width=7, format="%.2f", command=self.wavelenaction)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen2box.grid(column=1, row=2)
        self.wavelen3boxlabel = tk.Label(self.menu_left_upper, text='Base Wavelength 3:', fg = 'purple', relief = 'ridge')
        self.wavelen3boxlabel.grid(column=0, row=3)
        self.wavelen3box = Spinbox(self.menu_left_upper, from_=200, to=300, textvariable=self.wavelength3, width=7, format="%.2f", command=self.wavelenaction)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen3box.grid(column=1, row=3)
        self.wavelength1 = self.wavelen1box.get() #read StringVar as String for passing to next function
        self.wavelength2 = self.wavelen2box.get()
        self.wavelength3 = self.wavelen3box.get()
        # X axis visible range
        self.xminlabel = tk.Label(self.menu_left_upper, text='Minimum Wavelength', relief = 'ridge')
        self.xminlabel.grid(column=0, row=4)
        self.xminentry = tk.Entry(self.menu_left_upper, width = 7)
        self.xminentry.grid(column=1, row=4)
        self.xminentry.insert(0, self.xmin)
        self.xminentry.bind('<Return>', self.Xscale_change)
        self.xmaxlabel = tk.Label(self.menu_left_upper, text='Maximum Wavelength', relief = 'ridge')
        self.xmaxlabel.grid(column=0, row=5)
        self.xmaxentry = tk.Entry(self.menu_left_upper, width = 7)
        self.xmaxentry.grid(column=1, row=5)
        self.xmaxentry.insert(0, self.xmax)
        self.xmaxentry.bind('<Return>', self.Xscale_change)
        # rescale Y buttons
        self.button_rescaleY = tk.Button(self.menu_left_upper, text='Rescale Y')
        self.button_rescaleY.grid(column=0, row=6)
        self.button_rescaleY.bind('<ButtonRelease-1>', self.RescaleY)
        self.button_fullscaleY = tk.Button(self.menu_left_upper, text='Fullscale Y')
        self.button_fullscaleY.grid(column=0, row=7)
        self.button_fullscaleY.bind('<ButtonRelease-1>', self.FullscaleY)
        # Display mode
        self.DisplayCode = 1
        self.modelabel = tk.Label(self.menu_left_upper, text='Display Mode switch', relief = 'ridge')
        self.modelabel.grid(column=0, row=8)
        self.button_DisplayMode = tk.Button(self.menu_left_upper, text='Spectrum', width=10) #will change text dynamically with use
        self.button_DisplayMode.grid(column=1, row=8)
        self.button_DisplayMode.bind('<ButtonRelease-1>', self.DisplayMode)
        # Time Series length
        self.timelimitlabel = tk.Label(self.menu_left_upper, text='Time series \rlength (s)', relief = 'ridge')
        self.timelimitlabel.grid(column=0, row=9)
        self.timelimitentry = tk.Entry(self.menu_left_upper, width = 7)
        self.timelimitentry.grid(column=1, row=9)
        self.timelimitentry.insert(0, self.timelimit)
        self.timelimitentry.bind('<Return>', self.TimeLimit_change)
                
        #lower menu (use Pack placement)
        self.PStext = Text(self.menu_left_lower, width =25, height = 15)
        #self.PStext = scrolledtext.ScrolledText(self.menu_left_lower, width =20, height = 15)
        self.PStext.insert(tk.END, "Some text here")
        self.PStext.pack()
        self.PSentrylabel = tk.Label(self.menu_left_lower, text='PS command:')
        self.PSentrylabel.pack(side='left')
        self.PSentry = tk.Entry(self.menu_left_lower, width='10')
        #will need: self.menu_left_lower.bind('<Return>', self.PSentry_return)
        self.PSentry.pack(side='right')

        
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
        self.status = tk.Label(self.status_frame, text="this is the status bar")
        self.status.pack(fill="both", expand=True)

#set locations of the major areas to the corners of the box
        self.menu_left.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.some_title_frame.grid(row=0, column=1, sticky="ew")
        self.canvas_area.grid(row=1, column=1, sticky="nsew") 
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
#my stuff ends here
#
        #create plot object and draw it with empty data
        # 'ax1' is ax"one" not a letter
        self.fig = plt.Figure()
        self.ax1 = self.fig.add_subplot(111)
        self.line, = self.ax1.plot([], [], lw=2, color='blue')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1)

#my settings for the axes. Get these from the spectrograph data
        self.ax1.set_ylim(0,100)  #use (self.ymin*0.8, self.ymax*1.1) or get 'max_intensity' from SeaBreeze for full scale
        self.ax1.set_xlim(200,300)  # get max and min from wavelengths reported (self.xmin, self.xmax)
        self.waveline1 = self.ax1.axvline(x=float(self.wavelen1box.get()), lw=2, color='red', alpha = 0.5)
        self.waveline2 = self.ax1.axvline(x=float(self.wavelen2box.get()), lw=2, color='green', alpha = 0.5)
        self.waveline3 = self.ax1.axvline(x=float(self.wavelen3box.get()), lw=2, color='purple', alpha = 0.5)
#end axis settings

    def on_click(self):
        '''the button is a start, pause and unpause button all in one
        this method sorts out which of those actions to take'''
        if self.ani is None:
            # animation is not running; start it
            return self.start()

        if self.running:
            # animation is running; pause it
            #self.ani.event_source.stop()
            self.ani.event_source.start() #for tests start under all conditions
            self.btn.config(text='Un-Pause')
        else:
            # animation is paused; unpause it
            self.ani.event_source.start()
            self.btn.config(text='Pause')
        self.running = not self.running

    def start(self):
        self.points = 50
        self.ani = animation.FuncAnimation(
            self.fig,
            self.update_graph,
            frames=self.points,
            interval=100,
            repeat=False)
        self.running = True
        self.btn.config(text='Pause')
        self.ani._start()
        print('started animation')

    def update_graph(self, i):
        print(self.DisplayCode)
        #if DisplayCode = 0 then do time series;  else do spectrum as below
        if self.DisplayCode == 0:
            xdata = []
            linedata = []
            bkgdata = []
            for zzz in range(self.timelimit):
                data = np.array(get_data()) # gets full data
                #data_line = np.array(data[1,5]) #6th item in second array; spec data will be only one array
                xdata.append(zzz/2)
                linedata.append(xxxxxxxxx) 
                linedata = [xdata, linedata]
                #print(linedata)
                self.line.set_data(linedata) # something like this
                
            pass
            #data = *get_data
            #get new self.data then pick values at selected wavelengths
            #self.lineindex = self.x.index(self.wavelength1)
            #self.bkgindex = self.x.index(self.wavelength2)
            #self.baseindex = self.x.index(self.wavelength3)
            #self.line.set_data(
        else:
            self.line.set_data(*get_data()) # update graph
            self.waveline1.set_xdata(float(self.wavelength1)) #update lines instead of full redraw
            self.waveline2.set_xdata(float(self.wavelength2))
            self.waveline3.set_xdata(float(self.wavelength3))
                
            if i >= self.points - 1:
                # code to limit the number of run times; could be left out
                self.btn.config(text='Start')
                self.running = False
                self.ani = None
            return self.line,

    def wavelenaction(self):
        self.wavelength1 = self.wavelen1box.get()
        self.wavelength2 = self.wavelen2box.get()
        self.wavelength3 = self.wavelen3box.get()
        #self.lineindex = self.x.index(self.wavelength1) #prepares for time series plotting
        #self.bkgindex = self.x.index(self.wavelength2)
        #self.baseindex = self.x.index(self.wavelength3) #remove comment once spectrograph attached

    def RescaleY(self, event):
        self.ymin = np.around(min(self.data), decimals=2)
        self.ymax = np.around(max(self.data), decimals=2)
        self.ax1.set_ylim(self.ymin*0.8, self.ymax*1.1)

    def FullscaleY(self, event):
        # does the max_intensity call need to be massaged to float?
        self.ax1.set_ylim(-10, spec.max_intensity())

    def DisplayMode(self, event):
        if self.DisplayCode == 1:  # handles change to time series
            self.DisplayCode = 0
            self.button_DisplayMode.configure(text='Time Series')
            self.ax1.set_ylim(0,100)  #use (self.ymin*0.8, self.ymax*1.1) or get 'max_intensity' from SeaBreeze for full scale
            self.ax1.set_xlim(-1, self.timelimit)
            # DisplayCode also in the update_graph def
        else:
            self.DisplayCode = 1  # handles change to spectrum
            self.button_DisplayMode.configure(text='Spectrum')
            self.ax1.set_ylim(0,100)  #use (self.ymin*0.8, self.ymax*1.1) or get 'max_intensity' from SeaBreeze for full scale
            self.ax1.set_xlim(200,300)  # get max and min from wavelengths reported (self.xmin, self.xmax)
        

    def Xscale_change(self, event):  #always do both xmin and xmax on change of either
        xmintemp = self.xminentry.get()
        xmaxtemp = self.xmaxentry.get()
        try:
            float(xmintemp)
            xmintemp = float(self.xminentry.get())
            float(xmaxtemp)
            xmaxtemp = float(self.xmaxentry.get())
            if (xmintemp < self.xmax) and (xmaxtemp > self.xmin) and (xmintemp >= self.xmin) and (xmaxtemp <= self.xmax):
                self.xmin = xmintemp
                self.xminentry.delete(0, 'end')
                self.xminentry.insert(0, self.xmin)  #set text in xmin box
                self.xmax = xmaxtemp
                self.xmaxentry.delete(0, 'end')
                self.xmaxentry.insert(0, self.xmax)  #set text in xmax box
                self.ax1.set_xlim(self.xmin, self.xmax)

            else:
                #msg = "Minimum wavelength must be greater than " + str(np.around(min(self.x), decimals=2)) + "nm and maximum smaller than " + str(np.around(max(self.x), decimals=2)) + ".  Also, max greater than min.  You entered: min = " + str(xmintemp) + " nm and max = " + str(xmaxtemp) + "."
                # remove comments once connected to spectrgraph
                self.xminentry.delete(0, 'end')
                self.xminentry.insert(0, self.xmin)  #reset original xmin in box
                self.xmaxentry.delete(0, 'end')
                self.xmaxentry.insert(0, self.xmax)  #reset original xmax in box
                #messagebox.showerror("Entry error", msg)
        except:
            self.xminentry.delete(0, 'end')
            self.xminentry.insert(0, self.xmin)  #reset original xmin in box
            self.xmaxentry.delete(0, 'end')
            self.xmaxentry.insert(0, self.xmax)  #reset original xmax in box

    def TimeLimit_change(self, event):
        timelimittemp = self.timelimitentry.get()
        try:
            float(timelimittemp)
            timelimittemp = float(self.timelimitentry.get())
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

def main():
    root = tk.Tk()
    app = App(root)
    app.pack()
    root.mainloop()

if __name__ == '__main__':
    main()
