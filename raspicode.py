import paho.mqtt.client as paho
import os
import socket
import ssl
import random
import string
import json
from time import sleep
from random import uniform
 
from smbus2 import SMBus
from mlx90614 import MLX90614

bus = SMBus(1)
sensor = MLX90614(bus, address=0x5A)

connflag = False
 
def on_connect(client, userdata, flags, rc):                # func for making connection
    global connflag
    print "Connected to AWS"
    connflag = True
    print("Connection returned result: " + str(rc) )
 
def on_message(client, userdata, msg):                      # Func for Sending msg
    print(msg.topic+" "+str(msg.payload))
   
def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)
    return result_str
   
def getMAC(interface='eth0'):
  # Return the MAC address of the specified interface
  try:
    str = open('/sys/class/net/%s/address' %interface).read()
  except:
    str = "00:00:00:00:00:00"
  return str[0:17]
def getEthName():
  # Get name of the Ethernet interface
  try:
    for root,dirs,files in os.walk('/sys/class/net'):
      for dir in dirs:
        if dir[:3]=='enx' or dir[:3]=='eth':
          interface=dir
  except:
    interface="None"
  return interface
 
#def on_log(client, userdata, level, buf):
#    print(msg.topic+" "+str(msg.payload))
 
mqttc = paho.Client()                                       # mqttc object
mqttc.on_connect = on_connect                               # assign on_connect func
mqttc.on_message = on_message                               # assign on_message func
#mqttc.on_log = on_log

#### Change following parameters ####
awshost = "a2y9prqvlyko4a-ats.iot.us-east-2.amazonaws.com"      # Endpoint
awsport = 8883                                              # Port no.  
clientId = "RaspberryPi"                                     # Thing_Name
thingName = "RaspberryPi"                                    # Thing_Name
caPath = "/home/pi/AWSIoT/root-ca.pem"                                      # Root_CA_Certificate_Name
certPath = "/home/pi/AWSIoT/certificate.pem.crt"                            # <Thing_Name>.cert.pem
keyPath = "/home/pi/AWSIoT/private.pem.key"                          # <Thing_Name>.private.key
 
mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)  # pass parameters
 
mqttc.connect(awshost, awsport, keepalive=60)               # connect to aws server
 
mqttc.loop_start()                                          # Start the loop
 
while 1==1:
    sleep(5)
    if connflag == True:
        ethName=getEthName()
        ethMAC=getMAC(ethName)
        macIdStr = ethMAC
        Ambient_Temp = sensor.get_ambient()
        Body_Temp = sensor.get_object_1()
        paylodmsg0="{"
        paylodmsg1 = "\"mac_Id\": \""
        paylodmsg2 = "\", \"Ambient_Temp\":"
        paylodmsg3 = ", \"Body_Temp\": \""
        paylodmsg4="\"}"
        paylodmsg = "{} {} {} {} {} {} {} {}".format(paylodmsg0, paylodmsg1, macIdStr, paylodmsg2, Ambient_Temp, paylodmsg3, Body_Temp, paylodmsg4)
        paylodmsg = json.dumps(paylodmsg)
        paylodmsg_json = json.loads(paylodmsg)      
        mqttc.publish("IR_TEMPERATURE", paylodmsg_json , qos=1)        # topic: temperature # Publishing Temperature values
        print("msg sent: IR_TEMPERATURE" ) # Print sent temperature msg on console
        print(paylodmsg_json)
       
    else:
        print("waiting for connection...")                      
