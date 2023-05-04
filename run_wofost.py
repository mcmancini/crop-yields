from cropyields.dataproviders import NetCDFWeatherDataProvider
from pcse.db import NASAPowerWeatherDataProvider
from datetime import date
import pandas as pd
import os
import matplotlib.pyplot as plt
from pcse.fileinput import YAMLCropDataProvider
from pcse.fileinput import CABOFileReader
from pcse.util import WOFOST71SiteDataProvider
from pcse.util import WOFOST80SiteDataProvider
from pcse.base import ParameterProvider
from pcse.fileinput import YAMLAgroManagementReader
from datetime import date
from pcse.models import Wofost80_NWLP_FD_beta, Wofost71_WLP_FD
from cropyields.SoilManager import SoilGridsDataProvider

# LOCATION
osgrid_code = 'SX5941249334'

# YAML CROP PARAMETERS
data_dir = 'D:\\Documents\\Data\\PCSE-WOFOST\\'
cropd = YAMLCropDataProvider(data_dir+'WOFOST_crop_parameters')
# cropd.set_active_crop('wheat', 'Winter_wheat_101')
cropd.set_active_crop('wheat', 'Winter_wheat_101')

# SOIL PARAMETERS
# soilfile = os.path.join(data_dir, 'pcse_examples\\ec3.soil')
# soildata = CABOFileReader(soilfile)
soildata = SoilGridsDataProvider(osgrid_code)

# SITE PARAMETERS
sitedata = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)

parameters = ParameterProvider(cropdata=cropd, soildata=soildata, sitedata=sitedata)

# AGROMANAGEMENT
agromanagement_file = os.path.join(data_dir, 'pcse_examples\\winter_wheat_oneyr.agro')
agromanagement = YAMLAgroManagementReader(agromanagement_file)

# WEATHER
rcp = 'rcp26'
ensemble = 1
wdp = NetCDFWeatherDataProvider(osgrid_code, rcp, ensemble, force_update=False)
# wdp_2 = NASAPowerWeatherDataProvider(latitude=50.309, longitude=-3.785)
day = date(2022, 8, 31)
print(wdp(day))

# df_1 = pd.DataFrame(wdp_1.export())
# df_2 = pd.DataFrame(wdp_2.export())

# a = df_1[df_1['DAY'] < date(2021, 1, 1)]
# b = df_1[df_1['DAY'].between(date(2022, 1, 1), date(2022, 12, 31))]
# c = df_1[df_1['DAY'].between(date(2023, 1, 1), date(2023, 12, 31))]


# Define simulation engine
# wofsim = Wofost80_NWLP_FD_beta(parameters, wdp, agromanagement)
wofsim = Wofost71_WLP_FD(parameters, wdp, agromanagement)

# Run the model
wofsim.run_till_terminate()
output = wofsim.get_output()
summary_output = wofsim.get_summary_output()
len(output)

# Collect output
varnames = ["day", "DVS", "TAGP", "LAI", "TWSO"]
tmp = {}
for var in varnames:
    tmp[var] = [t[var] for t in output]

d = [len(tmp[x]) for x in varnames] 

df = pd.DataFrame(output)
df.set_index('day', inplace=True, drop=True)
start_date = date(2000, 5, 4)
df = df[df.index >= start_date]

# Plot
day = tmp.pop("day")
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10,8))
for var, ax in zip(["DVS", "TAGP", "LAI", "TWSO"], axes.flatten()):
    ax.plot_date(day, tmp[var], 'b-')
    ax.set_title(var)
fig.autofmt_xdate()
plt.show()