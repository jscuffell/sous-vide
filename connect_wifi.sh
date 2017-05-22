#!/bin/bash
# This little script creates a WPA supplicant config file and runs it::w#!/bin/bash
ssid=$1
passkey=$2

service hostapd stop
service dnsmasq stop
service dhcpcd stop

wpa_passphrase $ssid $passkey > wpa_supplicant.conf
ifdown wlan0
ifconfig wlan0 up
killall wpa_supplicant
/sbin/wpa_supplicant -s -B -P /run/wpa_supplicant.wlan0.pid -i wlan0 -D nl80211,wext -c `pwd`/wpa_supplicant.conf
ip addr flush dev wlan0

dhcpcd wlan0
