'''
CREATE NEV 2.0 SQL DATABASE
===========================

Author: Mattia Mancini
Created: 20-September-2022
--------------------------

Create a postgreSQL database containing the data for the NEV 2.0
farm model. It contains spatial data on parcels and farms, as well
as the Chess-Scape climate projections on a 1 km x 1 km grid in GB 
on a daily basis from 2020 to 2080. 
- The following RCPs are included: 'rcp26', 'rcp45', 'rcp60', 'rcp85'
- The following variables are included: 'tas', 'tasmax', 'tasmin', 'pr', 
'rlds', 'rsds', 'hurs', 'sfcWind'
- A year is defined as 12 months of 30 days each

Farm data includes parcels, farm ID, a reference to the National
Grid cell and a reference the ID of the 1km x 1km climate
cell where each parcel falls. 

'''
from cropyields.db_manager import create_db, create_db_tables, drop_db, populate_table
from cropyields.utils import  lonlat2osgrid
import xarray as xr
import geopandas as gpd
from shapely.geometry import Point
import time

# 1) Create new database and relations
# ====================================
create_db()
create_db_tables()
# drop_db()

# 2) Populate the database
# ========================

# 2.1. climate_cells
# ------------------
# # open a file with the spatial grid of the chess-scape data
nc_path = 'D:\\Documents\\Data\\ClimateData\\'
clim_data = xr.open_dataset(nc_path + 'gb_rcp26_2020_tas.nc').isel(time=0)['tas']

# prepare the records to insert into the climate_cells table (chess-scape cells)
clim_df = clim_data.to_dataframe().reset_index().dropna()
clim_df['cell_id'] = range(clim_df.shape[0])
clim_df.reset_index(drop=True, inplace=True)
clim_df.set_index(['cell_id'], inplace=True, drop=True)
data = clim_df[['x', 'y', 'lon', 'lat']].reset_index()
data.rename(columns={'cell_id': 'climate_cell'}, inplace=True)
x = list(data['lon'])
y = list(data['lat'])
t = time.time()
data['natgrid_ref'] = [lonlat2osgrid(coords, figs=4) for coords in zip(x, y)] # It takes a long time: 19231s
print(time.time() - t)
records = list(data.to_records(index=False))


# add records in bulk to climate_cells table
populate_table('climate_cells', records)

# 2.2. parcels
# ------------

# open shapefile of parcels
shp_path = 'D:\\Documents\\Data\\PCSE-WOFOST\\south_hams_arable\\'
parcels = gpd.read_file(shp_path + 'south_hams_arable_fields.shp')
parcels.rename({'oid':'parcel_id', 'custid': 'farm_id', 'full_parce': 'nat_grid_ref'}, axis=1, inplace=True)

# find centroids of parcels
centroids = gpd.GeoSeries(parcels.centroid.to_crs("EPSG:27700"))

# create geoseries of centroids of climate_cells
clim_pts = [Point(clim_df['lon'].iloc[x], clim_df['lat'].iloc[x]) for x in range(clim_df.shape[0])]
clim_points = gpd.GeoSeries(clim_pts, crs="OSGB1936").to_crs("EPSG:27700")

# find closest climate_cell to the centroid of each parcel
def which_min(parcel_centroid, climate_cells):
    dst = [parcel_centroid.distance(climate_cells.values[ind]) for ind in range(climate_cells.shape[0])]
    (val,idx) = min((val,idx) for idx,val in enumerate(dst))
    return climate_cells.index[idx] 

t = time.time()
closest_cells = []
for i in range(len(centroids)):
    print(f'finding nearest neighbour of parcel {i}')
    ctr_x, ctr_y= centroids[i].x, centroids[i].y
    clim_subset = clim_points.cx[ctr_x - 1000:ctr_x + 1000, ctr_y - 1000:ctr_y + 1000]
    closest = which_min(centroids.values[i], clim_subset)
    closest_cells.append(closest)
print(time.time() - t)

parcels['climate_cell'] = closest_cells
parcel_data = parcels[['parcel_id', 'farm_id', 'nat_grid_ref', 'climate_cell']]
parcel_data['parcel_id'] = parcel_data['parcel_id'].astype(int) # disregard the warning!
parcel_records = list(parcel_data.to_records(index=False))

# add records in bulk to parcels table
populate_table('parcels', parcel_records)
