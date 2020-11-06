
import random
import pyxdf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import copy
from pathlib import Path
from pylsl import local_clock
import time

#Calculate difference between LSL clock and computer clock
t1 = local_clock()
t2 = time.time()
difference = t2 - t1


dataPath  = Path('./data_raw/')
experiment = 2
for f in dataPath.glob('*.xdf'):

    #Load xdf files
    if len(re.findall(".xdf", f.name))>0:
        file = f

        # Rename files --> remove identifiers
        uid = re.findall('.+(?=_S[0-9]+_T0[0-9][0-9]_)', file.name)[0]
        session = int(re.findall('(?<=_S)[0-9]+(?=_T0[0-9][0-9]_)', file.name)[0])
        trial = int(re.findall('(?<=_S[0-9]{2}_T)[0-9]{3}(?=_)', file.name)[0])
        task = re.findall('(?<=_S[0-9]{2}_T[0-9]{3}_).+(?=.xdf)', file.name)[0]

        dstPath = Path('./data_txt/') / "{:}_S{:02d}_T{:02d}_{:}_raw.txt".format(uid, session, trial, task)

        print(uid, session, trial, task)
        print("srcPath", f)
        print("dstPath", dstPath)

        data, header = pyxdf.load_xdf(file)

        #Get data and experiment markers
        for stream in data:
            if stream['info']['name'][0] == 'ExperimentMarkers':
                markers = stream['time_series']
                markersTime = stream['time_stamps']
            elif stream['info']['name'][0] == 'NB-2015.10.15' or stream['info']['name'][0] == 'NB-2015.10.16':
                if stream['footer']['info']['first_timestamp'][0] != '0':
                    eegData = stream['time_series']
                    eegInfo = stream['info']
                    eegTime = stream['time_stamps']

        #Get EEG headers
        columns = []
        listOfChannels = eegInfo['desc'][0]['channels'][0]['channel']
        for ch in listOfChannels:
            try:
                columns.append(ch['label'][0])
            except:
                columns.append(ch['name'][0])

        columns = [x.upper() for x in columns]
        eegChannels = copy.deepcopy(columns)
        #eegChannels.remove("COUNTER")

        #Create data frame
        df =  pd.DataFrame(data=eegData, index=None, columns=columns)

        #Add label and time stamps
        df['COMPUTER_TIME'] = eegTime

        #Label
        if task == "Baseline" or task == 'BASELINE': #Baseline
            df['label'] = 0
        elif task == "Normal" or task == "Easy" or task == 'Low' or task == 'LOW': #Low Workload
            df['label'] = 5
        elif task == "Inv" or task =='inv' or task == "High" or task == 'HIGH': # high Workload
            df['label'] = 10

        #Remove data before start and after finish
        df = df.loc[(df['COMPUTER_TIME'] > markersTime[0]) & (df['COMPUTER_TIME'] < markersTime[1]) ]

        #Update timestamps to computer time
        df['COMPUTER_TIME'] = df['COMPUTER_TIME'] + difference

        print(len(df['COMPUTER_TIME']))
        #Save to CSV

        df.to_csv(dstPath,index=None)
