import subprocess
from lcdtools import LCDDisplay

lcd = LCDDisplay()

def reset():
# Right. If this is called, then the whole script stops, and it's time to connect it to a new wifi network
# The process is: run a hotspot. Connect a phone to the hotspot. Then go to the web interface to connect it to the real wifi network. Update the hass and python script to represent the new IP address.
# There will be a daemon, run from the main script, which allows this whole process to happen at any point.
    lcd.setMessage("Booting hotspot...")
    processHotspot = subprocess.Popen(['sudo', './start_hotspot.sh'], stdout=subprocess.PIPE)
    out, err = processHotspot.communicate()
    # this should wait until it's finished
    lcd.setMessage("potage-sousvide\n" + out)
reset();
    
