#import tkinter as tk
import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as lines
from matplotlib.widgets import SpanSelector

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk



class MainWindow(tk.Frame):
    def __init__(self, master=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        tk.Label(text = "Operations", font='bold', fg='blue').grid(row=0,column=0)
        self.load_data_button = tk.Button(text = 'Load Data')
        self.load_data_button.grid(row=1,column=0)
        self.load_data_button.bind('<ButtonRelease-1>', self.Load_Data)
        self.atom_time_button = tk.Button(text = 'Select Incident Emission')
        self.atom_time_button.grid(row=2,column=0)
        self.atom_time_button.bind('<ButtonRelease-1>', self.Incident_Abs)
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
        self.show_absdata_button.bind('<ButtonRelease-1>', self.Show_AbsData)

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

    def Load_Data(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load ETA data", filetypes = [("Text file",".txt"),("CSV file",".csv")], defaultextension='.txt', multiple=True)
        for file_name in filenames:
            path_ext = os.path.splitext(file_name)
            if 'line' in file_name:
                path_ext = os.path.splitext(file_name)
                self.linefile = path_ext[0]
                self.data_line = np.genfromtxt(str(self.linefile+path_ext[1]), dtype='float', delimiter=",", comments='#')
            if 'bkg' in file_name:
                path_ext = os.path.splitext(file_name)
                self.bkgfile = path_ext[0]
                self.data_bkg = np.genfromtxt(str(self.bkgfile+path_ext[1]), dtype='float', delimiter=",", comments='#')
            if 'base' in file_name:
                path_ext = os.path.splitext(file_name)
                self.basefile = path_ext[0]
                self.data_base = np.genfromtxt(str(self.basefile+path_ext[1]), dtype='float', delimiter=",", comments='#')

        #check that the time data matches in each trace
        if np.sum(self.data_line[0] - self.data_bkg[0]) == 0 and np.sum(self.data_line[0] - self.data_base[0]) == 0:
            pass
            #print("time ok")
        else:
            #print("time mismatch")
            #print("line vs bkg difference = ", np.sum(self.data_line[0] - self.data_bkg[0]))
            #print("line vs base difference = ", np.sum(self.data_line[0] - self.data_base[0]))
            tk.messagebox.showinfo(title="Something is wrong", message="line vs bkg time difference = " + str(np.sum(self.data_line[0] - self.data_bkg[0])))

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
            lineabssubfile = str(lineabsfile + "_sub.txt")
            lineabsheader = "# File " + os.path.basename(self.linefile) + " converted to absorbance with Incident = " + str(np.around(line_incident,2))
            bkgabsheader = "# File " + os.path.basename(self.bkgfile) + " converted to absorbance with Incident = " + str(np.around(bkg_incident,2))
            np.savetxt(lineabsfile, np.transpose([self.data_time, self.line_abs]), delimiter=',', header=lineabsheader, comments='')
            np.savetxt(bkgabsfile, np.transpose([self.data_time, self.bkg_abs]), delimiter=',', header=bkgabsheader, comments='')
            line_abs_subheader = "# File" + os.path.basename(lineabsfile) + " (minus) " + os.path.basename(bkgabsfile)
            np.savetxt(lineabssubfile, np.transpose([self.data_time, self.line_abs_sub]), delimiter=',', header=line_abs_subheader, comments='')
            #time.sleep(2)
            plt.close()
            
    #onscreen routine for picking integral points
    def Integrate(self, event):
        fig, ax = plt.subplots()
        ax.plot(self.data_time, self.line_abs_sub)
        plt.axhline(y=0, color='r', alpha=0.5)
        plt.title("Select data range to integrate")
        atomtime_selector = SpanSelector(ax, self.Get_Integral,
                         "horizontal",
                         button=[1,3],
                         props=dict(alpha=0.5, facecolor="tab:blue"),
                         minspan = 0.1, #must pick more than 0.1 second width
                         interactive=True)
        plt.show()

    #handler for the SpanSelector    
    def Get_Integral(self, tmin, tmax):
        if tmin != tmax:
            x1index = int(np.searchsorted(self.data_time, tmin, side='left'))
            x2index = int(np.searchsorted(self.data_time, tmax, side='left'))
            integral = np.trapz(self.line_abs_sub[x1index : x2index])
            height = np.max(self.line_abs_sub[x1index : x2index])
            output1 = str("area = " + str(np.around(integral, 4)) + "\nheight = " + str(np.around(height,4)))
            output1 += str("\nselected time range: " + str(np.around(tmin,3)) + "to " + str(np.around(tmax,3)))
            output1 += str("\ndata spacing (ms) = " + str(np.around(1000*np.mean(np.diff(self.data_time[x1index : x2index])),3)))
            tk.messagebox.showinfo(title="Integration Results", message=output1)
        plt.close()

    def Show_RawData(self, event): 
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_line[0], self.data_line[1], label="line")
            ax.plot(self.data_bkg[0], self.data_bkg[1], label="background")
            ax.plot(self.data_base[0], self.data_base[1], label="baseline")
            ax.legend()
            plt.show()

        except:
            tk.messagebox.showinfo(title="oops!", message="No data loaded yet.")
            plt.close()

    def Show_AbsData(self, event):
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_time, self.line_abs, label="line")
            ax.plot(self.data_time, self.bkg_abs, label="background")
            ax.legend()
            plt.show()

        except:
            tk.messagebox.showinfo(title="oops!", message="Absorbance not calculated yet.\nUse 'Select Incident Emission'.")
            plt.close()

    def Show_AbsSubData(self, event):
        try:
            fig, ax = plt.subplots()
            ax.plot(self.data_time, self.line_abs_sub, label="background corrected data")
            ax.legend()
            plt.show()

        except:
            tk.messagebox.showinfo(title="oops!", message="Absorbance not calculated yet.\nUse 'Select Incident Emission'.")
            plt.close()

def main():
    root = tk.Tk()
    app = MainWindow(root)
    app.grid()
    root.mainloop()

if __name__ == '__main__':
    main()
