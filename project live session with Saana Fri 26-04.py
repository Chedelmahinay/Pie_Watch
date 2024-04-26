from machine import ADC
from fifo import Fifo
from piotimer import Piotimer


class isr_adc:
    def __init__(self, adc_pin_nr):
        self.av = ADC(adc_pin_nr) # sensor AD channel
        self.fifo = Fifo(500) # fifo where ISR will put samples #250Hz - 1s:250 , 2s:500
       
    
    def handler(self, tid):
        self.fifo.put(self.av.read_u16())#16 bits 
        
pin_nr = 26
sample_rate = 250
threshold_percentage = 0.15

prev_sample = 0
peak_found = False #1 or 0 true or false (Boolean variable)
current_peak_index = 0
first_peak_found = False #have not found first peak
index = 0
ms_in_minute = 60000
min_hr = 30
max_hr= 240
adc = isr_adc(pin_nr) #owns the fifo object adc.fifo.data, min(adc.fifo.data) , max(adc.fifo.data), mean (adc.fifo.data) sum()same structure for the whole array


tmr = Piotimer(mode = Piotimer.PERIODIC, freq = sample_rate, callback = adc.handler) 

while True:
    # to read:
    if adc.fifo.has_data():
        #read a new sample
        value = adc.fifo.get()
        
        #calculate threshold
        min_value = min(adc.fifo.data)
        max_value = max(adc.fifo.data)
        amplitude = max_value - min_value
        threshold = max_value - threshold_percentage * amplitude
        
        ####print(value,threshold)
        
        #check if we are above the threshold
        if value > threshold:
            #start finding the peak
            if prev_sample > value:
                #we have found a peak
                if not peak_found:
                    #peak is not foud
                    #save the peak (using an index to see the time difference btw 2 peaks)
                    if first_peak_found:
                        ppi_samples = index - 1 #calculate bbi in number of 
                        ppi_ms = ppi_samples * 4 #1 sample is 4mssamples, calculate ppi in 
                        hr = round(ms_in_minute/ppi_ms) #bpm 1 min 60s = 60000ms
                            
                        #check of the resulting heart rate is within limits
                        if hr >= min_hr and hr <= max_hr:
                            print(ppi_samples, ppi_ms, hr)
                    else:
                        first_peak_found = True
                        
                    peak_found = True #(above threshold peak true - dont save it goes back below the threshold, find peak agai)
                    index = -1 #once we find the peak we will index the first one to 0 before the next eound
        
        #Here we are below the threshold
        else:
            peak_found = False
        
        prev_sample = value
        index += 1
                    
                    
                
            
        
        
        