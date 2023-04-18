import netCDF4
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from cropyields.utils import find_closest_climcell_ID
import time


# open a file with the spatial grid of the chess-scape data
nc_path = 'D:\\Documents\\Data\\ClimateData\\'
clim_data = netCDF4.Dataset(nc_path + 'gb_rcp26_2020_tas.nc')
clim_data = xr.open_dataset(nc_path + 'gb_rcp26_2020_tas.nc')

# open shapefile of parcels
shp_path = 'D:\\Documents\\Data\\PCSE-WOFOST\\south_hams_arable\\'
parcels = gpd.read_file(shp_path + 'south_hams_arable_fields.shp')

# Get the centroids, and create the indexers for the DataArray:
centroids = parcels.centroid.to_crs("EPSG:27700")
x_indexer = xr.DataArray(centroids.x, dims=["point"])
y_indexer = xr.DataArray(centroids.y, dims=["point"])

# Grab the results:
df = clim_data.sel(x=x_indexer, y=y_indexer, method="nearest")
# spatial_df = df.isel(time=1)['tas']
t_df = df.isel(point=350)['tas']
# plt.pcolor(spatial_df)
plt.plot(t_df)
plt.show()


prova = clim_data.isel(time=0)['tas']
prova = prova.to_dataframe()
prova = prova.reset_index()
prova = prova.dropna()
## =====================================================================

# open shapefile of parcels
shp_path = 'D:\\Documents\\Data\\PCSE-WOFOST\\south_hams_arable\\'
parcels = gpd.read_file(shp_path + 'south_hams_arable_fields.shp')
parcels.rename({'oid':'parcel_id', 'custid': 'farm_id', 'full_parce': 'nat_grid_ref'}, axis=1, inplace=True)

# find centroids of parcels
centroids = gpd.GeoSeries(parcels.centroid.to_crs("EPSG:27700"))

# open a file with the spatial grid of the chess-scape data
nc_path = 'D:\\Documents\\Data\\ClimateData\\'
clim_data = xr.open_dataset(nc_path + 'gb_rcp26_2020_tas.nc').isel(time=0)['tas']
clim_df = clim_data.to_dataframe().reset_index().dropna()
clim_df['cell_id'] = range(clim_df.shape[0])
clim_df.reset_index(drop=True, inplace=True)
clim_df.set_index(['cell_id'], inplace=True, drop=True)

from shapely.geometry import Point
clim_pts = [Point(clim_df['lon'].iloc[x], clim_df['lat'].iloc[x]) for x in range(clim_df.shape[0])]
clim_points = gpd.GeoSeries(clim_pts, crs="OSGB1936").to_crs("EPSG:27700")

# find distance matrix between centroids of parcels and climate cells
# start = time.process_time()
# dst = centroids.geometry.apply(lambda g: clim_points.distance(g)) # too slow!!!! 254 cells in 88 minutes
# print(time.process_time() - start)

def which_min(parcel_centroid, climate_cells):
    dst = [parcel_centroid.distance(climate_cells.values[ind]) for ind in range(climate_cells.shape[0])]
    (val,idx) = min((val,idx) for idx,val in enumerate(dst))
    return idx

# from joblib import Parallel, delayed
# t = time.time()
# results = Parallel(n_jobs=18)(delayed(which_min)(centroids.values[x], clim_points) for x in range(40))
# print(results)
# print(time.time() - t)

# method 1
t = time.time()
closest_cells = []
for i in range(40):
    print(f'finding nearest neighbour of parcel {i}')
    closest = which_min(centroids.values[i], clim_points)
    closest_cells.append(closest)
print(time.time() - t)
parcels['climate_cell'] = closest_cells

# method 2
t = time.time()
closest_cells = []
for i in range(40):
    print(f'finding nearest neighbour of parcel {i}')
    ctr_x, ctr_y= centroids[i].x, centroids[i].y
    clim_subset = clim_points.cx[ctr_x - 1000:ctr_x + 1000, ctr_y - 1000:ctr_y + 1000]
    closest = which_min(centroids.values[i], clim_subset)
    closest_cells.append(closest)
print(time.time() - t)
parcels['climate_cell'] = closest_cells

# method 3
closest_cells = []
t = time.time()
pts = centroids[0:40]
import multiprocessing
with multiprocessing.Pool() as pool:
    result = [pool.apply(find_closest_climcell_ID, args=(pts.values[x], clim_points)) for x in range(len(pts))]
print(time.time() - t)
pool.close()

# to parallelise: ray or xarray dask
