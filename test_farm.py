# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), June 2023
# ====================================================
"""
Test script to experiment with farms, crops and rotations
"""
import datetime as dt
import time
import psycopg2
from cropyields.farm_manager import Farm
from cropyields import db_parameters
from cropyields.config import crop_parameters
from cropyields.crop_manager import Crop, CropRotation

# List of parcel codes
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

OSCode = parcel_os_code[1]
a = Farm(OSCode)
print(a)
parcels = a.parcel_ids

# Rotation 1
potato_args = crop_parameters['potato']
potato_args['variety'] = 'Potato_701'
potatoes = Crop(2023, 'potato', **potato_args)

wheat_args = crop_parameters['wheat']
wheat_args['variety'] = 'Winter_wheat_106'
wheat = Crop(2023, 'wheat', **wheat_args)

maize_args = crop_parameters['maize']
maize_args['variety'] = 'Grain_maize_201'
maize = Crop(2025, 'maize', **maize_args)

fallow_args = {
    'start_crop_calendar': dt.date(2024, 9, 1)
}
fallow = Crop(2024, 'fallow', **fallow_args)

ryegrass_args = crop_parameters['ryegrass']
ryegrass_args['variety'] = 'Northern_RyeGrass'
npk_4 = {
    'month': 6,
    'day': 30,
    'N_amount': 70, 
    'P_amount': 35,
    'K_amount': 105
}
ryegrass_args['apply_npk'] = [npk_4]
# del ryegrass_args['mowing']
ryegrass = Crop(2024, 'rye_grass', **ryegrass_args)
ryegrass_rotation = CropRotation(ryegrass, fallow)

rotation_1 = CropRotation(potatoes, wheat, fallow, maize)
# rotation_2 = CropRotation(potatoes, fallow)
prova = {
    parcels[0]: rotation_1,
    parcels[1]: rotation_1,
    parcels[2]: rotation_1
}


start_time = time.time()
dt = a.run_rotation(**prova)
end_time = time.time()
end_time - start_time


# save_folder = 'D:\Documents\Data\PCSE-WOFOST\WOFOST_output\Figures'
# year = 2020
# col = 'yield_parcel'
# a.save_yield_map(year, col, f"{save_folder}\\{a.farm_id}_{year}.html")
# a.plot_yields(2020, 'yield_ha', f"{save_folder}\\{a.farm_id}_{year}.tiff")


# from cropyields.CropManager import Crop, CropRotation
# import datetime as dt
# events = {}
# events['date'] = dt.date(2024, 2, 15)
# events['N_amount'] = 60
# events['P_amount'] = 15
# events['K_amount'] = 5
# args = {}
# args['apply_npk'] = {}
# args['apply_npk'] = [events, events]
# args['crop_start_date'] = dt.date(2023, 11, 10)

# a = Crop('maize', 'maize_01', 2023)
# print(a.agromanagement)
# b = Crop('wheat', 'winter_wheat_01', 2023, **args)
# print(b.agromanagement)

# crop1 = Crop("wheat", "Winter_wheat_106", 2023, **args)
# crop2 = Crop("corn", "Yellow_corn_205", 2025)
# print(crop1.agromanagement)
# print(crop2.agromanagement)

# rotation = CropRotation(crop1, crop2)
# print(rotation.rotation)


# from pcse.fileinput import YAMLCropDataProvider
# p = YAMLCropDataProvider()
# print(p)