import netCDF4
import numpy as np
import xarray as xr

data_folder = 'D:\\Documents\\Data\\ClimateData\\nc_files\\'

f = netCDF4.Dataset(data_folder + 'chess-scape_rcp45_bias-corrected_01_tas_uk_1km_daily_20200101-20200130.nc')
print(f.variables.keys())
print(f.variables['tas'])
for d in f.dimensions.items():
    print(d)

tas = f.variables['tas']
tas.dimensions
tas.shape

crs = f.variables['crsOSGB']
lat, lon = f.variables['lat'], f.variables['lon']

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
cs = plt.pcolor(tas[1,:,:])

tas = xr.open_dataset(data_folder + 'chess-scape_rcp45_bias-corrected_01_tas_uk_1km_daily_20200101-20200130.nc')


airtemps = xr.tutorial.open_dataset("air_temperature")
air = airtemps.air - 273.15
air.attrs = airtemps.air.attrs
air.attrs["units"] = "deg C"

air1d = air.isel(lat=10, lon=10)
air1d.plot()
airtemps.air.isel(time=0).plot()

import pandas as pd
da = xr.DataArray(
    np.random.rand(4, 3),
    [
        ("time", pd.date_range("2000-01-01", periods=4)),
        ("space", ["IA", "IL", "IN"]),
    ],
)

prova = tas.isel(time=1)
df = prova['tas'].to_dataframe()
