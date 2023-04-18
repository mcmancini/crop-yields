import pcse
import pandas as pd
import os
import matplotlib.pyplot as plt
from pcse.fileinput import YAMLCropDataProvider
from pcse.fileinput import CABOFileReader
from pcse.util import WOFOST71SiteDataProvider
from pcse.base import ParameterProvider
from pcse.fileinput import YAMLAgroManagementReader
from pcse.fileinput import ExcelWeatherDataProvider 
from pcse.db import NASAPowerWeatherDataProvider
from pcse.models import Wofost80_NWLP_FD_beta, Wofost71_WLP_FD

# TEST RUN: SOUTH SPAIN, WINTER WHEAT, YEAR 2000 AND WATER-LIMITED CONDITIONS FOR A
# FREELY DRAINING SOIL (WLP) 
wofost_object = pcse.start_wofost(grid=31031, crop=1, year=2000, mode='wlp')
type(wofost_object)
wofost_object.run()
wofost_object.get_variable('LAI')
wofost_object.run(days=25)

wofost_object.run_till_terminate()
output = wofost_object.get_output()
df = pd.DataFrame(output)
df.head()

summary_output = wofost_object.get_summary_output()
msg = "Reached maturity at {DOM} with total biomass {TAGP} kg/ha "\
"and a yield of {TWSO} kg/ha."

print(msg.format(**summary_output[0]))

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
cropd.print_crops_varieties()
cropd.set_active_crop('sugarbeet', 'Sugarbeet_601')
print(cropd)


# Crop parameters
# cropfile = os.path.join(data_dir, 'pcse_examples\\sug0601.crop')
# cropdata = CABOFileReader(cropfile)
# print(cropdata)

# Soil parameters
soilfile = os.path.join(data_dir, 'pcse_examples\\ec3.soil')
soildata = CABOFileReader(soilfile)
print(soildata)

# Site parameters
sitedata = WOFOST71SiteDataProvider(WAV=100, CO2=360)
print(sitedata)

parameters = ParameterProvider(cropdata=cropd, soildata=soildata, sitedata=sitedata)

# Agromanagement
agromanagement_file = os.path.join(data_dir, 'pcse_examples\\sugarbeet_calendar.agro')
# agromanagement_file = os.path.join(data_dir, 'pcse_examples\\rotation_calendar.agro')
agromanagement = YAMLAgroManagementReader(agromanagement_file)
print(agromanagement)

a = agromanagement[:]
key_list = [list(x.keys())[0] for x in a]

agromanagement[0][key_list[0]]['CropCalendar']['crop_name'] = 'sugarbeet'
agromanagement[0][key_list[0]]['CropCalendar']['variety_name'] = 'Sugarbeet_601'
agromanagement[1][key_list[1]]['CropCalendar']['crop_name'] = 'sugarbeet'
agromanagement[1][key_list[1]]['CropCalendar']['variety_name'] = 'Sugarbeet_601'

# Daily weather observations
wdp = NASAPowerWeatherDataProvider(latitude=52, longitude=5)
print(wdp)
from datetime import date
day = date(2006,7,3)
wdc = wdp(day)
print(wdc)
wdc2 = wdp('20060704')
print(wdc2)

# Weather data from excel (there is also a CSVWeatherDataProvider in pcse.fileinput)
weather_path = os.path.join(data_dir, 'pcse_examples\\nl1.xlsx')
wdp = ExcelWeatherDataProvider(weather_path)

# Define simulation engine
# wofsim = Wofost80_NWLP_FD_beta(parameters, wdp, agromanagement)
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