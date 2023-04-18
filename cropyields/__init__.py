import os

# Parameters to download Chess-scape data from the CEDA archive
# and save them on disk
ceda_parameters = {
    'ceda_usr': os.environ.get('CEDA_user'),
    'ceda_pwd': os.environ.get('CEDA_pwd'),
    'download_dir': "D:\\Documents\\Data\\ClimateData\\nc_files\\Raw\\",
    'ftp_address': "ftp.ceda.ac.uk"
}

# parameters to create, modify and query the SQL database
db_parameters = {
    'db_user': os.environ.get('SQL_user'),
    'db_password': os.environ.get('SQL_pwd'),
    'db_name': 'nev_db_v2'
}

# other paths:
#   - OSGB_dir: where the rechunked Chess_Scape data is stored
paths = {
    'OSGB_dir': 'D:\\Documents\\Data\\ClimateData\\nc_files\\OsGrid\\'
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