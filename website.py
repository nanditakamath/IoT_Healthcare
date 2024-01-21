from datetime import datetime, timedelta

import sys
import boto3
import decimal
import json
import time
import matplotlib.pyplot as plt
import os
import glob
import random
import pytz

from flask import Flask, render_template
from boto3.dynamodb.conditions import Key, Attr
from pprint import pprint
app = Flask(__name__, static_url_path='/workspace/iot_course/aws-iot-sensors/dashboard/static')
db = boto3.resource('dynamodb', region_name='us-east-2')


class DB:
    
    def retrieve_values1():
        table1 = db.Table('MAX30100')
        response1 = table1.query(
            KeyConditionExpression=Key('mac_Id').eq('d8:f1:5b:11:a1:dc'),
            ScanIndexForward=False,
            Limit=20,
            FilterExpression=Attr('Pulse_Rate').gte(-1)
        )
        return response1
        
    def retrieve_values2():
        table2 = db.Table('MLX90614')
        response2 = table2.query(
            KeyConditionExpression=Key('mac_Id').eq('b8:27:eb:ef:ce:e9'),
            ScanIndexForward=False,
            Limit=10,
            FilterExpression=Attr('Ambient_Temp').gte(-1)
        )
        return response2


# Index Page
@app.route('/')
def landing_handler1():
    files = glob.glob('/workspace/iot_course/aws-iot-sensors/dashboard/static/img/*')
    for f in files:
        os.remove(f)
    DBx = (DB.retrieve_values1())[u'Items']
   

    for i in range(0, len(DBx)):
        DBx[i]['ts'] = (datetime.fromtimestamp(int((str(DBx[i]['ts']))[:-3])) + timedelta(hours=5, minutes=30)).strftime('%H:%M:%S')
        xa = []
        ya1 = []
        ya2 = []
    for i in range(0, len(DBx)):
        xa.append(DBx[len(DBx)-i-1]['ts'])
        ya1.append(DBx[len(DBx)-i-1]['Pulse_Rate'])
        ya2.append(DBx[len(DBx)-i-1]['Spo2'])
    fig, ax = plt.subplots(figsize=(20, 10))
    plt.plot(xa, ya1, label='Temperature')
    plt.plot(xa, ya2, label='Humidity')
    plt.legend(loc="upper left")
    n = random.randint(0, 1000);
    fname1 = 'my_plot' + str(n) + '.jpg'
    fig.savefig(str('/workspace/iot_course/aws-iot-sensors/dashboard/static/'+fname1))
    return render_template('index.html', DBx=DBx, fname1=fname1)





if __name__ == '__main__':
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    else:
        #host = '127.0.0.1'
        host = '0.0.0.0'

    app.run(host=host, debug=True)
