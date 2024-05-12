from piotimer import Piotimer as Timer
from time import sleep, sleep_ms, ticks_ms, ticks_diff
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, PWM
from fifo import Fifo
import utime
import array
import time
import network
import socket
import urequests as requests
import ujson
import ssd1306
import math
from umqtt.simple import MQTTClient
import mip
import framebuf

#LEDS
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Constants for OLED display
oled_width = 128
oled_height = 64
pixel = 8
border_width = 1


# Initialize I2C interface for OLED
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)  # Check your pin assignments

# Initialize SSD1306 OLED display
oled = SSD1306_I2C(oled_width, oled_height, i2c)


#Create a framebuffer for drawing
buffer = bytearray((oled_width * oled_height) // pixel)
fb = framebuf.FrameBuffer(buffer, oled_width, oled_height, framebuf.MONO_HLSB)

def draw_pixel(fb, x, y, border_width, oled_width, oled_height):
    if x < border_width or x >= oled_width - border_width or y < border_width or y >= oled_height - border_width:
        fb.pixel(x, y, 1)

def draw_border(fb, border_width, oled_width, oled_height):
    fb.rect(0, 0, oled_width - 1, oled_height - 1, 1)  

# Draw pixels with border
for y in range(oled_height):
    for x in range(oled_width):
        draw_pixel(fb, x, y, border_width, oled_width, oled_height)

# Draw border
draw_border(fb, border_width, oled_width, oled_height)





# Network Credentials (Replace with your actual credentials)
SSID = "SmartIotMQTT"
PASSWORD = "SmartIot"
BROKER_IP = "192.168.1.254"
CLIENT_ID = ""  # Unique ID for your device

counter_1=0
max_limits = 5



sensor = ADC(26)
sw0 = Pin(9, Pin.IN, Pin.PULL_UP)

#class Encoder to handle rotation and button interrupts
class Encoder:
    def __init__(self, outA_pin, outB_pin, switch_pin):
        self.outA = Pin(outA_pin, Pin.IN, Pin.PULL_UP)  # Pin CLK of encoder
        self.outB = Pin(outB_pin, Pin.IN, Pin.PULL_UP)  # Pin DT of encoder
        self.switch = Pin(switch_pin, Pin.IN, Pin.PULL_UP)  # inbuilt switch on the rotary encoder, ACTIVE LOW
        self.option = 1
        self.page = 0  # 0: select option, 1: HR only, 2: Offline, 3: Online, 4: History
        self.outA.irq(trigger=Pin.IRQ_FALLING, handler=self.encoder_irq)
        self.switch.irq(trigger=Pin.IRQ_FALLING, handler=self.button_irq)

    # interrupt handler function (IRQ) for CLK and DT pins
    def encoder_irq(self, pin):  # handle rotation in page 0 ONLY
        if self.page == 0:
            if self.outB.value():
                self.option = (self.option % 4) + 1  # Decrement the option when turning clockwise
                Page.Menu(self.option)
            else:
                self.option = (self.option - 2) % 4 + 1  # Increment the option when turning counterclockwise
                Page.Menu(self.option)



    # interrupt handler function (IRQ) for SW (switch) pin
    def button_irq(self, pin):
        global measuring
        global sw0
        global goBack
        sleep_ms(20)  # debounce time
        if not self.switch():
            if self.page == 0:
                self.page = self.option
                Page.Option(self.option)
                sw0.irq(trigger=Pin.IRQ_FALLING, handler=sw0Irq)
            else:
                self.page = 0
                sw0.irq(trigger=Pin.IRQ_FALLING, handler=None)
                measuring = False
                goBack = True #returns user to Menu option if Rotary Encoder is clicked when inside option 1,2,3 or 4


#sw_0 interrpt handler to start a new measurement
def sw0Irq(pin):
    global startMeasure
    sleep_ms(20)
    if not sw0():
       startMeasure = True
       # print('inside sw0Irq')
                

                
###########################
##Code for welcome text####
###########################
def greet_txt():
    oled.fill(0)  
    fb.fill(0)  # Clear the framebuffer
    text1 = "Welcome To"
    text2 = "Group 5's"
    text3 = "Pie Watch"
    text4 = "Project"
    x1 = (oled_width - pixel * len(text1)) // 2
    y1 = (oled_height - pixel) // 2 - 3 * pixel  # Adjusted y-coordinate
    x2 = (oled_width - pixel * len(text2)) // 2
    y2 = (oled_height - pixel) // 2 - pixel  # Adjusted y-coordinate
    x3 = (oled_width - pixel * len(text3)) // 2
    y3 = (oled_height - pixel) // 2 + pixel  # Adjusted y-coordinate
    x4 = (oled_width - pixel * len(text4)) // 2
    y4 = (oled_height - pixel) // 2 + 3 * pixel  # Adjusted y-coordinate
    fb.text(text1, x1, y1, 1)  
    fb.text(text2, x2, y2, 1)
    fb.text(text3, x3, y3, 1)  
    fb.text(text4, x4, y4, 1)
    draw_border(fb, 1, 128, 64)
    oled.blit(fb, 0, 0)
    oled.show()
    utime.sleep_ms(3750)
    
def waiting():
    oled.fill(0)  
    fb.fill(0) 
    text1 = "Wait for"
    text2 = "The Menu "
    text3 = "To Display"
    x1 = (oled_width - pixel * len(text1)) // 2
    y1 = (oled_height - pixel) // 2 - 3 * pixel  # Adjusted y-coordinate
    x2 = (oled_width - pixel * len(text2)) // 2
    y2 = (oled_height - pixel) // 2 - pixel  # Adjusted y-coordinate
    x3 = (oled_width - pixel * len(text3)) // 2
    y3 = (oled_height - pixel) // 2 + pixel  # Adjusted y-coordinate
    fb.text(text1, x1, y1, 1)  
    fb.text(text2, x2, y2, 1)
    fb.text(text3, x3, y3, 1)  
    draw_border(fb, 1, 128, 64)
    oled.blit(fb, 0, 0)
    oled.show()
    utime.sleep_ms(2000)    


# Function to connect to WLAN
def connect_wlan():
  # Connecting to the group WLAN
  wlan = network.WLAN(network.STA_IF)
  wlan.active(True)
  wlan.connect(SSID, PASSWORD)

  # Attempt to connect once per second
  while not wlan.isconnected():
    print("Connecting... ")
    sleep(1)

  # Print the IP address of the Pico
  print("Connection successful. Pico IP:", wlan.ifconfig()[0])





# Main program
connect_wlan()

def connect_mqtt():
  mqtt_client = MQTTClient(CLIENT_ID, BROKER_IP)
  mqtt_client.connect(clean_session=True)
  return mqtt_client


# Main program
if __name__ == "__main__":
  # Connect to WLAN
  connect_wlan()

  # Connect to MQTT
  try:
    mqtt_client = connect_mqtt()
  except Exception as e:
    print(f"Failed to connect to MQTT: {e}")


                                                       ###################
#------------------------------------------------------##HISTORY STORAGE##---------------
                                                       ###################
def store_measurement(measurement):
    try:
        # Write the new measurement data directly to the file in write mode ("w")
        with open("History_data.txt", "w") as file:
            file.write(measurement + "\n")  # Write the new measurement data

        print("Data saved successfully.")
        
        # Print contents of the file
        print("Contents of History_data.txt:")
        with open("History_data.txt", "r") as file:
            print(file.read())

    except Exception as e:
        print(f"Error occurred while saving data: {e}")


#class Program to execute offline and online mode
class Program:

    
    def OfflineAnalysis():
        oled.fill(0)
        oled.text('Analysing...', 0, 5)
        oled.show()
        
        tmp = 0
        oled.text('Analysing...', 0, 5)
        oled.show()
        
        tmp = 0
        meanRR = sum(intervals) // 20
        meanHR = 60000 // meanRR
        for i in intervals:
            tmp += (i - meanRR)**2
        sdnn = int(math.sqrt(tmp / 19))	#int(math.sqrt(tmp / (len(intervals) - 1)))
        tmp = 0
        for i in range(19):	# 19 = len(intervals) - 1
            tmp += (intervals[i+1] - intervals[i])**2
        rmssd = int(math.sqrt(tmp / 19))	#int(math.sqrt(tmp / (len(intervals) - 1)))
        
        oled.fill(0)
        oled.text('HRV Analysis: ',10,0)
        oled.text('meanPPI: '+str(meanRR),0, 15)
        oled.text('MeanHR: '+str(meanHR)+' bpm',0, 27)
        oled.text('SDNN: '+str(sdnn),0, 39)
        oled.text('RMSSD: '+str(rmssd),0, 51)
        oled.show()
        
        message = {
            "mean_ppi" : meanRR,
            "mean_hr" : meanHR,
            "sdnn" : sdnn,
            "rmssd" : rmssd,
        }
        
        
        topic = "Group_5/Analysis"
        mqtt_client.publish(topic, ujson.dumps(message))
        
        
 
#---------------------------------------------------------__ONLINE_ANALYSIS__----
        
    
    def OnlineAnalysis():  
        APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a" 
        CLIENT_ID = "3pjgjdmamlj759te85icf0lucv" 
        CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef" 
        TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token" 

        response = requests.post( 
            url = TOKEN_URL, data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID), 
            headers = {'Content-Type':'application/x-www-form-urlencoded'}, auth = (CLIENT_ID, CLIENT_SECRET)) 
        response = response.json() #Parse JSON response into a python dictionary
        access_token = response["access_token"] #Parse access token out of the response dictionary 
                   
        oled.fill(0)
        oled.text('Analysing...', 0, 5)
        oled.show()
        
        data_set = {
            "type": "RRI",
            "data": intervals,
            "analysis": {
            "type": "readiness"}
            }
        
        # Make the readiness analysis with the given data 
        response = requests.post( url = "https://analysis.kubioscloud.com/v2/analytics/analyze", 
            headers = { "Authorization": "Bearer {}".format(access_token), 
            #use access token to access your KubiosCloud analysis session 
            "X-Api-Key": APIKEY }, 
            json = data_set) #dataset will be automatically converted to JSON by the urequests library 
        response = response.json() 
        #Print out the SNS and PNS values on the OLED screen
 #------print(response)
        meanRR = int(response['analysis']['mean_rr_ms'])
        meanHR = int(response['analysis']['mean_hr_bpm'])
        sdnn = int(response['analysis']['sdnn_ms'])
        rmssd = int(response['analysis']['rmssd_ms'])
        sns_index = response['analysis']['sns_index']
        pns_index = response['analysis']['pns_index']
        time_stamp = response['analysis']['create_timestamp']
        oled.fill(0)
        oled.text('meanPPI: ' + str(meanRR), 0, 9)
        oled.text('MeanHR: ' + str(meanHR) + ' bpm', 0, 18)
        oled.text('SDNN: ' + str(sdnn), 0, 27)
        oled.text('RMSSD: ' + str(rmssd), 0, 36)
        oled.text('SNS: ' + str(sns_index), 0, 45)
        oled.text('PNS: ' + str(pns_index), 0, 54)
        oled.text('Time: ' + str(time_stamp), 0, 63)
        oled.show()

        Saved_text_datas = f"Time:{time_stamp},MeanPPI:{meanRR},MeanHR:{meanHR}bpm,SDNN:{sdnn},RMSSD:{rmssd},SNS:{sns_index},PNS:{pns_index}"
        store_measurement(Saved_text_datas)


