from cropyields.FarmManager import Farm
import psycopg2
from cropyields import db_parameters
import time 
  
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
args = {
    'years': [2020, 2021],
    'crop': 'wheat',
    'variety': 'Winter_wheat_101',
    'agromanagement_file': 'winter_wheat_oneyr.agro'
}
start_time = time.time()
dt = a.run(**args)
end_time = time.time()
end_time - start_time



save_folder = 'D:\Documents\Data\PCSE-WOFOST\WOFOST_output\Figures'
year = 2020
col = 'yield_parcel'
a.save_yield_map(year, col, f"{save_folder}\\{a.farm_id}_{year}.html")
a.plot_yields(2020, 'yield_ha', f"{save_folder}\\{a.farm_id}_{year}.tiff")


from cropyields.CropManager import Crop, CropRotation
import datetime as dt
events = {}
events['date'] = dt.date(2024, 2, 15)
events['N_amount'] = 60
events['P_amount'] = 15
events['K_amount'] = 5
args = {}
args['apply_npk'] = {}
args['apply_npk'] = [events, events]
args['crop_start_date'] = dt.date(2023, 11, 10)

a = Crop('maize', 'maize_01', 2023)
print(a.agromanagement)
b = Crop('wheat', 'winter_wheat_01', 2023, **args)
print(b.agromanagement)

crop1 = Crop("wheat", "Winter_wheat_106", 2023, **args)
crop2 = Crop("corn", "Yellow_corn_205", 2025)
print(crop1.agromanagement)
print(crop2.agromanagement)

rotation = CropRotation(crop1, crop2)
print(rotation.rotation)