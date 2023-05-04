from pcse.fileinput import YAMLCropDataProvider
import os
from pcse.fileinput import YAMLAgroManagementReader
from pcse.util import WOFOST80SiteDataProvider
from cropyields import db_parameters
import psycopg2
from cropyields.SoilManager import SoilGridsDataProvider
from cropyields.dataproviders import NetCDFWeatherDataProvider
from pcse.base import ParameterProvider
from pcse.models import Wofost71_WLP_FD
import pandas as pd
from cropyields.utils import printProgressBar

# INPUT PARAMETERS
rcp = 'rcp26'
ensemble = 1

# YAML CROP PARAMETERS
data_dir = 'D:\\Documents\\Data\\PCSE-WOFOST\\'
cropd = YAMLCropDataProvider(data_dir+'WOFOST_crop_parameters')
cropd.set_active_crop('wheat', 'Winter_wheat_101')

# AGROMANAGEMENT
agromanagement_file = os.path.join(data_dir, 'pcse_examples\\wwheat_oneyr.agro')
agromanagement = YAMLAgroManagementReader(agromanagement_file)

# SITE PARAMETERS
sitedata = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)


# PARCEL LIST
conn = None    
conn = psycopg2.connect(user=db_parameters['db_user'],
                        password=db_parameters['db_password'], 
                        database=db_parameters['db_name'], 
                        host='127.0.0.1', 
                        port= '5432')
conn.autocommit = True
cur = conn.cursor()
sql = '''
    SELECT nat_grid_ref 
    FROM parcels;
    '''
cur.execute(sql)
t = cur.fetchall()
parcel_list = [row[0] for row in t]
if conn is not None:
    conn.close()

# LOOP TO RUN WOFOST
wheat_yields = {}
counter = 1
total = len(parcel_list)
for parcel in parcel_list:
    printProgressBar(counter, total)
    parcel_yield = {}
    soildata = SoilGridsDataProvider(parcel)
    wdp = NetCDFWeatherDataProvider(parcel, rcp, ensemble, force_update=False)
    parameters = ParameterProvider(cropdata=cropd, soildata=soildata, sitedata=sitedata)
    wofsim = Wofost71_WLP_FD(parameters, wdp, agromanagement)
    try:
        wofsim.run_till_terminate()
    except:
        continue
    output = wofsim.get_output()
    varnames = ["TWSO"]
    tmp = {}
    for var in varnames:
        tmp[var] = [t[var] for t in output]
    d = [len(tmp[x]) for x in varnames] 

    df = pd.DataFrame(output)
    df.set_index('day', inplace=True, drop=True)
    parcel_yield = {
        "yield": df['TWSO'].max(),
        "harvest_date": df['TWSO'].idxmax().strftime('%Y-%m-%d')
    }
    wheat_yields[parcel] = parcel_yield
    counter += 1

os_1k = []
os_10k = []
for parcel in parcel_list:
    os_digits = [int(s) for s in parcel if s.isdigit()]
    os_digits_1k = os_digits[0:2] + os_digits[int(len(os_digits)/2):int(len(os_digits)/2+2)]
    os_digits_10k = os_digits[0:1] + os_digits[int(len(os_digits)/2):int(len(os_digits)/2+1)]
    os_digits_1k = ''.join(str(s) for s in os_digits_1k)
    os_digits_10k = ''.join(str(s) for s in os_digits_10k)
    os_1k.append(parcel[0:2].upper() + os_digits_1k)
    os_10k.append(parcel[0:2].upper() + os_digits_10k)

os_10k = list(set(os_10k))