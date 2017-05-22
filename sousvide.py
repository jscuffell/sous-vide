import os
import glob
import time
from bottle import Bottle, run, request, response, post, get
import re, json
import RPi.GPIO as GPIO
from lcdtools import LCDDisplay
#import Adafruit_CharLCD as LCD
import threading
import collections

# This script defines the sous vide class, which can interact with the REST API.

class TemperatureSensor:
    # Define each temperature sensor in an object. The thermometer deals with all of them at once.
    def __init__(self, device_address):
        print "Address is " + device_address
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = self.base_dir + device_address
        self.device_file = self.device_folder + '/w1_slave'
        self.device_address = device_address

    def __read_temp_raw(self):
            f = open(self.device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines

    def __read_temp(self):
        lines = self.__read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.__read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return round(temp_c, 1)

    def getTemperature(self):
        return self.__read_temp()

class Thermometer:
    def __init__(self, sensor_addresses = []):
        self.sensors = {} 
        for address in sensor_addresses:
            self.addSensor(address)
    
    def addSensor(self,device_address):
        newSensor = TemperatureSensor(device_address)
        self.sensors[device_address] = newSensor
        
    def getSensors(self):
        return self.sensors 

    def getSensorByIndex(self, index):
        index = int(index)
        return self.sensors[self.sensors.keys()[index]]
    
    def getTemperature(self, withSummary = 0):
        returnVal = {}
        # Get all the temperatures from the sensors
        for address in self.sensors.keys():
           returnVal[address] = self.sensors[address].getTemperature() 
        if withSummary > 0:
            summary = {}
            summary['mean'] = sum(returnVal.values())/len(returnVal)
            summary['min'] = min(returnVal.values())
            summary['max'] = max(returnVal.values())
            summary['range'] = summary['max'] - summary['min']
            returnVal['summary'] = summary
        return returnVal

    def getAverageTemperature(self):
        return self.getTemperature(1)['summary']['mean']
        


class Thermostat:
    
    def __init__(self):
        # Start thermostat at a default temperature. Say - 10 degrees celsius.
        self.thermTemp = float(10)
        therm = threading.Thread(target=self.thermostatAdjust)
        therm.daemon=True
        therm.start()

    def setThermostat(self, temp):
        if (temp > 90):
            print "High temperature set and that is not allowed"
            raise ValueError
        self.thermTemp = float(temp)
        # This is picked up by the thermostatAdjust function
        return self.thermTemp

    def getThermostat(self):
        return self.thermTemp

    def thermostatAdjust(self):
        global thermometer
        global heater
        tempReadings = collections.deque([], 3)
        j = 1 # this is so we don't do anything for the first 3 iterations, so that my collection can fill up
        while 1==1:
            readings = thermometer.getTemperature(1) # with summary
            thermostat = self.getThermostat()
            currentTemp = readings['summary']['mean']
            tempReadings.append([int(time.time()), currentTemp])
            delta = currentTemp - thermostat
            print str(delta) + "is delta"
            ''' if j > 3: # as long as we are three seconds into this
                # We will implement a 15 second rule. If, at the current rate, we will reach our temperature in 8 seconds, then slow it down.
                print json.dumps(list(tempReadings))
                dy_dx = (tempReadings[2][1] - tempReadings[0][1])/(tempReadings[2][0]-tempReadings[0][0])
                print "DY_DX = " + str(dy_dx)
    
                if ((currentTemp + 15*dy_dx ) > thermostat): # if we will overshoot thermostatic temperature in the next 15 secnods at this rate:
                    print "Slowing things down"
                    # Equally, if the temperature is still less than 2 degrees from correct, then dnon't just turn the bloody thing off
                    if (delta < -2):
                        heater.setPower(heater.getPower()-1)
                    elif (delta > -2) and (delta < -0.7):
                        heater.setPower(1)
                    else:
                        heater.setPower(0)
           
                else:
                    delta = currentTemp - thermostat
                    if (dy_dx < -0.005): # if the temperature is coming down rather than up
                        if (delta < -5):
                            heater.setPower(3)
                        elif (delta < -2):
                            heater.setPower(2)
                        elif (delta < -0.5 ):
                            heater.setPower(2)
                        elif (delta > -0.5):
                            heater.setPower(0)
                    else:
                        if (delta < -5):
                            heater.setPower(3)
                        elif (delta < -2):
                            heater.setPower(2)
                        elif (delta <= -0.5 ):
                            heater.setPower(1)
                        elif (delta > -0.5):
                            heater.setPower(0)
            else:
                j = j+1
                if (delta < 0):
                    heater.setPower(3)
                else:
                    heater.setPower(0)
            # As we approach the right temperature, start to pulse the element, so it is on less frequently
        #    if (delta < -5):
        #        heater.on()
        #    elif (delta < -2):
        #        heater.pulse(2,1)
        #    elif (delta < -0.5):
        #        heater.pulse(1,2)
        #    elif (delta < 0):
        #        heater.off()
        #    elif abs(delta) <= 0.5:
        #        heater.off()
        #    else:
        #        heater.off()  '''


            print "Heater state is " + str(heater.getState())
            # let's do this a little simpler.
            if (delta > 0.5) and (heater.getState() == 1):
                heater.setPower(0)
            elif (delta < -0.5) and (heater.getState() == 0):
                heater.setPower(3) 
            time.sleep(1)
        return
    
class GPIOTools:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    class GPIOSwitch:

        def __init__(self, GPIOPin, inv = 0):
            self.pin = GPIOPin
            GPIO.setup(self.pin, GPIO.OUT)
            self.inv = inv
            self.off() # Always start as off

        def on(self):
            if self.inv == 0:
                GPIO.output(self.pin, GPIO.HIGH)
            else:
                GPIO.output(self.pin, GPIO.LOW)
            self.state = 1
            return self.state

        def off(self):
            if self.inv == 0:
                GPIO.output(self.pin, GPIO.LOW)
            else:
                GPIO.output(self.pin, GPIO.HIGH)
            self.state = 0
            return self.state

        def getState(self):
            return self.state

        def setState(self, newState):
            if (newState == 1):
                self.on()
            else:
                self.off()
            return self.state

        def toggle(self):
            self.setState(self.state-1%2)


    
def LCDDaemon(lcd):
    i = 0
    while 1==1:
        print str(i) +","+json.dumps(thermometer.getTemperature(1))
        lcd.setMessage("Temp " + str(thermometer.getAverageTemperature()) + " C" + "\nThermostat " + str(int(thermostat.getThermostat())) + " C")
        time.sleep(1)
        i = i+1
    return 

class Heater:
       # A class to keep track of all the heaters. In this case we will have one or two, each with their specific BCM number
    def __init__(self, gpioPorts = []):
        self.gpio = GPIOTools()
        self.relays = []
        self.state = 0
        for port in gpioPorts: 
            self.addRelay(port)
        self.__off()
        self.power = 0
    
    def addRelay(self,gpioPort):
        self.relays.append(self.gpio.GPIOSwitch(gpioPort))
    
    def __on(self):
        for relay in self.relays:
            relay.on()
        self.state = 1

    def __off(self):
        for relay in self.relays:
            relay.off()
        self.state = 0
    
    def setState(self, state):
        for relay in self.relays:
            relay.setState(state)
        self.state = state
    
    def toggle(self):
        for relay in self.relays:
            relay.toggle()
        self.state = self.state-1%2
    
    def getState(self):
        return self.state
    def setPower(self, power):
       # Set the power. 0 is off, 1 is light pulse, 2 is heavy pulse, 3 is continuous operation
        if power > 3:
            power = 3
        if power < 0:
            power = 0
        self.power = power
        if power == 3:
            self.__on()
        elif power == 2:
            self.pulse(2, 1)
        elif power == 1:
            self.pulse(1, 2)
        else:
            self.__off()
        return 

    def getPower(self):
        return self.power
         
    def pulse(self, time_on, time_off):
        self.__on()
        time.sleep(time_on)
        self.__off()
        time.sleep(time_off)
        return self.state
    
    

heater = Heater([18]) # Put each of the GPIO pins you need in here
thermometer = Thermometer(['28-051685065aff'])    
#thermometer = Thermometer(['28-051685065aff', '28-0416847451ff'])    
thermostat = Thermostat()
lcd = LCDDisplay()

gpio = GPIOTools()
pumprelay = gpio.GPIOSwitch(19) #for gpio pin 19 being used.
#use pumprelay.on() 
#use pumprelay.off() 
#use pumprelay.getState() 
#use pumprelay.setState(0) #for off
#use pumprelay.setState(1) #for on

LCDDaemon = threading.Thread(target=LCDDaemon,args=(lcd,))
LCDDaemon.daemon=True
LCDDaemon.start()



# Do the REST API bit
app = Bottle()
@app.route('/hello')
def hello():
    return "Hello World"

@app.get('/temperature')
def getState():
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'temp': thermometer.getAverageTemperature()})

@app.get('/temperature/<sensor>')
def getStateBySensor( sensor = 0):
    response.headers['Content-Type'] = 'application/json'
    sensors = thermometer.getSensorByIndex(sensor)
    temp = thermometer.getTemperature()
    return json.dumps({'temp': sensors.getTemperature()})

@app.get('/thermostat')
def getThermostat():
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'state': thermostat.getThermostat()})

@app.post('/thermostat')
def setThermostat():
    new_temp = float(request.body.read())
    print new_temp
    try:
        new_temp = thermostat.setThermostat(new_temp)
    except ValueError:
        response.status = 400
        return
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'state': thermostat.getThermostat()})
     

@app.get('/heater')
def getHeater():
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'state': heater.getState()})

@app.post('/heater')
def changeHeater():
    new_state = int(request.body.read())
    print new_state
    try:
        if (new_state > 1) | (new_state < 0):
            raise ValueError
    except ValueError:
        response.status = 400
        return
    new_state = heater.setState(new_state)

    response.headers['Content-Type'] = 'application/json'
    return json.dumps({'state': heater.getState()})


run(app, host='192.168.0.37', port=8080)

