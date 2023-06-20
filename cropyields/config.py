# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), June 2023
# ====================================================
"""
Settings for running WOFOST for a specified farm using 
the class Farm in FarmManager
"""

from cropyields import data_dirs
from pcse.fileinput import YAMLCropDataProvider
from pcse.util import WOFOST80SiteDataProvider
from cropyields.CropManager import SingleRotationAgroManager

# CLIMATE
rcp = 'rcp26'
ensemble = 1
soilsource = 'SoilGrids'

# DIRS
base_dir = data_dirs['wofost_dir']
crop_dir = base_dir + 'WOFOST_crop_parameters\\'
agromanagement_dir = base_dir + 'pcse_examples\\'
output_dir = base_dir + 'WOFOST_output\\'

# CROP PARAMETERS
cropd = YAMLCropDataProvider(crop_dir)

# SITE PARAMETERS
sitedata = WOFOST80SiteDataProvider(WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20)
