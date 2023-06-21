# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), June 2023
# ====================================================
# 
# DESCRIPTION
# Script to perform sensitivity analysys on agromanagement
# for a selected crop. Parameters that can be changed are 
# the crop calendar year, sowing date, fertilisation dates 
# and fertilisation amounts
# =========================================================
import psycopg2
from cropyields import db_parameters, data_dirs
import random
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import yaml

import pcse
from pcse.models import Wofost72_WLP_FD
from pcse.fileinput import YAMLCropDataProvider
from pcse.util import WOFOST80SiteDataProvider
from cropyields.SoilManager import SoilGridsDataProvider
from cropyields.WeatherManager import NetCDFWeatherDataProvider
from pcse.base import ParameterProvider
import datetime as dt
import random


# DIRS
base_dir = data_dirs['wofost_dir']
crop_dir = base_dir + 'WOFOST_crop_parameters\\'
agromanagement_dir = base_dir + 'pcse_examples\\'
output_dir = base_dir + 'WOFOST_output\\'

# PARCELS
conn = psycopg2.connect(user=db_parameters['db_user'],
                        password=db_parameters['db_password'], 
                        database=db_parameters['db_name'], 
                        host='127.0.0.1', 
                        port= '5432')
conn.autocommit = True
cur = conn.cursor()
sql = '''
    SELECT parcel_id, nat_grid_ref 
    FROM parcels;
    '''
cur.execute(sql)
t = cur.fetchall()
parcel_list = [row[0] for row in t]
parcel_os_code = [row[1] for row in t]
if conn is not None:
    conn.close()

num_samples = 1
sampled_parcels = random.sample(parcel_os_code, num_samples)

# AGROMANAGEMENT
# PARAMETERS
start_year = 2022
crop = "wheat"
variety = "Winter_wheat_106"
crop_start_date = dt.date(start_year, 9, 1)
year = start_year + 1
month_1, month_2, month_3 = 2, 4, 5
day_1, day_2, day_3 = 20, 1, 1
N_amount_1, N_amount_2, N_amount_3 = 60, 100, 50
P_amount_1, P_amount_2, P_amount_3 = 3, 13, 23
K_amount_1, K_amount_2, K_amount_3 = 4, 14, 24

agromanagement_yaml = f"""
AgroManagement:
- {start_year}-09-01:
    CropCalendar:
        crop_name: {crop}
        variety_name: {variety}
        crop_start_date: {crop_start_date}
        crop_start_type: sowing
        crop_end_date:
        crop_end_type: maturity
        max_duration: 365
    TimedEvents:
    -   event_signal: apply_npk
        name:  Timed N/P/K application table
        comment: All fertilizer amounts in kg/ha
        events_table:
        - {year}-{month_1:02d}-{day_1:02d}: {{N_amount: {N_amount_1}, P_amount: {P_amount_1}, K_amount: {K_amount_1}}}
        - {year}-{month_2:02d}-{day_2:02d}: {{N_amount: {N_amount_2}, P_amount: {P_amount_2}, K_amount: {K_amount_2}}}
        - {year}-{month_3:02d}-{day_3:02d}: {{N_amount: {N_amount_3}, P_amount: {P_amount_3}, K_amount: {K_amount_3}}}
    StateEvents: Null
- {year}-09-01:
"""

cropd = YAMLCropDataProvider(crop_dir)
cropd.set_active_crop(crop, variety)
sitedata = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)
agromanagement = yaml.load(agromanagement_yaml, Loader=yaml.FullLoader)

# LOOP OVER PARCELS
for parcel in sampled_parcels:
    results = []
    soildata = SoilGridsDataProvider(parcel)
    wdp = NetCDFWeatherDataProvider(parcel, 'rcp26', 1, force_update=False)
    parameterprovider = ParameterProvider(soildata=soildata, cropdata=cropd, sitedata=sitedata)
    for i in range(75):
        csdate = crop_start_date + dt.timedelta(days=i)
        print(csdate)
        mgmt = agromanagement_yaml.replace(str(crop_start_date), str(csdate))
        agromanagement = yaml.load(mgmt, Loader=yaml.FullLoader)
        wofost = Wofost72_WLP_FD(parameterprovider, wdp, agromanagement)
        wofost.run_till_terminate()
        output = wofost.get_output()
        df = pd.DataFrame(output).set_index("day")
        results.append(df)


def generate_random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    color_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)

    return color_code

num_iterations = 75

colors = [generate_random_color() for _ in range(num_iterations)]
fig, ax = plt.subplots(figsize=(8, 6))

for c, df in zip(colors, results):
    df['TWSO'].plot(ax=ax, color=c)

ax.set_title('TWSO')
fig.autofmt_xdate()
plt.show()