"""
Wofost_SouthHams.R
==================

Author: Mattia Mancini
Created: 7-Jun-2023
----------------------
DESCRIPTION
Script that plots the results of the runs of Wofost for the South Hams area 
to compare differences in yields for winter wheat driven by climate (RCP
scenarios), soil, and wheat variety
===========================================================================
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

datapath  =  "D:\\Documents\\Data\\PCSE-WOFOST\\WOFOST_output\\"
rcp_list  =  ['rcp26', 'rcp45', 'rcp60', 'rcp85']
year_list =  [2020, 2025, 2030, 2035, 2040, 2045, 2050]
variety   = '101' # can be 101 to 106 depending on what has been run
soil      = 'SoilGrids' # can be SoilGrids or WHSD

## (1) Climate
## ===========
 
data_dict = dict()
for rcp in rcp_list:
    for year in year_list:
        filename = f'{datapath}SouthHams_{rcp}_WinterWheat_{variety}_{year}_{soil}.csv'
        df = pd.read_csv(filename)
        key = f'{rcp}_{year}'
        data_dict[key] = df

combined_data = pd.DataFrame()

for rcp in rcp_list:
    rcp_data = []
    
    for year in year_list:
        key = f'{rcp}_{year}'
        if key in data_dict:
            column_data = data_dict[key]['yield']
            df = pd.DataFrame({'Year': rcp, 'RCP': year, 'Value': column_data})
            combined_data = combined_data.append(df, ignore_index=True)

sns.set(style='whitegrid')
g = sns.catplot(x='Year', y='Value', hue='RCP', data=combined_data, kind='box', height=8, aspect=2)
g.set_axis_labels('Year', 'Yield [kg dm]')
g.fig.suptitle('Winter wheat yields - South Hams')

plt.grid(axis='y', linestyle='dashed')
plt.savefig(f'{datapath}Figures\\wheat_climate_yields_RCP.png', dpi=300)
plt.show()

## (2) Soils
## =========
rcp       = 'rcp26'
year      = 2020
variety   = '101'
soil_list = ['SoilGrids', 'WHSD']

data_dict = dict()
soil_data = pd.DataFrame()
for soil in soil_list:
    filename = f'{datapath}SouthHams_{rcp}_WinterWheat_{variety}_{year}_{soil}.csv'
    df = pd.read_csv(filename)
    column_data = df['yield']
    df = pd.DataFrame({'Soil': soil, 'Yield': column_data})
    soil_data = soil_data.append(df)


sns.set(style='whitegrid')
sns.boxplot(x='Soil', y='Yield', data=soil_data)

plt.xlabel('Soil data provider')
plt.ylabel('Yield [kg dm]')
plt.title('Yields by Soil data provider - South Hams 2020')
plt.savefig(f'{datapath}Figures\\yield_by_soil.png', dpi=300)
plt.show()


## (3) Varieties
## =============
rcp          = 'rcp26'
year         = 2020
soil         = 'SoilGrids'
variety_list = ['101', '103', '104', '105', '106', '107']


data_dict = dict()
var_data = pd.DataFrame()
for variety in variety_list:
    filename = f'{datapath}SouthHams_{rcp}_WinterWheat_{variety}_{year}_{soil}.csv'
    df = pd.read_csv(filename)
    column_data = df['yield']
    df = pd.DataFrame({'Variety': variety, 'Yield': column_data})
    var_data = var_data.append(df)


sns.set(style='whitegrid')
sns.boxplot(x='Variety', y='Yield', data=var_data)

plt.xlabel('Wheat variety')
plt.ylabel('Yield [kg dm]')
plt.title('Yields by variety - South Hams 2020')
plt.savefig(f'{datapath}Figures\\yield_by_variety.png', dpi=300)
plt.show()