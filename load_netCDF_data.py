from cropyields.ChessScape_manager import filter_files
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import nc_time_axis #required for matplotlib to interpret a 360 day calendar year


# Load the data
rcp = 'rcp26'
year = 2020
var = 'tas'
prova = filter_files(rcp=rcp, years=year, vars=var)

                    
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


cube = iris.load_cube(data_folder + 'chess-scape_rcp45_bias-corrected_01_tas_uk_1km_daily_20200101-20200130.nc')