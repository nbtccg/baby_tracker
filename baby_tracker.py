#!./venv/bin/python2.7

#set tabstop=4 expandtab:

from pytz import timezone
import sys
import argparse
import yaml
import time
import threading
import datetime
import os.path
import Queue
from flask import Flask, render_template, request, redirect, url_for

mst = timezone('US/Mountain')
databaseName = "baby_database.db"
app = Flask(__name__)
global semaphore
semaphore = threading.BoundedSemaphore(1)

def UpdateTally(valType, value, activityDateTime):
    semaphore.acquire()
    database = open(databaseName, 'a')
    now = datetime.datetime.now()
    print str(now) + ": Storing" + valType, value 
    database.write(str(activityDateTime) + "," + valType + "," + str(value) + ",\n")
    database.close()
    semaphore.release()

@app.route('/data', methods=['GET','POST'])
def data():
    babyData = {} 
    print "Acquiring"
    semaphore.acquire()
    database = open(databaseName, 'r')
    lineCount=0
    currentDay=None
    suppTot = 0
    wetTot = 0
    stoolTot = 0
    for line in database:
        lineCount+=1
        (date, dataType, dataVal, notes)=line.split(',', 4)
        (nextDay, time) = date.split(" ",2)
        if currentDay is not None  and currentDay != nextDay:
            summaryDataList  = str(suppTot) + "ml / " + str(wetTot) + " / " + str(stoolTot)
            babyData[lineCount] = {"date": "DAY_CHANGE", "data_type": "Supplement/Wet/Stool", "value": summaryDataList, "notes": "" }
            lineCount+=1
            suppTot = 0
            wetTot  = 0
            stoolTot = 0   
        (currentDay, time) = date.split(" ",2)
        babyData[lineCount] = {"date": date, "data_type": dataType, "value": dataVal, "notes": notes }
        if "supplement" in dataType:
            suppTot+=int(dataVal)
        if "wet" in dataType:
            wetTot+=1
        if "stool" in dataType:
            stoolTot+=1
    database.close()
    lineCount+=1
    summaryDataList  = str(suppTot) + " / " + str(wetTot) + " / " + str(stoolTot)
    babyData[lineCount] = {"date": "DAY_CHANGE", "data_type": "Supplement/Wet/Stool", "value": summaryDataList, "notes": "" }
    print "Releasing"
    semaphore.release()
    return render_template('data.html', baby_data = babyData)

@app.route('/', methods=['GET','POST'])
def index():
    now = datetime.datetime.now()
    if request.method == 'POST':
        print "Incoming POST: ", request.data
        activityDateTime = request.form['date'] + " " + request.form['time']
        if request.form['submit'] == 'wet':
            UpdateTally('wet', 1, activityDateTime)
        elif request.form['submit'] == "stool":
            UpdateTally('stool', 1, activityDateTime)
        elif request.form['submit'] == "breast fed":
            UpdateTally('breast fed', request.form['duration'],activityDateTime)
        elif request.form['submit'] == "formula":
            UpdateTally('formula supplement', request.form['supp amount'], activityDateTime)
        elif request.form['submit'] == "breast milk":
            UpdateTally('breastmilk supplement', request.form['supp amount'], activityDateTime)
        elif request.form['submit'] == "pump":
            UpdateTally('pump', request.form['pump amount'], activityDateTime)
        elif request.form['submit'] == "Show Data":
            return redirect(url_for('data',_anchor='page_bottom'))
        else:
            print "Unknown input", request.form['submit']
        return redirect(url_for('data', _anchor='page_bottom'))
    elif request.method == 'GET':
        print "rendering"
    return render_template('index.html', date=now.strftime("%Y-%m-%d"), time=now.strftime("%I:%M%p"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, threaded=True, debug=True)
