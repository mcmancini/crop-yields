# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), June 2023
# ====================================================
"""
Settings for running WOFOST for a specified farm using 
the class Farm in FarmManager
"""
from pcse.fileinput import YAMLCropDataProvider
from pcse.util import WOFOST80SiteDataProvider
from cropyields import data_dirs
from cropyields.crop_manager import SingleRotationAgroManager

# CLIMATE
rcp = "rcp26"
ensemble = 1
soilsource = "SoilGrids"

# DIRS
base_dir = data_dirs["wofost_dir"]
crop_dir = base_dir + "WOFOST_crop_parameters\\"
agromanagement_dir = base_dir + "pcse_examples\\"
output_dir = base_dir + "WOFOST_output\\"

# CROP PARAMETERS
cropd = YAMLCropDataProvider(crop_dir, force_reload=True)

# SITE PARAMETERS
sitedata = WOFOST80SiteDataProvider(
    WAV=100, CO2=360, NAVAILI=80, PAVAILI=10, KAVAILI=20
)


"""
CROP AGROMANAGEMENT ARGS
========================

These are timed events such as fertilisation. They are dictionaries with the following 
keys for each npk event: 'month', 'day', 'N_amount', 'P_amount', 'K_amount'. Defining 
month and day allows to automatically assign the correct year based on the crop calendar 
year defined when creating instances of the class 'Crop' (See CropManager.py). If a 'date'
key has been passed (as in for example npk_1['date'] = dt.time(2023, 5, 21)), then that 
will be used instead.
"""

# CROP PARAMETERS
# ===============
# This includes fertilisation, irrigation and mowing. Add based on use
default_timed_events = {
    "wheat": {
        "npk_1": {"month": 2, "day": 20, "N_amount": 60, "P_amount": 50, "K_amount": 50},
        "npk_2": {"month": 3, "day": 10, "N_amount": 100, "P_amount": 100, "K_amount": 100},
        "npk_3": {"month": 4, "day": 15, "N_amount": 50, "P_amount": 100, "K_amount": 100},
    },
    "maize": {
        'npk_1': {"month": 4, "day": 15, "N_amount": 20, "P_amount": 0, "K_amount": 0},
        'npk_2': {"month": 5, "day": 15, "N_amount": 20, "P_amount": 25, "K_amount": 30},
        'npk_3': {"month": 6, "day": 15, "N_amount": 20, "P_amount": 25, "K_amount": 40}
    },
    "potatoes": {
        'npk_1': {"month": 5, "day": 1, "N_amount": 40, "P_amount": 40, "K_amount": 40},
        'npk_2': {"month": 5, "day": 25, "N_amount": 70, "P_amount": 35, "K_amount": 105},
        'npk_3': {"month": 6, "day": 5, "N_amount": 70, "P_amount": 35, "K_amount": 105},
        'npk_4': {"month": 6, "day": 30, "N_amount": 70, "P_amount": 35, "K_amount": 105}
    },
    "ryegrass": {
        'mowing_1': {"month": 5, "day": 1, "biomass_remaining": 320},  # kg/ha
        'mowing_2': {"month": 5, "day": 25, "biomass_remaining": 320},
        'mowing_3': {"month": 6, "day": 5, "biomass_remaining": 320}
    }
}

crop_parameters = {
    'wheat': {
        'crop_start_month': 11,
        'crop_start_day': 5,
        'crop_end_type': 'maturity',
        'max_duration': 365,
        'apply_npk': [
            default_timed_events['wheat']['npk_1'],
            default_timed_events['wheat']['npk_2'],
            default_timed_events['wheat']['npk_3'],
        ]
    },
    'maize' : {
        "crop_start_month": 4,
        "crop_start_day": 1,
        "crop_end_type": "maturity",
        "max_duration": 365,
        "apply_npk": [
            default_timed_events['maize']['npk_1'],
            default_timed_events['maize']['npk_2'],
            default_timed_events['maize']['npk_3']
        ]
    },
    'potato': {
        "crop_start_month": 4,
        "crop_start_day": 1,
        "crop_end_type": "maturity",
        "max_duration": 365,
        "apply_npk": [
            default_timed_events['potatoes']['npk_1'],
            default_timed_events['potatoes']['npk_2'],
            default_timed_events['potatoes']['npk_3'],
            default_timed_events['potatoes']['npk_4']
        ]
    },
    'ryegrass': {
        "crop_start_month": 11,
        "crop_start_day": 5,
        "crop_end_type": "maturity",
        "max_duration": 730,
        "mowing": [
            default_timed_events['ryegrass']['mowing_1'],
            default_timed_events['ryegrass']['mowing_2'],
            default_timed_events['ryegrass']['mowing_3']
        ]
    }
}
