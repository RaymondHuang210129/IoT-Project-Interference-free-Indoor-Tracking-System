#!/usr/bin/python3

import serial
import time
from subprocess import Popen, PIPE, DEVNULL
import psutil, signal
import logging
import http.client, urllib, json
import math
import threading
import numpy as np
import requests
from lmfit import minimize, Parameters
import sys

x_length = 4.5;
y_length = 2.0;

if len(sys.argv) == 3:
    x_length = float(sys.argv[1])
    y_length = float(sys.argv[2])


DEVICE_INFO = {
    'device_id': "DDaP0YH4",
    'device_key': "rpb87R8Ea6zvnnMk"
}

SNIFFER_LOCATION = np.array([[x_length, y_length],
                             [x_length, 0.0],
                             [0.0, y_length],
                             [0.0, 0.0]])

def to_distance(rssi):
    return pow(10.0, (-50 - rssi) / (10 * 2.8))

def to_dist_with_strength(rssi, strength):
    return pow(10.0, (strength - rssi) / (10 * 2.8))

def enhanced_to_distance(rssi1, rssi2, x_length, y_length):
    diag_dist = ((x_length ** 2) + (y_length ** 2)) ** 0.5
    strength = [-70, -67.5, -65, -62.5, -60, -57.5, -55, -52.5, -50, -47.5, -45, -42.5, -40]
    selected_dist1 = 0
    selected_dist2 = 0
    selected_strength = 0
    min_error = 100.0
    for i in strength:
        dist1 = to_dist_with_strength(rssi1, i)
        dist2 = to_dist_with_strength(rssi2, i)
        if abs((dist1 + dist2) - diag_dist) < min_error:
            selected_dist1 = dist1
            selected_dist2 = dist2
            selected_strength = i
            min_error = abs((dist1 + dist2) - diag_dist)
    print("selected strength:", selected_strength)
    return selected_dist1, selected_dist2


def kill_child_process(ppid, sig=signal.SIGKILL):
    try:
        proc = psutil.Process(ppid)
    except psutil.error.NoSuchProcess:
        return
    cpid = proc.children(recursive=True)
    for pid in cpid:
        os.kill(pid.pid. sig)

def receive_packet(interface, macList):
    try:
        global rssiList
        serialPort = "/dev/ttyUSB%d" % interface
        serialRate = 115200
        ser = serial.Serial(serialPort, serialRate)
        t1 = time.time()
        while True:
            t2 = time.time()
            if (t2 - t1) <= 2:
                while ser.in_waiting:
                    data = ser.readline().decode("ascii").split()
                    if len(data) >= 5 and data[4] in macList:
                        if data[4] not in rssiList[interface]:
                            rssiList[interface][data[4]] = [int(data[2])]
                        else:
                            rssiList[interface][data[4]].append(int(data[2]))
            else:
                break
        ser.close()
    except KeyboardInterrupt:
        ser.close()
        pass

def receive_all(macList):
    try:
        global rssiList
        global ser
        t1 = time.time()
        while True:
            t2 = time.time()
            if (t2 - t1) <= 2:
                for j in range(0, 4):
                    while ser[j].in_waiting:
                        data = ser[j].readline().decode("ascii").split()
                        if len(data) >= 5 and data[4] in macList:
                            if data[4] not in rssiList[j]:
                                rssiList[j][data[4]] = [int(data[2])]
                            else:
                                rssiList[j][data[4]].append(int(data[2]))
            else:
                break
    except KeyboardInterrupt:
        pass

def distance(p1, p2):
    s = 0
    for i in range(0, 2):
        s += (p1[i] - p2[i]) ** 2
    return s ** 0.5

def residual(params, measures, sniffers):
    x = np.array([params['x'].value,
                  params['y'].value])
    s = np.empty(sniffers.shape[0])
    for i in range(0, sniffers.shape[0]):
        s[i] = (measures[i] - distance(sniffers[i], x)) ** 2
    return s

