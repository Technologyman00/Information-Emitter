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
intense = settings_data.get("brightness")

pixel_pin = board.D18 #GPIO to use

num_pixels = settings_data.get("num_LEDs") # Number of LEDs in the strip

ORDER = neopixel.GRB #Typical Order of Pixels

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=intense, auto_write=False, pixel_order=ORDER)

cond = threading.Condition()
notified = [False]

command = settings_data.get("startup_command")
arg = settings_data.get("startup_arg")
red = settings_data.get("startup_color")[0]
green = settings_data.get("startup_color")[1]
blue = settings_data.get("startup_color")[2]
TeamColor1 = settings_data.get("Team_Color1")
TeamColor2 = settings_data.get("Team_Color2")
delay = settings_data.get("startup_delay")

print(delay)

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

table = NetworkTables.getTable('InformationEmitter')

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

def GetColors():
    global red #global allows it to set the outside scope variables
    global green
    global blue

    color = table.getNumberArray('Color', [0,0,0])

    red = int(abs(color[0]))
    green = int(abs(color[1]))
    blue = int(abs(color[2]))

def CheckDelay():
    global delay

    newdelay = abs(table.getNumber('Delay', delay))
    if(newdelay > 0):
        delay = newdelay
    

def SmartWait(delaytime_s):
    global command
    
    start = datetime.now()
    current = datetime.now()
    difference = current - start
    while(difference.total_seconds() < delaytime_s):
        command = table.getNumber('Command', 0)
        if(command != 0):
            break
        current = datetime.now()
        difference = difference = current - start

ClearCommands(command, arg, settings_data.get("startup_color")) # put startup commands
table.putNumber('Delay', delay) # put default delay

while NetworkTables.isConnected():
        command = table.getNumber('Command', 0)
        if(command == 99): # Set Team Colors
            arg = abs(table.getNumber('Argument', arg))
            if(arg == 1):
                TeamColor1 = table.getNumberArray("Color")
            if(arg == 2):
                TeamColor2 = table.getNumberArray("Color")
            ClearCommands()
                
        if(command == 1): #Fill Color
            GetColors()
            ClearCommands()
            pixels.fill((red,green,blue))		
            pixels.show()
            

        if(command == 2): #Color Wipe
            GetColors()
            CheckDelay()
            ClearCommands()
            for i in range(0, num_pixels):
                pixels[i] = (red, green, blue)
                pixels.show()
                SmartWait(delay)
                if(command != 0):
                    break

        if(command == 3): # Rainbow
            CheckDelay()
            ClearCommands()
            while True:
                for j in range(255):
                    for i in range(num_pixels):
                        pixel_index = (i * 256 // num_pixels) + j
                        pixels[i] = wheel(pixel_index & 255)
                    pixels.show()
                    SmartWait(delay)
                    if(command != 0):
                        break
                if(command != 0):
                    break

        if(command == 4): # Team Color Cycle
            CheckDelay()
            arg = int(abs(table.getNumber('Argument', arg))) # Length of Section
            ClearCommands()
            firstcolor = True
            loc = 0
            while True:
                for j in range(arg):
                    for i in range(num_pixels):
                        if(firstcolor):
                            pixels[i] = (TeamColor1)
                        else:
                            pixels[i] = (TeamColor2)
                        loc = loc + 1
                        if(loc > arg+j):
                            firstcolor = False
                        if(loc > (2*arg)+j):
                            firstcolor = True
                        pixels.show()
                        SmartWait(delay)
                        if(command != 0):
                            break
                    if(command != 0):
                        break
                if(command != 0):
                        break
            
