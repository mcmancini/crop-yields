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
from cropyields.Sampler import InputSampler
import pandas as pd

# Location
lat, lon = 50.238797, -3.700497
year = 2020

sim = WofostSimulator(lon, lat)


# PARAMETER RANGE DEFINITION. This is where we can set a sampling desing. 
# The code is set up for each sample to be a list of dictionaries. Each 
# will have a name to be able to map the sample to the input parameter set.
params = {
    'name': 'test_sample',
    'crop': 'wheat',
    'variety': 'Winter_wheat_106',
    'year': year
  }

lhs_sampler = InputSampler(params)
parameter_samples = lhs_sampler.lhs(10)


# Run the simulator
a = sim.run(parameter_samples)
input_df = pd.DataFrame(parameter_samples)
output_df = pd.DataFrame(a)
output_df = output_df.T.reset_index(drop=True)
df = pd.concat([input_df, output_df], ignore_index=True, axis=1)
df.columns = list(input_df.columns) + list(output_df.columns)
df.to_csv('test.csv')