'''
CHESS-SCAPE data downloader.
============================

Author: Mattia Mancini
Created: 19-September-2022
--------------------------

Script that downloads climate data from the CEDA archive and saves it on disk
It requires a CEDA account, and the data is downloaded through ftp. 
Credentials to access CEDA are stored as environment variables.

CHESS-SCAPE data downloaded from this address:
https://catalogue.ceda.ac.uk/uuid/8194b416cbee482b89e0dfbe17c5786c

- The following RCPs are included: 'rcp26', 'rcp45', 'rcp60', 'rcp85'
- The following variables are included: 'tas', 'tasmax', 'tasmin', 'pr', 
  'rlds', 'rsds', 'hurs', 'sfcWind'
- A year is defined as 12 months of 30 days each
- Four ensembles for each RCP are available: 1, 4, 6, 15 based on different
  initial perturbations
- Data can be bias corrected or not, which is specified by the 'bias_corrected'
  parameter
'''

from cropyields.ChessScape_manager import download_ChessScape_data

# Define arguments for download
rcps = ['rcp26', 'rcp45', 'rcp60', 'rcp85']
vars = ['tas', 'tasmax', 'tasmin', 'pr', 'rlds', 'rsds', 'hurs', 'sfcWind']

# there are 4 realisations: 1, 4, 6, 15 (are these rcp ensemble members? Each RCP contains four ensemble members (01, 02, 03, 04); member 01 is the default 
# parameterisation of the Hadley Centre Climate model and the others provide an estimate of climate model uncertainty)
ensembles = [1, 4, 6, 15]

download_ChessScape_data(rcps, vars, ensembles, bias_corrected=True)
