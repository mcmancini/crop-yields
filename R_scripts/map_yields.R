## map_yields.R
## ============
##
## Author: Mattia Mancini
## Created: 15-May-2023
## ----------------------
##
## DESCRIPTION
## Script to take the output of a model run of Wofost and map it
## =============================================================

## (1) SETUP
## =========
rm(list=ls())
library(sf)
datapath <- 'D:/Documents/Data/PCSE-WOFOST/'
gitpath  <- 'D:/Documents/GitHub/crop-yields/'
source(paste0(gitpath, 'R_scripts/functions/fcn_plt_map.R'))

input <- 'SouthHams_WinterWheat_106'

## 1.1. Prepare data for mapping
## -----------------------------

# Shapefile of parcels
parcels <- st_read(paste0(datapath, 'south_hams_arable/south_hams_arable_fields.shp'))[,'oid']
output  <- read.csv(paste0(datapath, input, '.csv'))
output <- merge(parcels, output, by.x='oid', by.y='parcel_id')

plt <- fcn_plt_map(output, 'yield', c(0, 1000, 2000, 3000, 4000, 5000, 6000, 7000), 'Yields, winter wheat', 'Yields[kg/ha]', 'bottom', 'magma', -1)

filename <- paste0(input, '.jpeg')
ggsave(filename=filename, plot = plt, device = "jpeg",
       path = datapath, units = "in", width = 16, height = 12) 