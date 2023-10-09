# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), November 2022
# ========================================================
'''
Rechunk_ChessScape
==================
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
import multiprocessing
import os
import time
import xarray as xr
from cropyields import data_dirs
from cropyields.utils import osgrid2bbox, printProgressBar
from cropyields.ChessScape_manager import filter_files

def rechunk_ChessScape(OsCell):
    """
    Take netcdf files containing the ChessScape climate data and rechunk
    them to be in the format required for the Wofost crop yield model
    """
    nc_path = data_dirs['ceda_dir']
    out_path = data_dirs['OSGB_dir']
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    # nc data parameters
    rcp = 'rcp85'
    years = [x for x in range(2020, 2081)]
    climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']
    # climate_vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind', 'psurf']
    ensemble = '01'
    t = time.time()
    bbox = osgrid2bbox(OsCell, '10km')
    # initialise empty xr dataset
    os_chunk = xr.Dataset()

    # loop through climate_vars and files for each var (i.e. months)
    print(f'Processing cell \'{OsCell}\' ...')
    for var in climate_vars:
        counter = 1
        file_list = filter_files(rcp, years, var, ensemble, nc_path)
        list_length = len(file_list)
        printProgressBar(0, list_length, prefix = f'{var}:', suffix = 'Complete', length = 50)
        for file in file_list:
            printProgressBar(counter,
                             list_length,
                             prefix = f'{var}:',
                             suffix = 'Complete',
                             length = 50)
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
    OsRegions = [
        'SV', 'SW', 'SX', 'SY', 'SZ', 'TV',
        'SR', 'SS', 'ST', 'SU', 'TQ', 'TR',
        'SM', 'SN', 'SO', 'SP', 'TL', 'TM',
        'SH', 'SJ', 'SK', 'TF', 'TG', 'SC',
        'SD', 'SE', 'TA', 'NW', 'NX', 'NY',
        'NZ', 'OV', 'NR', 'NS', 'NT', 'NU',
        'NL', 'NM', 'NN', 'NO', 'NP', 'NF',
        'NG', 'NH', 'NJ', 'NK', 'NA', 'NB',
        'NC', 'ND', 'NE', 'HW', 'HX', 'HY',
        'HZ', 'HT', 'HU', 'HO', 'HP'
    ]

    OsGrid = [code +  f'{num:02}' for code in OsRegions for num in range(100)]

    pool = multiprocessing.Pool(processes=16)

    # Use the pool.map() function to parallelize the loop
    results = pool.map(rechunk_ChessScape, OsGrid)

    # Close the pool to indicate that no more tasks will be submitted
    pool.close()

    # Wait for all processes to complete
    pool.join()
    