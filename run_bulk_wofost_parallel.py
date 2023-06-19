from pcse.fileinput import YAMLCropDataProvider
import os
from pcse.util import WOFOST80SiteDataProvider
from cropyields import db_parameters
import psycopg2
from cropyields.SoilManager import SoilGridsDataProvider, WHSDDataProvider
from cropyields.WeatherManager import NetCDFWeatherDataProvider
from cropyields.CropManager import SingleRotationAgroManager
from pcse.base import ParameterProvider
from pcse.models import Wofost71_WLP_FD
import pandas as pd
import multiprocessing
import logging


def run_wofost(args):
    parcel, arg_dict, results_dict = args
    year = arg_dict['year']
    soilsource = arg_dict['soilsource']
    agromanagement = arg_dict['agromanagement']
    rcp = arg_dict['rcp']
    ensemble = arg_dict['ensemble']
    cropd = arg_dict['cropd']
    sitedata = arg_dict['sitedata']
    
    agromanagement.change_year(year)
    parcel_yield = {}
    print(f'Running WOFOST for parcel \'{parcel}\'')
    if soilsource == 'SoilGrids':
        soildata = SoilGridsDataProvider(parcel)
    else:
        soildata = WHSDDataProvider(parcel)
    try:
        wdp = NetCDFWeatherDataProvider(parcel, rcp, ensemble, force_update=False)
    except:
        print(f'failed to retrieve weather data for parcel at \'{parcel}\'')
    parameters = ParameterProvider(cropdata=cropd, soildata=soildata, sitedata=sitedata)
    wofsim = Wofost71_WLP_FD(parameters, wdp, agromanagement)
    try:
        wofsim.run_till_terminate()
    except:
        print(f'failed to run the WOFOST crop yield model for parcel \'{parcel}\'')
    output = wofsim.get_output()
    varnames = ["TWSO"]
    tmp = {}
    for var in varnames:
        tmp[var] = [t[var] for t in output]

    df = pd.DataFrame(output)
    df.set_index('day', inplace=True, drop=True)
    parcel_yield = {
        "yield": df['TWSO'].max(),
        "harvest_date": df['TWSO'].idxmax().strftime('%Y-%m-%d')
    }
    results_dict[parcel] = parcel_yield



if __name__ == "__main__":

    logging.disable(logging.CRITICAL) # this does not work
    # INPUT PARAMETERS
    input_params = {}
    input_params['year']       = 2020
    input_params['rcp']        = 'rcp26'
    input_params['ensemble']   = 1
    input_params['soilsource'] = 'SoilGrids'

    # PATHS
    data_dir            = 'D:\\Documents\\Data\\PCSE-WOFOST\\'
    agromanagement_file = os.path.join(data_dir, 'pcse_examples\\wwheat_oneyr.agro')
    crop_file           = data_dir+'WOFOST_crop_parameters'

    # CROP PARAMETERS
    cropd = YAMLCropDataProvider(crop_file)
    variety = 'Winter_wheat_101'
    cropd.set_active_crop('wheat', variety)
    input_params['cropd'] = cropd

    # SITE PARAMETERS
    input_params['sitedata'] = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)

    # AGROMANAGEMENT
    input_params['agromanagement'] = SingleRotationAgroManager(agromanagement_file)

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
    
    # start parallel pool
    pool = multiprocessing.Pool(processes=2)
    
    # Create an empty dictionary to store the results
    results_dict = multiprocessing.Manager().dict()

    # Prepare arguments for the run_wofost function
    args = [(item, input_params, results_dict) for item in parcel_os_code]

    pool.map(run_wofost, args)
    pool.close()
    pool.join()

    df = pd.DataFrame(results_dict).T
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

    df.to_csv(data_dir + 'SouthHams_' + input_params['rcp'] + '_' + str(input_params['ensemble']) + '_' + var_name + '_' + str(input_params['year']) + '.csv')