def get_location(distances):
    global x_length
    global y_length
    global SNIFFER_LOCATION
    init = np.array([x_length / 2, y_length / 2])
    params = Parameters()
    params.add('x', value = init[0])
    params.add('y', value = init[1])
    out = minimize(residual, params, args=(distances, SNIFFER_LOCATION))
    return out

def pretty_print(x, y):
    global SNIFFER_LOCATION
    x_length = int(SNIFFER_LOCATION[0][0] / 0.25)
    y_length = int(SNIFFER_LOCATION[0][1] / 0.25)
    x_pos = int(x / 0.25)
    if x_pos < 0:
        x_pos = 0
    elif x_pos > x_length:
        x_pos = x_length
    y_pos = int(y / 0.25)
    if y_pos < 0:
        y_pos = 0
    elif y_pos > y_length:
        y_pos = y_length
    canvas = []
    for i in range(0, x_length + 2):
        canvas.append([])
        for j in range(0, y_length + 2):
            canvas[i].append(" ")
    for i in range(0, (x_length + 2)):
        for j in range(0, (y_length + 2)):
            if (i == 0 and j == 0) or (i == (x_length + 1) and j == (y_length + 1) or (i == 0 and j == (y_length + 1)) or (i == (x_length + 1) and j == 0)):
                canvas[i][j] = "+"
            elif (i == 0 or i == (x_length + 1)) and (j != 0 and j != (y_length + 1)):
                canvas[i][j] = "|"
            elif j == 0 or j == (y_length + 1) and (i != 0 and i != x_length + 1):
                canvas[i][j] = "-"
            else:
                canvas[i][j] = " "
    canvas[x_pos][y_pos] = "*"
    for i in range((y_length + 1), -1, -1):
        for j in range(0, (x_length + 2)):
            print(canvas[j][i], end='')
        print('\n', end='')
    print('\n', end='')




print("start")
macList = []
processPingList = []
threadReceiveList = []
rssiList = []
ser = []
request_data = {'data': {}}
try:
    for i in range(0, 4):
        serialPort = "/dev/ttyUSB%d" % i
        serialRate =115200
        ser.append(serial.Serial(serialPort, serialRate))
    while True:
        processARP = Popen(['arp', '-a', '-n'], stdout=PIPE)
        (out, err) = processARP.communicate()
        exitCode = processARP.wait()
        output = out.decode('utf-8').split('\n')
        macList = []
        rssiList = []
        for i in range(0, 4):
            rssiList.append(dict())

        processPingList = []
        for entry in output:
            value = entry.split(" ")
            if len(value) >= 7 and value[3] != "<incomplete>" and value[6] == "wlan0":
                macList.append(value[3])
                for i in range(0, 4):
                    rssiList[i][value[3]] = []
                processPingList.append(Popen(["ping", value[1][1:-1], "-c", "10", "-i", "0.4"], stdout=DEVNULL))
        print(macList)

#        threadReceiveList = []
#        for i in range(0, 4):
#            threadReceiveList.append(threading.Thread(target = receive_packet, args = (i, macList,)))
#            threadReceiveList[i].start()

