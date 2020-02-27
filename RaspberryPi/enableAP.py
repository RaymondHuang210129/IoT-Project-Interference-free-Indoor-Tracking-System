#!/usr/bin/python3

from PyAccessPoint import pyaccesspoint


accessPoint = pyaccesspoint.AccessPoint(wlan='wlan0', inet=None, ip='192.168.30.1', netmask='255.255.255.0', ssid='RaymondPi', password='00000000')
if accessPoint.is_running():
    accessPoint.stop()
result = accessPoint.start()
print(result)
