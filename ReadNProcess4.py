#import tkinter as tk
import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk



class MainWindow(tk.Frame):
    def __init__(self, master=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        tk.Label(text = "Operations").grid(row=0,column=0)
        self.load_data_button = tk.Button(text = 'Load Data')
        self.load_data_button.grid(row=1,column=0)
        self.load_data_button.bind('<ButtonRelease-1>', self.Load_Data)
        self.atom_time_button = tk.Button(text = 'Select Atomization Time')
        self.atom_time_button.grid(row=2,column=0)
        self.atom_time_button.bind('<ButtonRelease-1>', self.Atom_Time)
        self.integrate_button = tk.Button(text = 'Integrate')
        self.integrate_button.grid(row=3,column=0)
        self.integrate_button.bind('<ButtonRelease-1>', self.Integrate)

        tk.Label(text = "Show Data").grid(row=0,column=1)
        self.show_rawdata_button = tk.Button(text = "Show raw data")
        self.show_rawdata_button.grid(row=1,column=1)
        self.show_rawdata_button.bind('<ButtonRelease-1>', self.Show_RawData)
        

    def Load_Data(self, event):
        filenames = tk.filedialog.askopenfilename(title = "Load ETA data", filetypes = [("Text file",".txt")], defaultextension='.txt', multiple=True)
        for file_name in filenames:
            path_ext = os.path.splitext(file_name)
            if 'line' in file_name:
                path_ext = os.path.splitext(file_name)
                self.linefile = path_ext[0]
                self.data_line = np.genfromtxt(str(self.linefile+path_ext[1]), dtype='float', delimiter=",", comments='#')
            if 'bkg' in file_name:
                path_ext = os.path.splitext(file_name)
                self.bkgfile = path_ext[0]
                data_bkg = np.genfromtxt(str(self.bkgfile+path_ext[1]), dtype='float', delimiter=",", comments='#')
            if 'base' in file_name:
                path_ext = os.path.splitext(file_name)
                self.basefile = path_ext[0]
                data_base = np.genfromtxt(str(self.basefile+path_ext[1]), dtype='float', delimiter=",", comments='#')

        #check that the time data matches in each trace
        if np.sum(self.data_line[0] - data_bkg[0]) == 0 and np.sum(self.data_line[0] - data_base[0]) == 0:
            print("time ok")
        else:
            print("time mismatch")
            print("line vs bkg difference = ", np.sum(self.data_line[0] - data_bkg[0]))
            print("line vs base difference = ", np.sum(self.data_line[0] - data_base[0]))

        # process data to remove baseline emission
        self.data_time = self.data_line[0]
        self.line_minus_base = self.data_line[1] - data_base[1]
        self.bkg_minus_base = data_bkg[1] - data_base[1]
        # end data processing

    #onscreen routine for picking incident emission points and calculating absorbance
    def Atom_Time(self,event):
        fig, ax = plt.subplots()
        ax.plot(self.data_time, self.line_minus_base)
        atomtime_selector = SpanSelector(ax, self.Get_Atom_Time,
                         "horizontal",
                         button=[1,3],
                         props=dict(alpha=0.5, facecolor="tab:blue"),
                         minspan = 0.3,
                         interactive=True)
        plt.show()

    def Get_Atom_Time(self, tmin, tmax):
        if tmin != tmax:
            x1index = int(np.searchsorted(self.data_time, tmin, side='left'))
            x2index = int(np.searchsorted(self.data_time, tmax, side='left'))
            line_incident = np.mean(self.line_minus_base[x1index : x2index])
            line_abs = np.log10(line_incident / self.line_minus_base)
            bkg_incident = np.mean(self.bkg_minus_base[x1index : x2index])
            bkg_abs = np.log10(bkg_incident / self.bkg_minus_base)
            self.line_abs_sub = line_abs - bkg_abs
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
            np.savetxt(lineabsfile, np.transpose([self.data_time, line_abs]), delimiter=',', header=lineabsheader, comments='')
            np.savetxt(bkgabsfile, np.transpose([self.data_time, bkg_abs]), delimiter=',', header=bkgabsheader, comments='')
            line_abs_subheader = "# File" + os.path.basename(lineabsfile) + " (minus) " + os.path.basename(bkgabsfile)
            np.savetxt(lineabssubfile, np.transpose([self.data_time, self.line_abs_sub]), delimiter=',', header=line_abs_subheader, comments='')
            #time.sleep(2)
            plt.close()
            
    #onscreen routine for picking integral points
    def Integrate(self, event):
        fig, ax = plt.subplots()
        ax.plot(self.data_time, self.line_abs_sub)
        plt.axhline(y=0, color='r', alpha=0.5)
        atomtime_selector = SpanSelector(ax, self.Get_Integral,
                         "horizontal",
                         button=[1,3],
                         props=dict(alpha=0.5, facecolor="tab:blue"),
                         minspan = 0.3,
                         interactive=True)
        plt.show()
        
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

    def Show_RawData(self, event):  #consider explicitly passing the data to avoid self.
        if self.data_line == []:
            tk.messagebox.showinfo(title="oops!", message="No data loaded yet.")

        else:
            fig, ax = plt.subplots()
            ax.plot(self.data_line[0], self.data_line[1])
            plt.show()



        
"""
build Tk interface
button for picking atomization time -- open trace and do rectangle selector in its own def
button for integration -- show subtracted absorbance and do rectangle selector in another def
button to show each trace as separate def
"""

def main():
    root = tk.Tk()
    app = MainWindow(root)
    app.grid()
    root.mainloop()

if __name__ == '__main__':
    main()