#        for i in range(0, 4):
#            threadReceiveList[i].join()
        receiveThread = threading.Thread(target = receive_all, args = (macList,))
        receiveThread.start()
        receiveThread.join()

        for proc in processPingList:
            kill_child_process(proc.pid)
            proc.terminate()
        
        request_data = {'data': {}}
        for mac in macList:
            rssiAvg = []
            for i in range(0, 4):
                if len(rssiList[i][mac]) > 0:
                    rssiAvg.append(sum(rssiList[i][mac]) / len(rssiList[i][mac]))
                else:
                    rssiAvg.append(0)
            
            print(mac, "recv cnt:", "%d,   %d,   %d,   %d," % (len(rssiList[0][mac]), len(rssiList[1][mac]), len(rssiList[2][mac]), len(rssiList[3][mac])))
            print(mac, "Avg rssi:", "%.2f, %.2f, %.2f, %.2f dBm" % (rssiAvg[0], rssiAvg[1], rssiAvg[2], rssiAvg[3]))
            print(mac, "Avg dist:", "%.2f, %.2f, %.2f, %.2f m" % (to_distance(rssiAvg[0]), to_distance(rssiAvg[1]), to_distance(rssiAvg[2]), to_distance(rssiAvg[3])))
            distances = np.arange(float(SNIFFER_LOCATION.shape[0]))
            #for i in range(0, SNIFFER_LOCATION.shape[0]):
            #    distances[i] = to_distance(rssiAvg[i])
            distances[0], distances[3] = enhanced_to_distance(rssiAvg[0], rssiAvg[3], x_length, y_length)
            distances[1], distances[2] = enhanced_to_distance(rssiAvg[1], rssiAvg[2], x_length, y_length)
            result = get_location(distances)
            result.params['x'].value = min(max(0.0, result.params['x'].value), x_length)
            result.params['y'].value = min(max(0.0, result.params['y'].value), y_length)
            print(mac, "Coordinate:", "(%.2f, %.2f)" % (result.params['x'].value, result.params['y'].value))
            pretty_print(result.params['x'].value, result.params['y'].value)
            request_data['data'].update({mac: [result.params['x'].value, result.params['y'].value, distances[0], distances[1], distances[2], distances[3]]})
        print(request_data)
        try:
            requests.post("http://140.113.95.198:5000/raspberryPi", json = request_data)
        except:
            pass
except KeyboardInterrupt:
    print("end")
    receiveThread.join()
    for i in range(0, 4):
        ser[i].close()
'''

try:
    t1 = time.time()
    while True:
        t2 = time.time()
        ## set refresh interval 2 second
        if (t2 - t1) > 2:
            t1 = t2
            ## calculate the rssi result and show
            message = "distances:\n"
            for k, v in rssiList.items():
                if len(v) > 0:
                    avgRssi = sum(v) / len(v)
                    print(k, avgRssi)
                    message += (str(k) + ": " + "%.2f m" % calculate_distance(avgRssi) + "\n")
            print(message)
            data = {
                'datapoints': [{
                    'dataChnId': 'esp32_distaance',
                    'values': {'value': message}
                }]
            }
            header = {
                'Content-type': 'application/json',
                'deviceKey': 'rpb87R8Ea6zvnnMk'
            }
            #try:
            #    conn = http.client.HTTPConnection("api.mediatek.com:80")
            #    conn.connect()
            #except (httplib.HTTPException, socket.error) as ex:
            #    print(ex)
            #conn.request("POST", "/mcs/v2/devices/DDaP0YH4/datapoints", json.dumps(data), header)
            #response = conn.getresponse()
            #print(response.status)
            ## kill ping process
            for proc in processList:
                kill_child_process(proc.pid)
                proc.terminate()
            processList = []
            ## get the connected devices
            process = Popen(["arp", "-a", "-n"], stdout=PIPE)
            (out, err) = process.communicate()
            exit_code = process.wait()
            output = out.decode("utf-8").split("\n")
            ## put device mac into list and dict
            rssiList = dict()
            macList = []
            for entry in output:
                mac = entry.split(" ")
                if len(mac) >= 7 and mac[3] != "<incomplete>" and mac[6] == "wlan0":
                    macList.append(mac[3])
                    rssiList[mac[3]] = []
                    ## start ping process
                    processList.append(Popen(["ping", mac[1][1:-1], "-c", "3"], stdout=DEVNULL))
            print(macList)
        ## receive sniffered packet
        while ser.in_waiting:
            data = ser.readline().decode("ascii").split()
            if len(data) >= 5 and data[4] in macList:
                if data[4] not in rssiList:
                    rssiList[data[4]] = [int(data[2])]
                else:
                    rssiList[data[4]].append(int(data[2]))
except KeyboardInterrupt:
    ser.close()
    print("end")

'''
