from machine import ADC
from fifo import Fifo
from piotimer import Piotimer

class isr_adc:
    def __init__(self, adc_pin_nr):
        self.av = ADC(adc_pin_nr) # sensor AD channel
        self.fifo = Fifo(500) # fifo where ISR will put samples


    def handler(self, tid):
        self.fifo.put(self.av.read_u16())


pin_nr = 26
sample_rate = 250
threshold_percentage = 0.15

#this is the peak and it will be updating with the current sample  
prev_sample = 0
peak_found = False
current_peak_index = 0
previous_peak_index = 0
index = 0
ms_in_minute = 60000
min_hr = 30
max_hr = 240

adc = isr_adc(pin_nr)
tmr = Piotimer(mode = Piotimer.PERIODIC, freq = sample_rate, callback = adc.handler)

while True: # to read:
    
    if adc.fifo.has_data():
        value = adc.fifo.get()
        
        #Calculate Threshhold
        min_value = min(adc.fifo.data)
        max_value = max(adc.fifo.data)
        amplitude = max_value - min_value
        threshold = max_value - threshold_percentage * amplitude
               
        if value > threshold: #this checks if we are above the threshold. 
            #start finding the peak
            if prev_sample > value:
                # we have found a peak
                if not peak_found:
                    #save the peak
                    current_peak_index = index - 1 
                    ppi_samples = index - 1 #calculate ppi in number of samples
                    ppi_ms = ppi_samples * 4 #1 sample is 4ms
                    hr = round(ms_in_minute / ppi_ms) # calculates heart rate in BPM # if bpm is 1 min ->60s -> 60,000ms, know how many beats is in 60,000 ms. if values are small we are not detecting all the peaks. you need to fine tune it
                    
                    
                    if hr >= min_hr and hr <= max_hr: #check if the resulting heart rate value is within limits
                        print(ppi_samples, ppi_ms, hr)
                        
                    peak_found = True
                    index = -1 # this is negative one so that index will be zero before next round
                    
        
        else: # here we are below the teshold
            peak_found = False
        
        prev_sample = value                
        index += 1 
            
            
# the print shows an inaccurate but a good way starter to get the pulse. use plotter to get the visual.
# it is inaccurate because its not yet the mean of the pulses.
# you can use the numbers and go to excel charts to see the actual display of how it would look like.

# print(value, threshold)
        
# it should be divided in to functions or methods if you have long codes.
        
# when reading the peak to peak information, you can use the average of several peak to peak values thats
# measured within 5 seconds. afer reading 5 seconds you can discard the first PPI value cos its not new anymore,
# and then adjust by moving the window of the PPI samples then get its average. keep continuing till u get an average of 5.

# This algorythim uses a treshold, calculates ppi, ms and heart rate.

# group can adjust the pie watch to already read the button even when it is in the startup menu

# Goal is to make the calculations into OOP so that it would be shorter in the code. this is because its too long and needs to 
