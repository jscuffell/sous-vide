#!/bin/bash
# To start a hotspot, shut down wpa_supplicant. Then start up hostapd using the current details

ip="10.0.0.1" # this is so it works with the dhcp server

killall wpa_supplicant
killall dhcpcd
service hostapd stop
service dnsmasq stop

ifdown wlan1
ifconfig wlan1 down
ip address flush dev wlan1

service hostapd restart
service dnsmasq restart
ifconfig wlan1 $ip netmask 255.255.255.0 up
echo $ip
