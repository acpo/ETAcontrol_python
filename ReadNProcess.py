import csv
import numpy as np
import matplotlib.pyplot as plt
#import mplcursors
from matplotlib.backend_bases import MouseButton

atom_time = 3.86

data_line = np.genfromtxt('shorttest1line.txt', dtype='float', delimiter=",", comments='#')
data_bkg = np.genfromtxt('shorttest1bkg.txt', dtype='float', delimiter=",", comments='#')
data_base = np.genfromtxt('shorttest1base.txt', dtype='float', delimiter=",", comments='#')

if np.sum(data_line[0] - data_bkg[0]) == 0 and np.sum(data_line[0] - data_base[0]) == 0:
    print("time ok")
else:
    print("time mismatch")
    print("line vs bkg difference = ", np.sum(data_line[0] - data_bkg[0]))
    print("line vs base difference = ", np.sum(data_line[0] - data_base[0]))

def on_click(event):
    x, y = event.x, event.y
    if event.inaxes:
        ax = event.inaxes  # the axes instance
        print('data coords %f %f' % (event.xdata, event.ydata))

data_time = data_line[0]
line_minus_base = data_line[1] - data_base[1]
bkg_minus_base = data_bkg[1] - data_base[1]
incident_index1 = int(np.searchsorted(data_time, atom_time - 1.2, side='left'))
incident_index2 = int(np.searchsorted(data_time, atom_time - 0.05, side='left'))
line_incident = np.mean(line_minus_base[incident_index1 : incident_index2]) #need index values of the range 1 second before atomization
print(line_incident)
line_abs = np.log10(line_incident / line_minus_base)
bkg_incident = np.mean(bkg_minus_base[incident_index1 : incident_index2])
bkg_abs = np.log10(bkg_incident / bkg_minus_base)
line_abs_sub = line_abs - bkg_abs
#print(line_abs_sub)

#onscreen routine for picking integral points

integral = np.trapz(line_abs_sub[incident_index1 : incident_index2])
height = np.max(line_abs_sub[incident_index1 : incident_index2])
print("area = ", integral, "height = ", height)

fig, ax = plt.subplots()
ax.plot(data_time, line_abs_sub)
plt.connect('button_press_event', on_click)
plt.show()
