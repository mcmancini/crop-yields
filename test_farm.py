from cropyields.FarmManager import Farm
import psycopg2
from cropyields import db_parameters
import time 
from cropyields.config import wheat_args, maize_args, potato_args
from cropyields.CropManager import Crop, CropRotation
  
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
potatoes = Crop('potato', 'Potato_701', 2023, **potato_args)
wheat = Crop('wheat', 'Winter_wheat_106', 2023, **wheat_args)
maize = Crop('maize', 'maize_01', 2025, **maize_args)
rotation_1 = CropRotation(potatoes, wheat, maize)
rotation_2 = CropRotation(potatoes, wheat, maize)
prova = {
    parcels[0]: rotation_1,
    parcels[1]: rotation_1,
    parcels[2]: rotation_2
}


start_time = time.time()
dt = a.run(**prova)
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



import pandas as pd
import datetime

# Sample DataFrame with datetime index
data = {'Value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
index = pd.date_range(start='2023-01-01', periods=10, freq='D')
df = pd.DataFrame(data, index=index)

# List of datetime bounds
bounds = [datetime.date(2023, 4, 1), datetime.date(2023, 11, 5), datetime.date(2025, 4, 1)]

# Convert datetime bounds to pandas Timestamps
bounds = [pd.Timestamp(bd) for bd in bounds]

# Convert datetime bounds to numeric values
ref_date = pd.Timestamp('1970-01-01')
numeric_bounds = [(bd - ref_date).days for bd in bounds]

# Split the DataFrame based on numeric bounds
split_data = pd.cut(df.index.to_julian_date(), bins=[-float('inf')] + numeric_bounds + [float('inf')], labels=False, include_lowest=True)
split_data = pd.Series(split_data)

dfs = []
for group in split_data.unique():
    dfs.append(df.loc[split_data == group])