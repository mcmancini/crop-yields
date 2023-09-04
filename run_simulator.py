# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), September 2023
# =========================================================
"""
run_simulator.py
================
This script allows the following:
    - Create an instance of the Wofost Simulator for a selected
      location in GB. 
    - Define an input parameter space as a list of parameter
      dictionaries. This list is then passed to the simulator
    - Run the simulator on the defined input parameter space
      collecting the output.
"""
from cropyields.SimulationManager import WofostSimulator
import datetime as dt

# Location
lat, lon = 50.238797, -3.700497
year = 2020

sim = WofostSimulator(lon, lat)


# PARAMETER RANGE DEFINITION. This is where we can set a sampling desing. 
# The code is set up for each sample to be a list of dictionaries. Each 
# will have a name to be able to map the sample to the input parameter set.
params = [{
    'name': 'test_sample',
    'crop': 'wheat',
    'variety': 'Winter_wheat_106',
    'year': year,
    'WAV': 100,      # Initial amount of water in total soil profile [cm]
    'NAVAILI': 80,   # Amount of N available in the pool at initialization of the system [kg/ha]
    'PAVAILI': 10,   # Amount of P available in the pool at initialization of the system [kg/ha]
    'KAVAILI': 20,   # Amount of K available in the pool at initialization of the system [kg/ha]
    'crop_start_date': dt.date(year, 11, 20),
    'N_FIRST': 60,   # Amount of N applied in first, second and third fertilisation event [kg/ha]. Max: 250 in total
    'N_SECOND': 100, 
    'N_THIRD': 50, 
    'P_FIRST': 3,    # Amount of P applied in first, second and third fertilisation event [kg/ha]. Max: 60
    'P_SECOND': 13, 
    'P_THIRD': 23,  
    'K_FIRST': 4,    # Amount of K applied in first, second and third fertilisation event [kg/ha]. Max: 150
    'K_SECOND': 14, 
    'K_THIRD': 24    
}]

# Run the simulator
sim.run(params)