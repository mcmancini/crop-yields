'''
CREATE NEV 2.0 SQL DATABASE
===========================

Author: Mattia Mancini
Created: 20-September-2022
--------------------------

Create a postgreSQL database containing the data for the NEV 2.0
farm model. It contains spatial data on parcels and farms including
parcel IDs, farm IDs, a reference to the National Grid cell, and the 
elevation, aspect and slope of each parcel
'''
from cropyields import db_parameters
from cropyields.db_manager import create_db, create_db_tables, drop_db, populate_table, get_dtm_values
import geopandas as gpd
import pandas as pd
from cropyields.utils import lonlat2osgrid
from sqlalchemy import create_engine
from cropyields.utils import printProgressBar

# 1) Create new database and relations
# ====================================
create_db()
create_db_tables()
# drop_db()

import sys, importlib
importlib.reload(sys.modules['cropyields.db_manager'])
from cropyields.db_manager import create_db_tables

# 2) Populate the database
# ========================

# 2.1. parcels
# ------------

# open shapefile of parcels
shp_path = 'D:\\Documents\\Data\\PCSE-WOFOST\\south_hams_arable\\'
parcels = gpd.read_file(shp_path + 'south_hams_arable_fields.shp')
parcels.rename({'oid':'parcel_id', 'custid': 'farm_id', 'full_parce': 'nat_grid_ref'}, axis=1, inplace=True)
centroids = gpd.GeoSeries(parcels.centroid.to_crs("EPSG:4326"))
coord_list = [(x,y) for x,y in zip(centroids.x , centroids.y)]
os_parcel_ref = [lonlat2osgrid(x, figs=10) for x in coord_list]
parcels['nat_grid_ref'] = os_parcel_ref
parcels['parcel_id'] = parcels['parcel_id'].astype(int)
parcels['farm_id'] = parcels['farm_id'].astype(int)
parcels = parcels.to_crs(epsg=4326)

# database connection
database_url = f"postgresql://{db_parameters['db_user']}:{db_parameters['db_password']}@localhost/{db_parameters['db_name']}"
engine = create_engine(database_url)

# Send the spatial dataframe to the postGIS database
table_name = 'parcels'
parcels.to_postgis(table_name, engine, if_exists='append', index=False)

# 2.2. topography
# ---------------
# Load terrain_50 DTM data from the terrain_50 database
# elevation = {get_dtm_values(key).items() for key in parcels['nat_grid_ref']}
# AAA: Make sure to create an index for x and y in the terrain_50.dtm.dtm_slope_elevation 
# table before running this otherwise it takes more than 8 hours to run!
elevation = {}
missing_data = []
counter = 1
tot_parcels = len(parcels)
for i in parcels['nat_grid_ref']:
    try:
        printProgressBar(counter, tot_parcels, prefix="Retrieving topographic data: ")
        a = get_dtm_values(i)
        elevation[i] = {'elevation':a['elevation'], 'slope':a['slope'], 'aspect':a['aspect']}
        counter += 1
    except:
        missing_data[i]
        continue

topography = pd.DataFrame.from_dict(elevation).transpose().reset_index()
topography.rename({'index': 'nat_grid_ref'}, axis=1, inplace=True)

parcel_data = parcels[['parcel_id', 'nat_grid_ref']]
parcel_data['parcel_id'] = parcel_data['parcel_id'].astype(int) # disregard the warning!
parcel_data = parcel_data.merge(topography, on='nat_grid_ref', how='left')
parcel_data = parcel_data[['parcel_id', 'elevation', 'slope', 'aspect']]

# Create record list from parcel_data dataframe
parcel_records = list(parcel_data.to_records(index=False))

# add records in bulk to parcels table
populate_table('topography', parcel_records)