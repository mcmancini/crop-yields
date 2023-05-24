import os

# Parameters to download Chess-scape data from the CEDA archive
# and save them on disk
ceda_parameters = {
    'ceda_usr': os.environ.get('CEDA_user'),
    'ceda_pwd': os.environ.get('CEDA_pwd'),
    'ftp_address': "ftp.ceda.ac.uk"
}

# parameters to create, modify and query the SQL database
db_parameters = {
    'db_user': os.environ.get('SQL_user'),
    'db_password': os.environ.get('SQL_pwd'),
    'db_name': 'nev_db'
}

# other paths:
#   - OSGB_dir:   where the rechunked Chess_Scape data is stored
#   - soilds_dir: where the soil data is stored.
data_dirs = {
    'ceda_dir':  'D:\\Documents\\Data\\PCSE-WOFOST\\ClimateData\\nc_files\\Raw\\',
    'OSGB_dir':  'D:\\Documents\\Data\\PCSE-WOFOST\\ClimateData\\nc_files\\OsGrid\\',
    'soils_dir': 'D:\\Documents\\Data\\PCSE-WOFOST\\SoilData\\nc_files\\',
    'utils_dir': 'D:\\Documents\\Data\\PCSE-WOFOST\\Utils\\'
}

# DEM terrain_50 parameters
dem_parameters = {
    'db_user': os.environ.get('SQL_user'),
    'db_password': os.environ.get('SQL_pwd'),
    'db_name': 'terrain_50'
}

# WHSD parameters
whsd_parameters = {
    'db_user': os.environ.get('SQL_user'),
    'db_password': os.environ.get('SQL_pwd'),
    'db_name': 'nev',
    'schema': 'seer'
}