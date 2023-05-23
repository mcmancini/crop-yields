'''
Rechunk_ChessScape
==================

Author: Mattia Mancini
Created: 01-November-2022
--------------------------

Chess-scape daily weather projections are organised for each RCP and ensemble,
in files containing a single climate variable for a one month time series for 
all 1km cells in GB.
This script rechunks the chess-scape netCDF files in two ways, based
on user input:
    1 - each chunk contains a 60 year daily time series of all climatic 
        variables for 100 cells contained in each 10km2 tile of the
        British National Grid. 
    2 - each chunk contains a 60 year daily time series of all climatic 
        variables for 10000 cells contained in each 100km2 tile of the
        British National Grid. 
The climate variables of interest are: 'tas', 'tasmax', 'tasmin', 'pr', 'rlds', 
'rsds', 'hurs', 'sfcWind', 'psurf'
More info on the variables and data in the CEDA archive:
https://catalogue.ceda.ac.uk/uuid/8194b416cbee482b89e0dfbe17c5786c
'''
import os
import xarray as xr
from cropyields import data_dirs
from cropyields.utils import osgrid2bbox, printProgressBar
from cropyields.ChessScape_manager import filter_files
import time
import multiprocessing

# OsRegions = ['SV', 'SW', 'SX', 'SY', 'SZ', 'TV',
#              'SR', 'SS', 'ST', 'SU', 'TQ', 'TR',
#              'SM', 'SN', 'SO', 'SP', 'TL', 'TM',
#              'SH', 'SJ', 'SK', 'TF', 'TG', 'SC',
#              'SD', 'SE', 'TA', 'NW', 'NX', 'NY',
#              'NZ', 'OV', 'NR', 'NS', 'NT', 'NU',
#              'NL', 'NM', 'NN', 'NO', 'NP', 'NF',
#              'NG', 'NH', 'NJ', 'NK', 'NA', 'NB',
#              'NC', 'ND', 'NE', 'HW', 'HX', 'HY',
#              'HZ', 'HT', 'HU', 'HO', 'HP']

# OS British National Grid tiles
# OsCells = [f'{number:02d}'for number in range(100)]
# OsGrid = [x + num for num in OsCells for x in OsRegions]

def rechunk_ChessScape(OsCell):
    nc_path = data_dirs['ceda_dir']
    out_path = data_dirs['OSGB_dir']
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    # nc data parameters
    rcp = 'rcp85'
    years = [x for x in range(2020, 2081)]
    vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']
    # vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind', 'psurf']
    ensemble = '01'
    t = time.time()
    bbox = osgrid2bbox(OsCell, '10km')
    # initialise empty xr dataset
    os_chunk = xr.Dataset()

    # loop through vars and files for each var (i.e. months)
    print(f'Processing cell \'{OsCell}\' ...')
    for var in vars:
        counter = 1
        file_list = filter_files(rcp, years, var, ensemble)
        list_length = len(file_list)
        printProgressBar(0, list_length, prefix = f'{var}:', suffix = 'Complete', length = 50)
        for file in file_list:
            printProgressBar(counter, list_length, prefix = f'{var}:', suffix = 'Complete', length = 50)
            counter += 1
            try:
                nc_file = xr.open_dataset(file)[var]
                if file is file_list[0]:
                    cell_data = nc_file.where((nc_file.x >= bbox['xmin']) & 
                        (nc_file.x < bbox['xmax']) &
                        (nc_file.y >= bbox['ymin']) &
                        (nc_file.y < bbox['ymax']), drop=True)
                else:
                    df = nc_file.where((nc_file.x >= bbox['xmin']) & 
                        (nc_file.x < bbox['xmax']) &
                        (nc_file.y >= bbox['ymin']) &
                        (nc_file.y < bbox['ymax']), drop=True)
                    cell_data = xr.concat([cell_data, df], dim='time')
            except:
                # print(f'Cannot open file \'{file}\'. Skipping...')
                continue 
        
        # Add xr.DataArray for specified var to Dataset
        os_chunk[var] = cell_data

    # Sum longwave and shortwave downward surface radiation to total surface radiation
    os_chunk['rds'] = os_chunk['rlds'] + os_chunk['rsds']

    # Save on disk
    tot_time = time.time() - t
    print(f'OS cell \'{OsCell}\' processed in {tot_time:.2f} seconds\n')
    os_chunk.to_netcdf(out_path+f'{OsCell}_{rcp}_{ensemble}.nc')


if __name__ == "__main__":

    OsGrid = ["SX73", "SX78", "SX89", "SX60", "SX79", "SX51", 
            "SX77", "SX75", "SX56", "SX83", "SX61", "SX70", 
            "SX54", "SX72", "SX87", "SX67", "SX65", "SX71", 
            "SX69", "SX81", "SX50", "SX85", "SX57", "SX84", 
            "SX66", "SX59", "SX88", "SX80", "SX91", "SX74", 
            "SX58", "SX55", "SX82", "SX76", "SX90", "SX68", 
            "SX92", "SX53", "SX86", "SX63", "SX62", "SX52", 
            "SX64", "SX49", "SX46", "SX94", "SX44", "SX95", 
            "SX45"]
    
    pool = multiprocessing.Pool(processes=16)

    # Use the pool.map() function to parallelize the loop
    results = pool.map(rechunk_ChessScape, OsGrid)

    # Close the pool to indicate that no more tasks will be submitted
    pool.close()

    # Wait for all processes to complete
    pool.join()
    