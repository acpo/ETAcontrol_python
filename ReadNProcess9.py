## Changed read to accommodate data pairs with linefeeds
# works with .csv data converted from .spc files!
# Need to make our data saves the same format for compatibility
## 03/2023 Changed integration to include dx.
#  Previously integrals gave each trapeziod a width of 1.0,
#  therefore area depended on integration time.  Now using average dx within selected integral range.
# Added ability to open already processed data.
## 04/2023 Added ability to open prior temperature data.
## 02/2024 Added ability to swap data columns in temperature calculation
#  to address probe setups that swap current and voltage positions.
## 03/2024 Minimum integration interval decreased to 0.04 s to accommodate
#  fast pulse methods.
## 10/2024 Method to set a new Zero Time point.
## 11/2024 Button to extract 3rd channel for PMT-based data records
#  reduced Minimum integration interval to accommodate PMT pulse data.
## 11/2024 added button to do time shift of multi-channel data (PMT data)
## 01/2025 added integration outputs to support peak-to-peak estimates of noise

import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as lines
from matplotlib.widgets import SpanSelector
from matplotlib.widgets import Cursor 

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
    import tkinter.filedialog   #seems to be necessary to be explicit about this dialog

class MainWindow(tk.Frame):
    def __init__(self, master=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        tk.Label(text = "Operations", font='bold', fg='blue').grid(row=0,column=0)
        self.load_data_button = tk.Button(text = 'Load Spec Data')
        self.load_data_button.grid(row=1,column=0)
        self.load_data_button.bind('<ButtonRelease-1>', self.Load_SpecData)
        self.calc_abs_button = tk.Button(text = 'Select Incident Emission')
        self.calc_abs_button.grid(row=2,column=0)
        self.calc_abs_button.bind('<ButtonRelease-1>', self.Incident_Abs)
        self.integrate_button = tk.Button(text = 'Integrate')
        self.integrate_button.grid(row=3,column=0)
        self.integrate_button.bind('<ButtonRelease-1>', self.Integrate)

        tk.Label(text = "Show Data", font='bold', fg='blue').grid(row=0,column=1)
        self.show_rawdata_button = tk.Button(text = "Show raw data")
        self.show_rawdata_button.grid(row=1,column=1)
        self.show_rawdata_button.bind('<ButtonRelease-1>', self.Show_RawData)
        self.show_absdata_button = tk.Button(text = "Show absorbance data")
        self.show_absdata_button.grid(row=2,column=1)
        self.show_absdata_button.bind('<ButtonRelease-1>', self.Show_AbsData)
        self.show_absdata_button = tk.Button(text = "Show subtracted absorbance data")
        self.show_absdata_button.grid(row=3,column=1)
        self.show_absdata_button.bind('<ButtonRelease-1>', self.Show_AbsSubData)

        tk.Label(text = "Loaded Data", font='bold', fg='blue').grid(row=4,column=0,columnspan=2)
        tk.Label(text = "Line file:").grid(row=5,column=0, sticky='w')
        tk.Label(text = "Background file:").grid(row=6,column=0, sticky='w')
        tk.Label(text = "Baseline file:").grid(row=7,column=0, sticky='w')
        self.LineLabel = tk.Label(text = "")
        self.LineLabel.grid(row=5,column=1, sticky='w')
        self.BkgLabel = tk.Label(text = "")
        self.BkgLabel.grid(row=6,column=1, sticky='w')
        self.BaseLabel = tk.Label(text = "")
        self.BaseLabel.grid(row=7,column=1, sticky='w')

        self.LoadSubData_button = tk.Button(text = "Load subtracted absorbance data")
        self.LoadSubData_button.grid(row=8,column=1)
        self.LoadSubData_button.bind('<ButtonRelease-1>', self.Load_SubData)

        self.SetTimeZero_button = tk.Button(text = "Set Time Zero")
        self.SetTimeZero_button.grid(row=9,column=1)
        self.SetTimeZero_button.bind('<ButtonRelease-1>', self.Set_TimeZero)
        self.SetTimeZero_label = tk.Label(text = "Time shift only on \nsubtracted absorbance")
        self.SetTimeZero_label.grid(row=9,column=0)

        self.Extract3rdChannel_button = tk.Button(text = "Extract 3rd Channel")
        self.Extract3rdChannel_button.grid(row=10,column=1)
        self.Extract3rdChannel_button.bind('<ButtonRelease-1>', self.Extract_Third_Channel)        

# Temperature data section
        tk.Label(text = "Temperature data", font='bold', fg='blue').grid(row=20,column=0,columnspan=2)
        self.load_scopetempdata_button = tk.Button(text = 'Load Scope Data')
        self.load_scopetempdata_button.grid(row=21,column=0)
        self.load_scopetempdata_button.bind('<ButtonRelease-1>', self.Load_ScopeData)
        self.show_scopetempdata_button = tk.Button(text = 'Show scope data')
        self.show_scopetempdata_button.grid(row=21,column=1)
        self.show_scopetempdata_button.bind('<ButtonRelease-1>', self.Show_ScopeData)
        self.calc_temperature_button = tk.Button(text = 'Calculate Temperature')
        self.calc_temperature_button.grid(row=22,column=0)
        self.calc_temperature_button.bind('<ButtonRelease-1>', self.Calc_Temperature)
        self.show_temperature_button = tk.Button(text = 'Show Temperature')
        self.show_temperature_button.grid(row=22,column=1)
        self.show_temperature_button.bind('<ButtonRelease-1>', self.Show_Temperature)

        tk.Label(text = "Loaded Data", font='bold', fg='blue').grid(row=23,column=0,columnspan=2)
        tk.Label(text = "Temperature file:").grid(row=24,column=0, sticky='w')
        self.TemperatureLabel = tk.Label(text = "")
        self.TemperatureLabel.grid(row=24,column=1, sticky='w')
        self.LoadTempData_button = tk.Button(text = "Load temperature data")
        self.LoadTempData_button.grid(row=25,column=1)
        self.LoadTempData_button.bind('<ButtonRelease-1>', self.Load_TempData)


# addresses oscilloscope channel swaps, calls def Swap_TempColumns
        self.SwapTempLabel = tk.Label(text = "Swap columns if scope data was reversed")
        self.SwapTempLabel.grid(row=26, column=1)
        self.SwapTempColumns_button = tk.Button(text = "Swap current and voltage columns")
        self.SwapTempColumns_button.grid(row=27, column=1)
        self.SwapTempColumns_button.bind('<ButtonRelease-1>', self.Swap_TempColumns)
# --end    

        self.ShiftPMTfile_button = tk.Button(text = 'Time Shift Whole File')
        self.ShiftPMTfile_button.grid(row=28,column=0)
        self.ShiftPMTfile_button.bind('<ButtonRelease-1>', self.ShiftWholeFile)
        tk.Label(text = "will Load file and allow zero shifting").grid(row=28,column=1)


# functions for processing optical data
    def Load_SpecData(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load ETA data", filetypes = [("Text file",".txt"),("CSV file",".csv")], defaultextension='.txt', multiple=True)
        if not filenames:
            pass  #exits on Cancel
        else:
            for file_name in filenames:
                path_ext = os.path.splitext(file_name)
                if 'line' in file_name:
                    path_ext = os.path.splitext(file_name)
                    self.linefile = path_ext[0]
                    self.data_line = np.genfromtxt(str(self.linefile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#')
                if 'bkg' in file_name:
                    path_ext = os.path.splitext(file_name)
                    self.bkgfile = path_ext[0]
                    self.data_bkg = np.genfromtxt(str(self.bkgfile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#')
                if 'base' in file_name:
                    path_ext = os.path.splitext(file_name)
                    self.basefile = path_ext[0]
                    self.data_base = np.genfromtxt(str(self.basefile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#')

    # need to modify this check for the data pair format
            #check that the time data matches in each trace
            #if np.sum(self.data_line[0] - self.data_bkg[0]) == 0 and np.sum(self.data_line[0] - self.data_base[0]) == 0:
            #    pass
            #    #print("time ok")
            #else:
                #print("time mismatch")
                #print("line vs bkg difference = ", np.sum(self.data_line[0] - self.data_bkg[0]))
                #print("line vs base difference = ", np.sum(self.data_line[0] - self.data_base[0]))
            #    tk.messagebox.showinfo(title="Something is wrong", message="line vs bkg time difference = " + str(np.sum(self.data_line[0] - self.data_bkg[0])))

            # process data to remove baseline emission
            self.data_time = self.data_line[0]
            self.line_minus_base = self.data_line[1] - self.data_base[1]
            self.bkg_minus_base = self.data_bkg[1] - self.data_base[1]
            # end data processing
            self.LineLabel.config(text = os.path.basename(self.linefile))
            self.BkgLabel.config(text = os.path.basename(self.bkgfile))
            self.BaseLabel.config(text = os.path.basename(self.basefile))

    #onscreen routine for picking incident emission points and calculating absorbance
    def Incident_Abs(self,event):
        fig, ax = plt.subplots()
        ax.plot(self.data_time, self.line_minus_base)
        plt.title("Select data just before atomization")
        atomtime_selector = SpanSelector(ax, self.Get_Incident_Abs,
                         "horizontal",
                         button=[1,3],
                         props=dict(alpha=0.5, facecolor="tab:blue"),
                         minspan = 0.3,  #must select more than 0.3 seconds to average
                         interactive=True)
        plt.show()

    def Get_Incident_Abs(self, tmin, tmax):
        if tmin != tmax:
            x1index = int(np.searchsorted(self.data_time, tmin, side='left'))
            x2index = int(np.searchsorted(self.data_time, tmax, side='left'))
            line_incident = np.mean(self.line_minus_base[x1index : x2index])
            self.line_abs = np.log10(line_incident / self.line_minus_base)
            bkg_incident = np.mean(self.bkg_minus_base[x1index : x2index])
            self.bkg_abs = np.log10(bkg_incident / self.bkg_minus_base)
            self.line_abs_sub = self.line_abs - self.bkg_abs
            output1 = str("Absorbance calculated based on \nincident emission averaged from " + str(np.around(tmin, 3)) + "to " + str(np.around(tmax,3)))
            output1 = str("\nNumber of values averaged = " + str(x2index - x1index))
            output1 += str("\nMean intensity = " + str(np.around(line_incident, 2)))
            tk.messagebox.showinfo(title="Results calculated", message=output1)
            # also save the processed files
            lineabsfile = str(self.linefile + "_abs.txt")  #consider changing to self.path_ext[1] for flexible extension use
            bkgabsfile = str(self.bkgfile + "_abs.txt")
            lineabssubfile = str(self.linefile + "_abs_sub.txt")
            lineabsheader = "# File " + os.path.basename(self.linefile) + " converted to absorbance with Incident = " + str(np.around(line_incident,2)) + "\n# Time (s), Absorbance"
            bkgabsheader = "# File " + os.path.basename(self.bkgfile) + " converted to absorbance with Incident = " + str(np.around(bkg_incident,2)) + "\n# Time (s), Absorbance"
            np.savetxt(lineabsfile, np.transpose([self.data_time, self.line_abs]), delimiter=',', newline='\n', header=lineabsheader, comments='')
            np.savetxt(bkgabsfile, np.transpose([self.data_time, self.bkg_abs]), delimiter=',', newline='\n', header=bkgabsheader, comments='')
            line_abs_subheader = "# File" + os.path.basename(lineabsfile) + " (minus) " + os.path.basename(bkgabsfile) + "\n# Time (s), Absorbance"
            np.savetxt(lineabssubfile, np.transpose([self.data_time, self.line_abs_sub]), delimiter=',', newline='\n', header=line_abs_subheader, comments='')
            #time.sleep(2)
            plt.close()
            
    #onscreen routine for picking integral points
    def Integrate(self, event):
        fig, ax = plt.subplots()
        ax.plot(self.data_time, self.line_abs_sub)
        plt.axhline(y=0, color='r', alpha=0.5)
        plt.title("Select data range to integrate")
        integral_selector = SpanSelector(ax, self.Get_Integral,
                         "horizontal",
                         button=[1,3],
                         props=dict(alpha=0.5, facecolor="tab:blue"),
                         minspan = 0.02, #must pick more than 0.02 second width
                         interactive=True)
        plt.show()

    #handler for the SpanSelector    
    def Get_Integral(self, tmin, tmax):
        if tmin != tmax:
            x1index = int(np.searchsorted(self.data_time, tmin, side='left'))
            x2index = int(np.searchsorted(self.data_time, tmax, side='left'))
            integral = np.trapz(self.line_abs_sub[x1index : x2index], dx = np.mean(np.diff(self.data_time[x1index : x2index])))
            height = np.max(self.line_abs_sub[x1index : x2index])
            output1 = str("area = " + str(np.around(integral, 4)) + "\nheight = " + str(np.around(height,4)))
            output1 += str("\nselected time range: " + str(np.around(tmin,3)) + "to " + str(np.around(tmax,3)))
            output1 += str("\ndata spacing (ms) = " + str(np.around(1000*np.mean(np.diff(self.data_time[x1index : x2index])),3)))
## new 2025-01 for peak-to-peak noise assessment
            minimum = np.min(self.line_abs_sub[x1index : x2index])
            avg_height = np.mean(self.line_abs_sub[x1index : x2index])
            output1 += str("\n" + "\nminimum: " + str(np.around(minimum, 4)))
            output1 += str("\naverage height: " + str(np.around(avg_height,4)))
## end new            
            tk.messagebox.showinfo(title="Integration Results", message=output1)
        plt.close()

# functions for displaying optical data
    def Show_RawData(self, event): 
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_line[0], self.data_line[1], label="line")
            ax.plot(self.data_bkg[0], self.data_bkg[1], label="background")
            ax.plot(self.data_base[0], self.data_base[1], label="baseline")
            ax.legend(loc=2)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Counts")
            plt.title("Spectrometer intensity data")
            plt.show(block = False)  # try to make non-blocking

        except:
            tk.messagebox.showinfo(title="oops!", message="No data loaded yet.")
            plt.close()

    def Show_AbsData(self, event):
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_time, self.bkg_abs, label="background")
            ax.plot(self.data_time, self.line_abs, label="line")
            plt.axhline(y=0, color='r', alpha=0.5)
            ax.legend(loc=2)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Absorbance")
            plt.title("Absorbance data (baseline corrected)")
            plt.show(block = False)  # try to make non-blocking

        except:
            tk.messagebox.showinfo(title="oops!", message="Absorbance not calculated yet.\nUse 'Select Incident Emission'.")
            plt.close()

    def Show_AbsSubData(self, event):
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_time, self.line_abs_sub, label="background corrected data")
            plt.axhline(y=0, color='r', alpha=0.5)
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Absorbance")
            plt.title("Background subtracted absorbance data")
            plt.show()

        except:
            tk.messagebox.showinfo(title="oops!", message="Absorbance not calculated yet.\nUse 'Select Incident Emission'.")
            plt.close()


# processing of old data
    def Load_SubData(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load already processed data", filetypes = [("Text file",".txt"),("CSV file",".csv")], defaultextension='.txt', multiple=False)
        if not filenames:
            pass  #exits on Cancel
        else:
            path_ext = os.path.splitext(filenames)
            self.subdatafile = path_ext[0]  #full path with filename NO extension
            subdata = np.genfromtxt(str(self.subdatafile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#', skip_header=0)
            self.data_time = subdata[0]
            self.line_abs_sub = subdata[1]
            # clean up GUI labels
            self.LineLabel.config(text = os.path.basename(self.subdatafile))
            self.BkgLabel.config(text = "none")
            self.BaseLabel.config(text = "none")
# --- end

# Shift time axis to new zero point  
    def Set_TimeZero(self, event):
        fig, ax = plt.subplots()
        ax.plot(self.data_time, self.line_abs_sub)
        lims = ax.get_xlim()
        plt.axhline(y=0, color='r', alpha=0.5)
        plt.title("Select time position to set to zero")
        plt.text(0.05, 0.9, "Press Enter to confirm selection", color='red', transform=ax.transAxes)
        cursor = Cursor(ax, color='green', linewidth=1) 
        plt.waitforbuttonpress()
        selected_point = np.asarray(plt.ginput(n=-1, timeout=-1, show_clicks=True))  # allows infinite clicks

        self.data_time = self.data_time - selected_point[-1][0]  # takes 'x' of the last click
        shiftedsubfile = str(self.subdatafile + "_shift.txt")
        shiftheader = "# File " + os.path.basename(self.subdatafile) + " shifted by time = " + str(np.around(selected_point[0][0],2)) + "\n# Time (s), Absorbance"
        
        print(shiftheader)
        np.savetxt(shiftedsubfile, np.transpose([self.data_time, self.line_abs_sub]), delimiter=',', newline='\n', header=shiftheader, comments='')
        print(shiftheader)
        
        ax.set_xlim(lims)
        ax.plot(self.data_time, self.line_abs_sub, label="time shifted data")
        ax.figure.canvas.draw()
# --- end

# Extract Third Channel for PMT-based data
    def Extract_Third_Channel(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load data", filetypes = [("CSV file","*.csv"), ("Text file","*.txt")], defaultextension='.csv', multiple=False)
        if not filenames:
            pass  #exits on Cancel
        else:
            path_ext = os.path.splitext(filenames)
            self.extrdatafile = path_ext[0]  #full path with filename NO extension
            subdata = np.genfromtxt(str(self.extrdatafile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#', skip_header=3)
            self.data_time = subdata[0]
            self.line = subdata[3]
            # clean up GUI labels
            self.LineLabel.config(text = os.path.basename(self.extrdatafile))
            self.BkgLabel.config(text = "none")
            self.BaseLabel.config(text = "none")
            # process single-channel light data

        fig, ax = plt.subplots()
        self.line_minus_base = self.line * -1 # fix the polarity of the PMT signal
        ax.plot(self.data_time, self.line_minus_base)
        plt.title("Select data just before atomization")
        atomtime_selector = SpanSelector(ax, self.Get_Incident_Abs_Single_Channel,
                         "horizontal",
                         button=[1,3],
                         props=dict(alpha=0.5, facecolor="tab:blue"),
                         minspan = 0.3,  #must select more than 0.3 seconds to average
                         interactive=True)
        plt.show()
        self.line_abs_sub = self.line_abs # make names compatible with other processing steps
        
    def Get_Incident_Abs_Single_Channel(self, tmin, tmax):
        if tmin != tmax:
            x1index = int(np.searchsorted(self.data_time, tmin, side='left'))
            x2index = int(np.searchsorted(self.data_time, tmax, side='left'))
            line_incident = np.mean(self.line_minus_base[x1index : x2index])
            self.line_abs = np.log10(line_incident / self.line_minus_base)
            
            output1 = str("Absorbance calculated based on \nincident emission averaged from " + str(np.around(tmin, 3)) + "to " + str(np.around(tmax,3)))
            output1 = str("\nNumber of values averaged = " + str(x2index - x1index))
            output1 += str("\nMean intensity = " + str(np.around(line_incident, 2)))
            tk.messagebox.showinfo(title="Results calculated", message=output1)
            # also save the processed files
            lineabsfile = str(self.extrdatafile + "_abs.txt")  #consider changing to self.path_ext[1] for flexible extension use
            lineabsheader = "# File " + os.path.basename(self.extrdatafile) + " converted to absorbance with Incident = " + str(np.around(line_incident,2)) + "\n# Time (s), Absorbance"
            np.savetxt(lineabsfile, np.transpose([self.data_time, self.line_abs]), delimiter=',', newline='\n', header=lineabsheader, comments='')
            plt.close()


            
# --- end

# functions for temperature data
    def Load_ScopeData(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load Oscilloscope data", filetypes = [("CSV file",".csv"), ("Text file",".txt")], defaultextension='.csv', multiple=False)
        if not filenames:
            pass  #exits on Cancel
        else:
            path_ext = os.path.splitext(filenames)
            self.scopefile = path_ext[0]  #full path with filename NO extension
            scopedata = np.genfromtxt(str(self.scopefile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#', skip_header=3)
            self.data_voltage = scopedata[0], scopedata[1]
            self.data_current = scopedata[0], scopedata[2]

    def Calc_Temperature(self, event):
        temp = self.data_voltage[1] / self.data_current[1]
        temp = temp ** 0.8226  #coefficient for 15-volt filament
        temp = (temp * 2759.45) - 51.7749 #coefficient for 15-volt filament
        # added to deal with 'nan' values  -- problem is due to small voltage offsets in the current probe
        temp[np.isnan(temp)] = 0
        # end added part
        self.temperature = self.data_voltage[0], temp
        #voltagefile = str(self.scopefile + "_voltage.txt")  #consider changing to self.path_ext[1] for flexible extension use
        #currentfile = str(self.scopefile + "_current.txt")
        temperaturefile = str(self.scopefile + "_temperature.txt")
        temperatureheader = "# processed from File " + os.path.basename(self.scopefile) + "using coefficients for 15-volt filament \n# Time (s), Temperature (K)" #do we add coeffient values to the header???
        np.savetxt(temperaturefile, np.transpose(self.temperature), delimiter=',', newline='\n', header=temperatureheader, comments='')
        
    def Show_ScopeData(self, event):
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_voltage[0], self.data_voltage[1], label="voltage")
            ax.plot(self.data_current[0], self.data_current[1], label="current")
            ax.legend(loc=2)
            plt.title(os.path.basename(self.scopefile))
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Current (A) or Voltage (V)")
            plt.show()

        except:
            tk.messagebox.showinfo(title="oops!", message="No data loaded yet.")
            plt.close()

    def Show_Temperature(self, event):
        try:
            fig, ax = plt.subplots()
            ax.plot(self.temperature[0], self.temperature[1], label="temperature")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Temperature (K)")
            plt.ylim(0, 4000)
            plt.title("Filament temperature (K) of " + os.path.basename(self.scopefile))
            plt.show()

        except:
            tk.messagebox.showinfo(title="oops!", message="Temperature not calculated yet.")
            plt.close()

# processing of old temperature data
    def Load_TempData(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load already processed data", filetypes = [("Text file",".txt"),("CSV file",".csv")], defaultextension='.txt', multiple=False)
        if not filenames:
            pass  #exits on Cancel
        else:
            path_ext = os.path.splitext(filenames)
            self.tempdatafile = path_ext[0]  #full path with filename NO extension
            temperaturedata = np.genfromtxt(str(self.tempdatafile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#', skip_header=0)
            self.temperature = temperaturedata[0], temperaturedata[1]
            # clean up GUI labels
            self.TemperatureLabel.config(text = os.path.basename(self.tempdatafile))
            self.scopefile = os.path.basename(self.tempdatafile)    # for compatibility with Show_Temperature
# --- end
# special def for fixing scope data in wrong order
    def Swap_TempColumns(self, event):
        try:
            temp_time = self.data_voltage[0]
            temp_current = self.data_voltage[1]
            temp_voltage = self.data_current[1]
            self.data_voltage = temp_time, temp_voltage
            self.data_current = temp_time, temp_current
        except:
            tk.messagebox.showinfo(title="oops!", message="Has data been loaded yet?")
# --- end

# special def for time shifting a whole file (for PMT data sets)
    def ShiftWholeFile(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load Oscilloscope data", filetypes = [("CSV file",".csv"), ("Text file",".txt")], defaultextension='.csv', multiple=False)
        if not filenames:
            pass  #exits on Cancel
        else:
            path_ext = os.path.splitext(filenames)
            self.scopefile = path_ext[0]  #full path with filename NO extension
            scopedata = np.genfromtxt(str(self.scopefile+path_ext[1]), unpack = True, dtype='float', delimiter=",", comments='#', skip_header=3)
        
        fig, ax = plt.subplots()
        ax.plot(scopedata[0], scopedata[2], label="voltage")
        ax.plot(scopedata[0], scopedata[1], label="current")
        ax.legend(loc=2)
        plt.title(os.path.basename(self.scopefile))
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Current (A) or Voltage (V)")

        lims = ax.get_xlim()
        plt.axhline(y=0, color='r', alpha=0.5)
        plt.title("Select time position to set to zero")
        plt.text(0.05, 0.8, "Press Enter to confirm selection", color='red', transform=ax.transAxes)
        cursor = Cursor(ax, color='green', linewidth=1) 
        plt.waitforbuttonpress()
        selected_point = np.asarray(plt.ginput(n=-1, timeout=-1, show_clicks=True))  # allows infinite clicks

        scopedata[0] = scopedata[0] - selected_point[-1][0]  # takes 'x' of the last click
        shiftedscopefile = str(self.scopefile + "_shift.csv")
        scopeheader = np.genfromtxt(str(self.scopefile+path_ext[1]), delimiter=',', max_rows=2, dtype=str) 
        ## need to get correct header from original file
        shiftheader = "# File " + os.path.basename(self.scopefile) + " shifted by time = " + str(np.around(selected_point[0][0],2)) + "\n" + str(scopeheader).lstrip('[[').rstrip(']]')
        np.savetxt(shiftedscopefile, np.transpose(scopedata), delimiter=',', newline='\n', header=shiftheader, comments='')
        
        ax.set_xlim(lims)
        ax.plot(scopedata[0], scopedata[1], label="time shifted data", alpha = 0.5)
        ax.figure.canvas.draw()
# --- end


def main():
    root = tk.Tk()
    app = MainWindow(root)
    app.grid()
    root.mainloop()

if __name__ == '__main__':
    main()
