#!/bin/bash
python sousvide.py &
sudo su - homeassistant -s /bin/bash -c "/home/homeassistant/start_hass.sh"
