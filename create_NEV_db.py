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
from cropyields.db_manager import create_db, create_db_tables, drop_db, populate_table, get_dtm_values
import geopandas as gpd
import time
import numpy as np
import codecs
import pandas as pd
from cropyields.utils import lonlat2osgrid
from soilgrids import SoilGrids
from soilgrids import BmiSoilGrids

# 1) Create new database and relations
# ====================================
create_db()
create_db_tables()
# drop_db()

import sys, importlib
importlib.reload(sys.modules['nev.db_manager'])
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
parcel_data = parcels[['parcel_id', 'farm_id', 'nat_grid_ref']]
parcel_data['parcel_id'] = parcel_data['parcel_id'].astype(int)

# Create record list from parcel_data dataframe
parcel_records = list(parcel_data.to_records(index=False))

# add records in bulk to parcels table
populate_table('parcels', parcel_records)

# 2.2. topography
# ---------------
# Load terrain_50 DTM data from the terrain_50 database
# elevation = {get_dtm_values(key).items() for key in parcels['nat_grid_ref']}
# AAA: this takes a long time (8 hours or more) because the SQL query statement 
# runs very slow
elevation = {}
missing_data = {}
counter = 1
tot_parcels = len(parcels)
for i in parcels['nat_grid_ref']:
    try:
        print(f'Processing OS grid {counter} of {tot_parcels}')
        a = get_dtm_values(i)
        elevation[i] = {'elevation':a['elevation'], 'slope':a['slope'], 'aspect':a['aspect']}
        counter += 1
    except:
        print(f'no elevation data for cell \'{i}\'. Continuing...')
        missing_data[i]
        continue

topography = pd.DataFrame.from_dict(elevation).transpose().reset_index()
topography.rename({'index': 'nat_grid_ref'}, axis=1, inplace=True)

parcel_data = parcels[['parcel_id', 'farm_id', 'nat_grid_ref']]
parcel_data['parcel_id'] = parcel_data['parcel_id'].astype(int) # disregard the warning!
parcel_data = parcel_data.merge(topography, on='nat_grid_ref', how='left')
parcel_data = parcel_data[['parcel_id', 'elevation', 'slope', 'aspect']]

# Create record list from parcel_data dataframe
parcel_records = list(parcel_data.to_records(index=False))

# add records in bulk to parcels table
populate_table('parcels', parcel_records)

# 2.3. soil
# ---------
# This comes from the SoilGrids dataset (https://www.isric.org/explore/soilgrids)
# using the soilgrids 0.1.3 library (https://pypi.org/project/soilgrids/)
from pyproj import Transformer
transformer = Transformer.from_crs(4326, 27700, always_xy=True)
x1, y1 = transformer.transform(-2.547855,54.00366) #centroid of Great Britain
west, east, south, north = x1 - 0.5e6, x1 + 0.5e6, y1 - 0.8e6, y1 + 0.8e6
transformer = Transformer.from_crs(27700, 4326, always_xy=True)
bl = transformer.transform(west, south)
br = transformer.transform(east, south)
tl = transformer.transform(west, north)
tr = transformer.transform(east, north)
soil_grids = SoilGrids()
data = soil_grids.get_coverage_data(service_id='phh2o', coverage_id='phh2o_0-5cm_mean',
                                       west=bl[0], south=bl[1], east=br[0], north=tr[1],
                                       width=100, height=100,
                                       crs='urn:ogc:def:crs:EPSG::4326', output='test.tif')



# show metadata
for key, value in soil_grids.metadata.items():
    print('{}: {}'.format(key,value))

import matplotlib.pyplot as plt
data.plot(figsize=(9,5))
plt.title('Mean pH between 0 and 5 cm soil depth in GB')
plt.show()

# initiate a data component
data_comp = BmiSoilGrids()
data_comp.initialize('config_file.yaml')

# get variable info
var_name = data_comp.get_output_var_names()[0]
var_unit = data_comp.get_var_units(var_name)
var_location = data_comp.get_var_location(var_name)
var_type = data_comp.get_var_type(var_name)
var_grid = data_comp.get_var_grid(var_name)
print('variable_name: {} \nvar_unit: {} \nvar_location: {} \nvar_type: {} \nvar_grid: {}'.format(
    var_name, var_unit, var_location, var_type, var_grid))

# get variable grid info
grid_rank = data_comp.get_grid_rank(var_grid)

grid_size = data_comp.get_grid_size(var_grid)

grid_shape = np.empty(grid_rank, int)
data_comp.get_grid_shape(var_grid, grid_shape)

grid_spacing = np.empty(grid_rank)
data_comp.get_grid_spacing(var_grid, grid_spacing)

grid_origin = np.empty(grid_rank)
data_comp.get_grid_origin(var_grid, grid_origin)

print('grid_rank: {} \ngrid_size: {} \ngrid_shape: {} \ngrid_spacing: {} \ngrid_origin: {}'.format(
    grid_rank, grid_size, grid_shape, grid_spacing, grid_origin))

# get variable data
data = np.empty(grid_size, var_type)
data_comp.get_value(var_name, data)
data_2D = data.reshape(grid_shape)

# get X, Y extent for plot
min_y, min_x = grid_origin
max_y = min_y + grid_spacing[0]*(grid_shape[0]-1)
max_x = min_x + grid_spacing[1]*(grid_shape[1]-1)
dy = grid_spacing[0]/2
dx = grid_spacing[1]/2
extent = [min_x - dx, max_x + dx, min_y - dy, max_y + dy]