#--------------------------------------------------Class Page for displaying current OLED page and contents
class Page:
    
    def Menu(option):
        oled.fill(0)
        oled.text('Select a mode:',10,0)
        if option == 1:
            oled.fill_rect(0,14,128,10,1)
            oled.text('Measure HR',0,15,0)
            oled.text('Basic HRV ',0,30)
            oled.text('Kubios ',0,45)
            oled.text('History', 0,60)
        elif option == 2:
            oled.fill_rect(0,29,128,10,1)
            oled.text('Measure HR',0,15)
            oled.text('Basic HRV ',0,30,0)
            oled.text('Kubios ',0,45)
            oled.text('History', 0,60)
        elif option == 3:
            oled.fill_rect(0,44,128,10,1)
            oled.text('Measure HR',0,15)
            oled.text('Basic HRV ',0,30)
            oled.text('Kubios ',0,45,0)
            oled.text('History', 0,60)
        elif option == 4:
            oled.fill_rect(0,49,128,10,1)  
            oled.text('Measure HR',0,15)
            oled.text('Basic HRV ',0,30)
            oled.text('Kubios ',0,45)
            oled.text('History',0,50,0)  
        oled.show()


    

    def Option(option):
        if option == 1: #modified by chedel to access History menu option displays were globally removed and specified only to option 1,2,3
            oled.fill(0)
            oled.text('Press SW_0', 0, 5)
            oled.text('to start',0,15)
            oled.show()            
        if option == 2: #modified by chedel to access History menu option displays were globally removed and specified only to option 1,2,3
            oled.fill(0)
            oled.text('Press SW_0', 0, 5)
            oled.text('to start',0,15)
            oled.show()            
        if option == 3:	#online mode 
            # Connecting to the group WLAN
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(SSID, PASSWORD)
            # below runs the same display as option 1 and option 2
            oled.fill(0)
            oled.text('Press SW_0', 0, 5)
            oled.text('to start',0,15)
            oled.show()                                                                   #####################
        if option == 4:  #_______________________________________________________________ ## HISTORY DISPLAY ##
            oled.fill(0)                                                                  #####################
            try:
                with open("History_data.txt", "r") as file:
                    lines = file.readlines()

                # Initialize variables to store data
                data = {"Time": "", "MeanPPI": "", "MeanHR": "", "SDNN": "", "RMSSD": "", "SNS": "", "PNS": ""}

                # Parse each line and extract data (handle leading/trailing spaces and special case for Time)
                for line in lines:
                    # Remove leading/trailing spaces from the entire line
                    line = line.strip()

                    # Split the line using commas, allowing extra spaces
                    parts = line.split(",")
                    for part in parts:
                        # Handle Time data point specifically (assuming no colon)
                        if part.startswith("Time"):
                            time_data = part[len("Time"):].strip()
                            time_parts = time_data.split("T")
                            data["Time"] = time_parts[0]
                            data["Time"] = part[len("Time"):].strip() # Extract value after "Time"
                            oled.text(time_parts[1], 0, 9) 
                            continue  # Skip to next part after handling Time

                        try:
                            # Attempt to split with colon, handle potential errors
                            key, value = part.strip().split(":")
                            data[key] = value  # Update data dictionary only if valid
                        except ValueError:  # If split fails due to extra data points
                            pass  # Skip to next part

                # Display the data on the OLED screen (use formatting for numeric values)
                oled.text('Time' + str(data.get("Time", "")), 0, 0)
                oled.text('meanPPI:' + str(data.get("MeanPPI","")), 0, 18)   
                oled.text('MeanHR:' + str(data.get("MeanHR","")) + ' bpm', 0, 27)   
                oled.text('SDNN:' + str(data.get("SDNN","")), 0, 36)   
                oled.text('RMSSD:' + str(data.get("RMSSD","")), 0, 45)   
                oled.text('SNS:' + str(data.get("SNS","")), 0, 54)   
                oled.text('PNS:' + str(data.get("PNS","")), 0, 63)   
                oled.show()

            except Exception as e:
                oled.fill(0)
                oled.text('Error reading data', 0, 54)
                oled.show()
            
