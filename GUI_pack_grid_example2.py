# Animated Matplotlib inside a GUI
# This shows how to separate out getting the data from the GUI

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
from tkinter import scrolledtext
from tkinter import Spinbox
from tkinter import Text

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib import style
style.use("ggplot")
plt.rcParams['axes.facecolor']='#F8F8F8'
plt.rcParams['lines.color']='blue'

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
        #done example requirements

#my stuff starts here
        
        self.wavelength1 = tk.StringVar(self, 273.43)
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
        self.wavelen1boxlabel = tk.Label(self.menu_left_upper, text='Line Wavelength 1:', fg = 'red')
        self.wavelen1boxlabel.grid(column=0, row=1)

        self.wavelen1box = Spinbox(self.menu_left_upper, from_=200, to=300, textvariable=self.wavelength1, width=7, format="%.2f", command=self.wavelenaction)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen1box.grid(column=1, row=1)
        self.wavelen2boxlabel = tk.Label(self.menu_left_upper, text=' Bkg Wavelength 2:', fg = 'green')
        self.wavelen2boxlabel.grid(column=0, row=2)
        self.wavelen2box = Spinbox(self.menu_left_upper, from_=200, to=300, textvariable=self.wavelength2, width=7, format="%.2f", command=self.wavelenaction)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen2box.grid(column=1, row=2)
        self.wavelen3boxlabel = tk.Label(self.menu_left_upper, text='Base Wavelength 3:', fg = 'purple')
        self.wavelen3boxlabel.grid(column=0, row=3)
        self.wavelen3box = Spinbox(self.menu_left_upper, from_=200, to=300, textvariable=self.wavelength3, width=7, format="%.2f", command=self.wavelenaction)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen3box.grid(column=1, row=3)
        self.wavelength1 = self.wavelen1box.get() #read the spinboxes as strings for passing to next function
        self.wavelength2 = self.wavelen2box.get()
        self.wavelength3 = self.wavelen3box.get()
                
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
        
        self.btn = tk.Button(self.some_title_frame, text='Start', command=self.on_click)
        self.btn.pack(side=tk.RIGHT)


        
        #first two lines give a functioning empty box
        self.canvas_area = tk.Canvas(self, width=700, height=500, background="#ffffff")
        self.canvas_area.grid(row=1, column=1)
        
        
        #lower status bar
        self.status_frame = tk.Frame(self)
        self.status = tk.Label(self.status_frame, text="this is the status bar")
        self.status.pack(fill="both", expand=True)

        self.menu_left.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.some_title_frame.grid(row=0, column=1, sticky="ew")
        self.canvas_area.grid(row=1, column=1, sticky="nsew") 
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
#my stuff ends here


        self.fig = plt.Figure()
        self.ax1 = self.fig.add_subplot(111)
        self.line, = self.ax1.plot([], [], lw=2, color='blue')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1, column=1)

#my settings for the axes.
        self.ax1.set_ylim(0,100)
        self.ax1.set_xlim(200,300)
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
        

def main():
    root = tk.Tk()
    app = App(root)
    app.pack()
    root.mainloop()

if __name__ == '__main__':
    main()
