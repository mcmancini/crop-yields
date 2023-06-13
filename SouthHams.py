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
variety_list = ['101', '102', '103', '104', '105', '106', '107']


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

## (4) Time series
## ===============
rcp  =  'rcp26'
year_list =  [year for year in range(2020, 2051)]
variety   = '101' # can be 101 to 106 depending on what has been run
soil      = 'SoilGrids' # can be SoilGrids or WHSD

data_dict = dict()
for year in year_list:
    filename = f'{datapath}SouthHams_{rcp}_WinterWheat_{variety}_{year}_{soil}_dry.csv'
    df = pd.read_csv(filename)
    key = year
    data_dict[key] = df

quantiles = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
quantile_data = {}

for year, df in data_dict.items():
    quantiles_year = df['yield'].quantile(quantiles)
    quantile_data[year] = quantiles_year

# Convert the quantile_data dictionary into a DataFrame
quantile_df = pd.DataFrame(quantile_data)

# Plot the line graph
fig, ax = plt.subplots()

# Plot median line in dark red
ax.plot(quantile_df.columns, quantile_df.loc[0.5], color='navy', label='Median')

# Shade areas between quantiles
qtls = [0.01, 0.05, 0.25, 0.75, 0.95, 0.99]
colors = ['mistyrose', 'lightcoral', 'red', 'lightcoral', 'mistyrose'] 
colors = ['lightskyblue', 'dodgerblue', 'blue', 'dodgerblue', 'lightskyblue']
for i in range(len(qtls)-1):
    lower_quantile = qtls[i]
    upper_quantile = qtls[i+1]
    ax.fill_between(
        quantile_df.columns,
        quantile_df.loc[lower_quantile],
        quantile_df.loc[upper_quantile],
        color=colors[i],
        alpha=0.7
    )

# Set labels and title
ax.set_xlabel('Year')
ax.set_ylabel('Yield')
ax.set_title('Time series of yields -- Winter wheat')

# Legend
legend_elements = [plt.Line2D([0], [0], color='navy', lw=2, label='Median')]
legend_elements.extend([plt.Rectangle((0, 0), 1, 1, color=color) for color in colors])
labels = ['Median', '1-5%', '5-25%', '25-75%', '75-95%', '95-99%']
ax.legend(legend_elements, labels)

plt.savefig(f'{datapath}Figures\\yield_timeseries.png', dpi=150)
plt.show()