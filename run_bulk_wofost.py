from pcse.fileinput import YAMLCropDataProvider
import os
from pcse.util import WOFOST80SiteDataProvider
from cropyields import db_parameters
import psycopg2
from cropyields.SoilManager import SoilGridsDataProvider, WHSDDataProvider
from cropyields.dataproviders import NetCDFWeatherDataProvider, SingleRotationAgroManager
from pcse.base import ParameterProvider
from pcse.models import Wofost71_WLP_FD
import pandas as pd
from cropyields.utils import printProgressBar

# INPUT PARAMETERS
rcp_list = ['rcp26']
year_list = [2020]
variety_list = ['Winter_wheat_101', 'Winter_wheat_102', 'Winter_wheat_103', 
                'Winter_wheat_104', 'Winter_wheat_105', 'Winter_wheat_106',
                'Winter_wheat_107']


for rcp in ['rcp26']:
    ensemble = 1
    soilsource = 'SoilGrids'

    # PATHS
    data_dir            = 'D:\\Documents\\Data\\PCSE-WOFOST\\'
    output_dir          = 'D:\\Documents\\Data\\PCSE-WOFOST\\WOFOST_output\\'
    agromanagement_file = os.path.join(data_dir, 'pcse_examples\\wwheat_oneyr.agro')
    crop_file           = data_dir+'WOFOST_crop_parameters'

    # CROP PARAMETERS
    cropd = YAMLCropDataProvider(crop_file)

    # SITE PARAMETERS
    sitedata = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)

    # PARCEL LIST
    conn = None    
    conn = psycopg2.connect(user=db_parameters['db_user'],
                            password=db_parameters['db_password'], 
                            database=db_parameters['db_name'], 
                            host='127.0.0.1', 
                            port= '5432')
    conn.autocommit = True
    cur = conn.cursor()
    sql = '''
        SELECT parcel_id, nat_grid_ref 
        FROM parcels;
        '''
    cur.execute(sql)
    t = cur.fetchall()
    parcel_list = [row[0] for row in t]
    parcel_os_code = [row[1] for row in t]
    if conn is not None:
        conn.close()

    # LOOP TO RUN WOFOST
    for variety in variety_list:
        cropd.set_active_crop('wheat', variety)
        for year in year_list:
            wheat_yields = {}
            failed_parcels = []
            counter = 1
            total = len(parcel_list)
            agromanagement = SingleRotationAgroManager(agromanagement_file)
            agromanagement.change_year(year)
            if agromanagement.retrieve_variety != variety:
                agromanagement.change_variety(variety)
            for parcel in parcel_os_code:
                printProgressBar(counter, total)
                parcel_yield = {}
                if soilsource == 'SoilGrids':
                    soildata = SoilGridsDataProvider(parcel)
                else:
                    soildata = WHSDDataProvider(parcel)
                try:
                    wdp = NetCDFWeatherDataProvider(parcel, rcp, ensemble, force_update=False)
                except:
                    print(f'failed to retrieve weather data for parcel at \'{parcel}\'')
                    failed_parcels.append(parcel)
                    continue
                parameters = ParameterProvider(cropdata=cropd, soildata=soildata, sitedata=sitedata)
                wofsim = Wofost71_WLP_FD(parameters, wdp, agromanagement)
                try:
                    wofsim.run_till_terminate()
                except:
                    print(f'failed to run the WOFOST crop yield model for parcel \'{parcel}\'')
                    failed_parcels.append(parcel)
                    continue
                output = wofsim.get_output()
                varnames = ["TWSO"]
                tmp = {}
                for var in varnames:
                    tmp[var] = [t[var] for t in output]
                # d = [len(tmp[x]) for x in varnames] 

                df = pd.DataFrame(output)
                df.set_index('day', inplace=True, drop=True)
                parcel_yield = {
                    "yield": df['TWSO'].max(),
                    "harvest_date": df['TWSO'].idxmax().strftime('%Y-%m-%d')
                }
                wheat_yields[parcel] = parcel_yield
                counter += 1

            df = pd.DataFrame(wheat_yields).T
            parcelset = df.index.to_list()
            # extract x values for subset of y values. Needed because of WOFOST failing for some of the parcels
            subset_x = [x for x, y in t if y in parcelset]
            df['parcel_id'] = subset_x
            df = df[['parcel_id', 'yield', 'harvest_date']]
            df.index.names = ['os_code']

            # Extract words and digits to create output file name
            char_list = variety.split('_')
            is_digits = [x.isdigit() for x in char_list]
            words = [word for word, is_digit in zip(char_list, is_digits) if not is_digit]
            digits = [word for word, is_digit in zip(char_list, is_digits) if is_digit]
            new_words = [word.capitalize() for word in words]
            var_name = ''.join(new_words) + '_' + digits[0]

            df.to_csv(output_dir + 'SouthHams_' + rcp + '_' + var_name + '_' + str(year) + '_' + soilsource + '.csv')
