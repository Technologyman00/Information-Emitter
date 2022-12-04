import threading
import sys
import time
from networktables import NetworkTables
import logging
import time
import board
import neopixel
from datetime import datetime
import json

#logging.basicConfig(level=logging.DEBUG)

settings_file = open('InformationEmitter_Settings.json')
settings_data = json.load(settings_file)
settings_file.close()

team_number = settings_data.get("Team_Number")

# Loads the Pin from JSON File
# Loads the Numbert of LEDs from the JSON File
# Loads the Brightness from the JSON File
# Loads the Pixel Order from the JSON File
# Sets up the Pixel Array and Settings for the Pixels

ORDER = getattr(neopixel, settings_data.get("led_order"))
num_pixels = settings_data.get("num_LEDs")

gamma = settings_data.get("gamma")

pixels = neopixel.NeoPixel(getattr(board, "D"+settings_data.get("Pin")), num_pixels, brightness=settings_data.get("brightness"), auto_write=False, pixel_order=ORDER)

cond = threading.Condition()
notified = [False]

# load the rest of the important user settings
command = settings_data.get("startup_command")
arg = settings_data.get("startup_arg")

color = settings_data.get("startup_color")

TeamColor1 = settings_data.get("Team_Color1")
TeamColor2 = settings_data.get("Team_Color2")
delay = settings_data.get("startup_delay")

pixels.fill((0,0,0)) # Have RAM Reflect the Colors of the Pixels being currently off

def connectionListener(connected, info):
    print(info, '; Connected=%s' % connected)
    with cond:
        notified[0] = True
        cond.notify()

# TO FIX
# TO FIX
# TO FIX
# TO FIX
# TO FIX
NetworkTables.initialize(server='192.168.1.155') # Need to add Static IP based on Team Number
NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)
# TO FIX
# TO FIX
# TO FIX
# TO FIX

with cond:
    print("Waiting")
    if not notified[0]:
        cond.wait()

# Insert your processing code here
print("Connected!")

def valueChanged(table, key, value, isNew):
    global command
    global delay
    global color
    global arg
    
    if(key == 'Command'):
        command = int(value)
    if(key == 'Argument'):
        arg = int(value)
    if(key == 'Color'):
        color = value
    if(key == 'Delay'):
        if(value > 0):
            delay = abs(value)

table = NetworkTables.getTable('InformationEmitter')
table.addEntryListener(valueChanged)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)

def ClearCommands(command = 0, arg = 0, color = [0,0,0]):
    table.putNumber('Command', command)
    table.putNumber('Argument', arg)
    table.putNumberArray('Color', color)

# Just split out as its reused constantly
def CheckDelay():
    global delay

    newdelay = abs(table.getNumber('Delay', delay))
    if(newdelay > 0):
        delay = newdelay
    
# This delay is used instead of the time.sleep() as we want the LEDs to be as responsive as possible without locking the thread to pausing
def SmartWait(delaytime_s):
    global command
    
    start = datetime.now()
    current = datetime.now()
    difference = current - start
    while(difference.total_seconds() < delaytime_s):
        #command = table.getNumber('Command', 0)
        if(command != 0):
            break
        current = datetime.now()
        difference = difference = current - start

def gamma_enc(color):
    global gamma

    if(gamma != 1):
        encode_red = int(abs(((color[0]/255)**(gamma)) * 255))
        encode_green = int(abs(((color[1]/255)**(gamma)) * 255))
        encode_blue = int(abs(((color[2]/255)**(gamma)) * 255))

        color = (encode_red, encode_green, encode_blue)
    else:
        color = (int(abs(color[0])), int(abs(color[1])), int(abs(color[2])))

    return color

ClearCommands(command, arg, settings_data.get("startup_color")) # put startup commands
table.putNumber('Delay', delay) # put default delay

while NetworkTables.isConnected():
        #command = table.getNumber('Command', 0)
        if(command == 99): # Set Team Colors
            #arg = abs(table.getNumber('Argument', arg))
            if(arg == 1):
                TeamColor1 = table.getNumberArray("Color", [0,0,0])
            if(arg == 2):
                TeamColor2 = table.getNumberArray("Color", [0,0,0])
            ClearCommands()
                
        if(command == 1): #Fill Color
            #color = table.getNumberArray('Color', [0,0,0])
            ClearCommands()
            pixels.fill(gamma_enc(color))		
            pixels.show()
            

        if(command == 2): #Color Wipe
            #color = table.getNumberArray('Color', [0,0,0])
            #CheckDelay()
            ClearCommands()
            for i in range(0, num_pixels):
                pixels[i] = gamma_enc(color)
                pixels.show()
                SmartWait(delay)
                if(command != 0):
                    break

        if(command == 3): # Rainbow
            #CheckDelay()
            ClearCommands()
            while True:
                for j in range(255):
                    for i in range(num_pixels):
                        pixel_index = (i * 256 // num_pixels) + j
                        pixels[i] = gamma_enc(wheel(pixel_index & 255))
                    pixels.show()
                    SmartWait(delay)
                    if(command != 0):
                        break
                if(command != 0):
                    break

        if(command == 4): # Team Color Cycle
            #CheckDelay()
            #arg = int(abs(table.getNumber('Argument', arg))) # Length of Section
            ClearCommands()
            count = 0
            while True:
                for i in range(num_pixels):
                        if(count <= arg):
                            pixels[i] = gamma_enc(TeamColor1)
                        else:
                            pixels[i] = gamma_enc(TeamColor2)
                        count += 1

                        if(count > (2*arg)):
                            count = 0
                                            
                        if(command != 0):
                            break
                pixels.show()
                SmartWait(delay)
                if(command != 0):
                    break
