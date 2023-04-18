import xarray as xr
from cropyields.db_manager import parcel2climcell
from cropyields.ChessScape_manager import filter_files 
from cropyields.utils import lonlat2OSgrid
import pandas as pd
import matplotlib.pyplot as plt
import nc_time_axis #required for matplotlib to interpret a 360 day calendar year

# Load the data
nc_path = 'D:\\Documents\\Data\\ClimateData\\nc_files\\'
rcp = 'rcp26'
year = [x for x in range(2020, 2081)]
                    
for file in prova:
    if file is prova[0]:
        nc_file = xr.open_dataset(file)
    else:
        nc_temp = xr.open_dataset(file)
        nc_file = xr.concat([nc_file, nc_temp], dim="time")

nc_file.to_netcdf(f'D:\\Documents\\Data\\ClimateData\\gb_{rcp}_{year}_{var}.nc')
spatial_tas = nc_file.isel(time=1)
t_tas = nc_file.isel(x=443, y=260)

plt.pcolor(spatial_tas['tas'])
plt.plot(t_tas['tas'])


df_sp_tas = spatial_tas['tas'].to_dataframe()
df = t_tas['tas'].to_dataframe()
df.index = pd.to_datetime(df.index)

plt.plot(df['tas'])

####################################################################################

# Sample parcels
parcels = [2585259, 2584502, 2582358]
climate_cells = parcel2climcell(parcels)
coords =[{'x':elem['x'], 'y':elem['y']} for elem in climate_cells]
lonlat = [{'lon':elem['lon'], 'lat':elem['lat']} for elem in climate_cells]

point = (lonlat[0]['lon'], lonlat[0]['lat'])
prova = lonlat2OSgrid(point, figs=4)

ensembles = '01'
rcps = ['rcp26']
# rechuncking netCDF files
for ensemble in ensembles:
    for rcp in rcps:
        df = pd.data
        for var in vars:
            file_list = filter_files(rcp=rcp, years=[x for x in range(2020, 2081)], vars=var, ensembles=ensemble)
            for file in file_list:


file_list = filter_files(rcp='rcp26', years=[x for x in range(2020, 2081)], vars='tas', ensembles='01')

for file in file_list:
    if file is file_list[0]:
        nc_file = xr.open_dataset(file)['tas']
        df = nc_file.where((nc_file.x==coords[0]['x']) & (nc_file.y==coords[0]['y']), drop=True).to_series()
        spatial_tas = df.isel(time=1)
        df_sp_tas = spatial_tas['tas'].to_dataframe()
    else:
        nc_temp = xr.open_dataset(file)
        nc_file = xr.concat([nc_file, nc_temp], dim="time")

prova = nc_file.transpose()

prova = nc_file.lon.to_dataframe().reset_index()
prova.where((prova['lat'] == lat[0]) & (prova.lon == lon[0]))
prova = nc_file.coords.to_dataset()
prova = nc_file["lon"].to_index()
print(nc_file.lon.attrs)

chunks = {'lat': float(lat[0]),
          'lon': float(lon[0])}
prova = nc_file.chunk(chunks)