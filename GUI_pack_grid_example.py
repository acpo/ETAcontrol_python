import tkinter as tk
from tkinter import scrolledtext
from tkinter import Spinbox
from tkinter import Text

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

#for testing purposes
wavelength1 = 275.12
wavelength2 = 278.35
#end testing

class Example():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ETAAS Spectroscopy Control")
        #super(Example, self).__init__() # suggestion from internet
        # menu left
        self.menu_left = tk.Frame(self.root, width=150, bg="#ababab")
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
        self.wavelen1boxlabel = tk.Label(self.menu_left_upper, text='Wavelength 1:')
        self.wavelen1boxlabel.grid(column=0, row=1)
        self.wavelen1box = Spinbox(self.menu_left_upper, textvariable=wavelength1, from_=200, to=300, width=7)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen1box.grid(column=1, row=1)
        self.wavelen2boxlabel = tk.Label(self.menu_left_upper, text='Wavelength 2:')
        self.wavelen2boxlabel.grid(column=0, row=2)
        self.wavelen2box = Spinbox(self.menu_left_upper, textvariable=wavelength2, from_=200, to=300, width=7)#ADD values=(wavelengths) to have only valid wavelengths displayed
        self.wavelen2box.grid(column=1, row=2)
        
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
        
        # right display area
        self.some_title_frame = tk.Frame(self.root, bg="#dfdfdf")
        self.some_title = tk.Label(self.some_title_frame, text="Spectrograph Window", bg="#dfdfdf")
        self.some_title.pack()

        self.canvas_area = tk.Canvas(self.root, width=700, height=500, background="#ffffff")
        #self.canvas_area = FigureCanvasTkAgg(fig,self) #matplotlib figure goes here
        self.canvas_area.grid(row=1, column=1)

        #lower status bar
        self.status_frame = tk.Frame(self.root)
        self.status = tk.Label(self.status_frame, text="this is the status bar")
        self.status.pack(fill="both", expand=True)

        self.menu_left.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.some_title_frame.grid(row=0, column=1, sticky="ew")
        self.canvas_area.grid(row=1, column=1, sticky="nsew") 
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.root.mainloop()

Example()
