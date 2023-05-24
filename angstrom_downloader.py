""" 
angstrom_downloader.py
======================

Author: Mattia Mancini
Created: 24-May-2023
-----------------------

DESCRIPTION
Script that uses the NASAPowerWeatherDataProvider from Wofost
to retrieve and estimate the Angstrom A and B coeffifients.
These are stored by parcel into a csv file which is then used
in the NetCDFWeatherDataProvider.
------------  AAA  -------------------
This is just a temporary fix to avoid having to call the 
NASA weather data provider every time. In the future we will
need to review and improve the entire estimation of the 
various values of evapotranspiration!!!
"""

from pcse.util import check_angstromAB
from pcse.db import NASAPowerWeatherDataProvider
from cropyields import data_dirs, db_parameters
from cropyields.utils import osgrid2lonlat
import psycopg2
import pandas as pd

# retrieve parcel list
conn = None    
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

# retrieve Angstrom coefficients
angst_coeff = {}
for parcel in parcel_os_code:
    print(f'Estimating Angstrom coefficients for parcel \'{parcel}\'...')
    os_digits = [int(s) for s in parcel if s.isdigit()]
    os_digits_1k = os_digits[0:2] + os_digits[int(len(os_digits)/2):int(len(os_digits)/2+2)]
    os_digits_1k = ''.join(str(s) for s in os_digits_1k)
    osgrid_1km = parcel[0:2].upper() + os_digits_1k
    lon, lat = osgrid2lonlat(osgrid_1km, EPSG=4326)
    w = NASAPowerWeatherDataProvider(lon, lat)
    angstA, angstB = w.angstA, w.angstB
    angstA, angstB = check_angstromAB(angstA, angstB)
    angst = {
        "angstA": angstA,
        "angstB": angstB
    }
    angst_coeff[parcel] = angst


df = pd.DataFrame(angst_coeff).T
df.index.names = ['parcel']
df.to_csv(data_dirs['utils_dir'] + 'angst_coefficients.csv')






