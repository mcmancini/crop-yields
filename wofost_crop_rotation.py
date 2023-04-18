import pcse
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
from pcse.fileinput import ExcelWeatherDataProvider 
from pcse.db import NASAPowerWeatherDataProvider
from pcse.models import Wofost80_NWLP_FD_beta, Wofost71_WLP_FD

# RUN PCSE/WOFOST WITH CUSTOM INPUT DATA
# To do so, the models requires the following:
#   1) Model parameters: 
#       1.1. Crop specific parameters
#       1.2. Soil parameters
#       1.3. Site parameters
#   2) Driving variables:
#       2.1. Weather data
#       2.2. Agromanagement practices

# YAML CROP PARAMETERS
data_dir = 'D:\\Documents\\Data\\PCSE-WOFOST\\'
cropd = YAMLCropDataProvider(data_dir+'WOFOST_crop_parameters')
cropd.set_active_crop('wheat', 'Winter_wheat_101')


# SOIL PARAMETERS
soilfile = os.path.join(data_dir, 'pcse_examples\\ec3.soil')
soildata = CABOFileReader(soilfile)

# SITE PARAMETERS
sitedata = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)

parameters = ParameterProvider(cropdata=cropd, soildata=soildata, sitedata=sitedata)

# AGROMANAGEMENT
agromanagement_file = os.path.join(data_dir, 'pcse_examples\\rotation_calendar_hist.agro')
agromanagement = YAMLAgroManagementReader(agromanagement_file)

# WEATHER
wdp = NASAPowerWeatherDataProvider(latitude=52, longitude=5)

# Define simulation engine
wofsim = Wofost80_NWLP_FD_beta(parameters, wdp, agromanagement)
wofsim = Wofost71_WLP_FD(parameters, wdp, agromanagement)

# Run the model
wofsim.run_till_terminate()
output = wofsim.get_output()
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