from cropyields import ceda_parameters, data_dirs
import ftplib
import os
from os import listdir
from os.path import isfile, join
import re

def download_ChessScape_data(rcps, vars, ensembles, bias_corrected):
    '''
    FTP download of ChessScape data, which is then
    saved into a specified directory
    '''

    ddir = data_dirs['ceda_dir']
    user = ceda_parameters['ceda_usr']
    pwd = ceda_parameters['ceda_pwd']
    ftp_addr = ceda_parameters['ftp_address']

    if not os.path.isdir(ddir):
        os.mkdir(ddir)
        print('Download data directory successfully created!')

    # Change the local directory to where you want to put the data
    os.chdir(ddir)

    # login to CEDA FTP
    f = ftplib.FTP(ftp_addr, user, pwd)

    # loop through RCPs
    for rcp in rcps:

        # loop through enselmbles
        for ensemble in ensembles:

            # loop through weather variables
            for var in vars:

                # loop through years
                for year in range(2020,2081):

                    # loop through months
                    for month in range(1,13):
                        if bias_corrected:
                            filedir = f'/badc/deposited2021/chess-scape/data/{rcp}_bias-corrected/{ensemble:02d}/daily/{var}/'
                            f.cwd(filedir)
                            file = f'chess-scape_{rcp}_bias-corrected_{ensemble:02d}_{var}_uk_1km_daily_{year:04d}{month:02d}01-{year:04d}{month:02d}30.nc'
                        else:
                            filedir = f'/badc/deposited2021/chess-scape/data/{rcp}/{ensemble:02d}/daily/{var}/'
                            f.cwd(filedir)
                            file = f'chess-scape_{rcp}_{ensemble:02d}_{var}_uk_1km_daily_{year:04d}{month:02d}01-{year:04d}{month:02d}30.nc'
                        try:
                            f.retrbinary("RETR %s" % file, open(file, "wb").write)
                            print(f'Downloading file {file}...')
                        except:
                            print(f'file {file} not found. Skipping...')
                            continue
    
    print(f'All files successfully downloaded')
    # Close FTP connection
    f.close()

# List all ChessScape files within path for the selected rcp, years, vars and ensembles
def filter_files(rcp, years, vars, ensembles):
    '''
    Identifies all files in ceda download dir. containing years and vars for the 
    specified ensemble and rcp. Years and vars can be one or more. In
    both cases, they must be passed as lists
    '''
    path = data_dirs['ceda_dir']
    
    if not isinstance(years, list):
        years = [years]
    if not isinstance(vars, list):
        vars = [vars]
    if not isinstance(ensembles, list):
        ensembles = [ensembles]
    allfiles = [f for f in listdir(path) if isfile(join(path, f))]
    df = [re.split('_|\.|-', elem) for elem in allfiles]
    
    filter_list = [False for x in range(len(df))]
    for year in years:
        for var in vars:
            for ensemble in ensembles:
                for i in range(len(df)):
                    yr = int(df[i][10][0:4])
                    if ensemble in df[i][5] and rcp in df[i][2] and var == df[i][6] and yr == year:
                        filter_list[i] = True
                    else:
                        continue
    filtered_files = [i for (i, v) in zip(allfiles, filter_list) if v]
    filtered_files = [path + '\\' + x for x in filtered_files]
    return filtered_files
