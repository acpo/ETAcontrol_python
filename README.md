# ETAcontrol_python
Python control of an electrothermal atomizer system - programming fragments and studies

These are fragments of programming toward the goal of managing a tungsten electrothermal atomizer from a single Python GUI.  Control of hardware and data processing with user interaction are all parts of the goal.  An eventual solution will include:  
  * Serial communication (bidirectional) for hardware control  
  * Spectrometer interaction via SeaBreeze  
  * GUI that shows experiment conditions  
  * Animated Matplotlib plot showing live spectrometer results  
  * Mouse pointer selection of data from Matplotlib figure  
 
## Lessons learned  
MatPlotLib is (not surprisingly) the slowest part of the program.  Real-time data display is the limiting factor for the minimum data acquisition speed.  
If I turn of refreshing the plot during the time-series acquisition, then data can be recorded near the hardware limit of the spectrometer.  For example, a Raspberry PI 3B was able to record data with a 7-ms integration time with correct timing.  
With real-time data displayed, the minimum time is very hardware, Python version, dependent and *also depends on plotting choices*.  An i5-9500 running Windows 10 was the test system.  Real-time plotting with lines yielded minimum stable integration times of 25 ms (Python 3.6.8) and 22 ms (Python 3.9.10) using the same Matplotlib library.  Hooray for progress, but beware of the speed limitations of older Python versions.  A Raspberry Pi 3B achieved a minimum stable integration time of about 65 ms and an older Windows 10 PC achieved about 40 ms.  The hardware influence is very clear.  There may be a RAM influence, too, but I haven't had time to fully explore that variable.  
Plotting choices within Matplotlib can affect results, too.  The plotting speed slowest to fastest is:  line (lw=1), circle ('o'), point ('.'), and pixel (',').  Again, not a surprise since calculating a line inevitably is more resource intensive.  Plotting pixel may make the real-time result difficult to see.  However, using point or pixel I was able to achieve a 15-ms integration time while plotting three trends at the same time on the test system.  
Another plotting choice to achieve faster integration times is to use the Matplotlib `markevery` option in the line definition.  On long results (e.g., total time between 30 and 90 seconds) the integration time may show doubling sporadically or continuously after about 10 seconds.  I assume that this is a memory issue.  Using `markevery=2` plots everyother point, and so on.  It seems to actually reduce the number of items that Matplotlib is managing, so it can help to avoid the doubling effect.  

