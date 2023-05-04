'''
SoilGrids data downloader.
==========================

Author: Mattia Mancini
Created: 24-April-2023
--------------------------

Script that downloads and stores soil data retrieved from the SoilGrids dataset.
This needs to be run in the setup of the farm model. (see readme)
This is a system for global digital soil mapping that uses state-of-the-art machine 
learning methods to map the spatial distribution of soil properties across the 
globe. SoilGrids prediction models are fitted using over 230 000 soil profile 
observations from the WoSIS database and a series of environmental covariates. 
Covariates were selected from a pool of over 400 environmental layers from Earth 
observation derived products and other environmental information including climate, 
land cover and terrain morphology. The outputs of SoilGrids are global soil property 
maps at six standard depth intervals (according to the GlobalSoilMap IUSS working 
group and its specifications) at a spatial resolution of 250 meters.

The SoilGrids dataset can be found at https://www.isric.org/explore/soilgrids;
it was downloaded using the soilgrids 0.1.3 library (https://pypi.org/project/soilgrids/)
Docs at https://www.isric.org/explore/soilgrids/faq-soilgrids and
https://maps.isric.org/

Soil data from SoilGrids requires
to be processed as follows:
    - 1. Compute depth weighted averages of all values: the raw data is
            reported by depth, but we want averages for 0-60cm.
    - 2. Rescale values based on the conversion factors reported at
            https://www.isric.org/explore/soilgrids/faq-soilgrids
'''
import os
from cropyields import data_dirs
from pyproj import Transformer
from soilgrids import SoilGrids
import xarray as xr
import time
import numpy as np

# Conversion functions
NoConversion = lambda x: x
mult_hundred = lambda x: x*100.
mult_ten     = lambda x: x*10.
div_ten      = lambda x: x/10.
div_hundred  = lambda x: x/100.

# Conversion by soil parameter (see https://www.isric.org/explore/soilgrids/faq-soilgrids)
obs_conversions = {
        "bdod": mult_hundred,
        "cec": div_ten,
        "cfvo": div_ten,
        "clay": div_ten,
        "nitrogen": div_hundred,
        "phh2o": div_ten,
        "sand": div_ten,
        "silt": div_ten,
        "soc": div_ten,
        "ocd": div_ten,
        "ocs": mult_ten
    }

if not os.path.isdir(data_dirs['soils_dir']):
    os.makedirs(data_dirs['soils_dir'])

transformer = Transformer.from_crs(4326, 27700, always_xy=True)
x1, y1 = transformer.transform(-2.547855,54.00366) #centroid of Great Britain
west, east, south, north = x1 - 0.5e6, x1 + 0.5e6, y1 - 0.8e6, y1 + 0.8e6
transformer = Transformer.from_crs(27700, 4326, always_xy=True)
bl = transformer.transform(west, south)
br = transformer.transform(east, south)
tl = transformer.transform(west, north)
tr = transformer.transform(east, north)

soilvars = ['bdod', 'cec', 'cfvo', 'clay', 'nitrogen', 'phh2o', 'sand', 'silt', 'soc', 'ocd', 'ocs']
soil_depths = ['0-5', '5-15', '15-30', '30-60', '60-100', '100-200']
soil_grids = SoilGrids()
counter = 1
soil_data = xr.Dataset()
for var in soilvars:
    print(f'Processing variable {counter} of {len(soilvars)}: \'{var}\'')
    soil_chunk = xr.Dataset()
    if var == 'ocs':
        while True: # required because the server sometimes returns a 500 error
            depth='0-30'
            try:
                soil_data[var] = soil_grids.get_coverage_data(service_id=var, coverage_id=f'{var}_{depth}cm_mean',
                                            west=bl[0], south=bl[1], east=br[0], north=tr[1],
                                            width=4000, height=6400,
                                            crs='urn:ogc:def:crs:EPSG::4326', output=(data_dirs['soils_dir']+'tmp.tif'))
                # conversion to conventional units
                func = obs_conversions[var]
                soil_data[var] = func(soil_data[var])
            except:
                print("get_coverage_data failed. Retrying in 60 seconds...")
                time.sleep(60)
                continue
            break
    else:
        for depth in soil_depths:
            while True:
                try:
                    soil_chunk[depth] = soil_grids.get_coverage_data(service_id=var, coverage_id=f'{var}_{depth}cm_mean',
                                                west=bl[0], south=bl[1], east=br[0], north=tr[1],
                                                width=4000, height=6400,
                                                crs='urn:ogc:def:crs:EPSG::4326', output=(data_dirs['soils_dir']+'tmp.tif'))
                    # conversion to conventional units
                    func = obs_conversions[var]
                    soil_chunk[depth] = func(soil_chunk[depth])
                except:
                    print("get_coverage_data failed. Retrying in 60 seconds...")
                    time.sleep(60)
                    continue
                break
    
        # soil_chunk.to_netcdf(data_dirs['soils_dir'] + f'soil_{var}.nc')
        # Weighted average of soil variables for depths up to 60cm
        weight_factor = {
            '0-5': 1,
            '5-15': 2,
            '15-30': 3,
            '30-60': 6
        }
        # empty array to store the weighted average. Can't be an empty object
        # (i.e. xr.DataArray()) because dimensions cannot change for in-place operations
        soil_data[var] = soil_chunk[depth] * 0 

        for key in weight_factor.keys():
            df = soil_chunk[key] * weight_factor[key]
            soil_data[var] += df
        soil_data[var] = soil_data[var] / 12
        soil_data[var] = soil_data[var].where(soil_data[var] != 0, np.nan)
        counter += 1
        time.sleep(60)

soil_data.to_netcdf(data_dirs['soils_dir'] + 'GB_soil_data.nc')

# # show metadata
# for key, value in soil_grids.metadata.items():
#     print('{}: {}'.format(key,value))

# # plot soil data
# import matplotlib.pyplot as plt
# soil_chunk['0-30'].plot(figsize=(9,5))
# plt.title('Mean pH between 0 and 5 cm soil depth in GB')
# plt.show()