#function to draw hr pulse graphic and bpm
lastPosY = 0
def drawOled(dv, minv, maxv, bpm):
    global lastPosY
    oled.scroll(-1,0) # Scroll left 1 pixel
    if dv > maxv:
        dv = maxv
    elif dv < minv:
        dv = minv
    newPosY = 64 - 32 * (dv - minv) // valRange
    oled.line(125, lastPosY, 125, newPosY, 1)
    lastPosY = newPosY
    oled.fill_rect(0,0,128,32,0)
    oled.text('Measuring...', 10, 5)
    oled.text('%d BPM' % bpm, 10, 20)
    oled.show()

#----------------------------------------------------GLOBAL_VARIABLESETC.--------------------------#

greet_txt()
waiting()
rot = Encoder(10,11,12)
startMeasure = False
measuring = False
goBack = True
dlist = []
last_led_toggle_time = time.ticks_ms()

while True:
    if goBack:	#check if go back from executing program to selecting mode screen
        goBack = False
        Page.Menu(rot.option)
        
    if startMeasure:	#check if sw_0 has been pressed to start new measurement
        #print('startMeasure = True***')
        startMeasure = False
        if rot.option == 1 or rot.option == 2 or rot.option == 3: #changed by Chedel to access the History
            measuring = True #changed by Chedel to access the History
            
         # Toggle LED to indicate measurement start
        led_onboard.value(1)
        time.sleep(0.1)
        led_onboard.value(0)
        beat = False	#mark if found beat or not
        beatTime = [0 , 0]	#store timestamps of 2 consecutive beats
        bpm = 0	#storind calculated bpm
        minv = 65535	#init minv to prepare for calculating threshold
        maxv = 0		#init maxv to prepare for calculating threshold
        sampleCount = 0	#count samples to recalculate threshold
        sumIbi = 0	#sum of amount of ibi to calculate mean value of ibi
        beatCount = 0	#number of beats to calculate a average ibi
        intervals = []
        intervalsCount = 0				
       
        #get correct minv maxv first
        for a in range(200):
            dv = sensor.read_u16()
            sleep_ms(4)
            dlist.append(dv)
            dlist = dlist[-5:]
            #find max and min value to display beat line on oled
            if dv > maxv:
                maxv = dv
            if dv < minv:
                minv = dv
        #calculation of threshold
        thres_H = (minv + maxv * 3) // 4   # 3/4
        thres_L = (minv + maxv) // 2      # 1/2
        valRange = maxv - minv
       
    if measuring:	#check if program is executing a measurement
        #print('measuring = ', measuring)
        if ticks_diff(ticks_ms(), last_led_toggle_time) >= 1000:  # Blink every 1000 ms (1 second)
          led_onboard.value(not led_onboard.value())  # Toggle LED state
          last_led_toggle_time = ticks_ms()  # Update the last LED toggle time
        if intervalsCount < 20:
            dlist.append(sensor.read_u16())
            sleep_ms(4)                
            dlist = dlist[-5:]
            dv = sum(dlist) // 5
            sampleCount += 1	#count number of dv
            #find max and min value to display beat line on oled
            if dv > maxv:
                maxv = dv
            if dv < minv:
                minv = dv
            #detect a beat: a beat is found when a very first dv > threshold
            #print('line 229')
            if dv > thres_H and not beat:
                beat = True
                dt = ticks_ms()	#get a timestamp when a beat is found
                beatTime.append(dt)	#add new timestamp to a queue
                beatTime = beatTime[-2:]	#limit the timestamp list to 2 items
                #calculate inter-beat-interval ibi: calculate a timespan between 2 consecutive beats
                ibi = ticks_diff(beatTime[-1], beatTime[-2])
                #print(ibi)
                #calculate mean ibi then calculate bpm
                if 250 < ibi < 1500:	#limit range of bpm from 40-240 bpm
                    sumIbi += ibi
                    beatCount += 1
                    #calculate mean ibi after beatCount
                    if beatCount == 1:	#modify this value to get better result
                        beatCount = 0
                        avrIbi = sumIbi #modify this value to get better result
                        bpm = 60000 // avrIbi
                        intervals.append(avrIbi)
                        intervalsCount += 1
                        sumIbi = 0
            #print('line 250')
            if dv < thres_L and beat:	#ignor all dv < threshold
                beat = False
            #update data and draw beat line to oled after every calculated mean dv
            drawOled(dv, minv, maxv, bpm)
            #recalculate threshold after sampleCount
            #print('line 256')
            if sampleCount > 200:
                sampleCount = 0                 
                thres_H = (minv + maxv * 3) // 4   # 3/4
                thres_L = (minv + maxv) // 2      # 1/2
                valRange = maxv - minv
                minv = 65535
                maxv = 0
                #print(thres_L, thres_H)
            #sleep_ms(2)
            if rot.option == 1:
                intervalsCount = 0	#reset intervalsCount to get infinite measurement in option 1 -- this makes the HRV BPM run endlessly!! 
            
        else:	#if intervalsCount = 20 then starts to go with offline or online mode - option 0,1,2,and 3 stems from one condition and its the "if measuring"
            #print(intervals)
            measuring = False
            if rot.option == 2:	#offline analysis
                Program.OfflineAnalysis()
            if rot.option == 3:	#online analysis
                Program.OnlineAnalysis()


