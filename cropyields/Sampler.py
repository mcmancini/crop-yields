# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), September 2023
# =========================================================
import datetime as dt
import numpy as np
from pyDOE2 import lhs

class InputSampler:
    """
    Class InputSampler:
    class generating a sampling design based on a set of input parameters
    to pass to a Simulator object (see SimulationManager.WofostSimulator).
    This allows to run Wofost iteratively on cominations of input parameters
    ------------------------------------------------------------------------

    Input parameters for initialisation:
    :param params: a dictionary containing the following keys:
        'name': a name to identify the sampling set of runs
        'crop': a crop to be run into the simulation
        'variety': a crop variety
        'year': the year for which the simulator needs to be run
    
    Methods defined here:

    __str__(self, /)
        Return str(self).

    lhs(self, num_each):
        creates a latin hypercube sampling design where 'num_each'
        samples are taken for each parameter, for a total of 
        num_each x number of parameters. At the moment these are 
        hard coded in the class (see _DATA_TEMPLATE)
        This method returns a list of dictionaries, each with 
        a combination of input parameters from latin hypercube 
        sampling
    """

    _DATA_TEMPLATE = {
        'WAV': 100,      # Initial amount of water in total soil profile [cm]
        'NAVAILI': 80,   # Amount of N available in the pool at initialization of the system [kg/ha]
        'PAVAILI': 10,   # Amount of P available in the pool at initialization of the system [kg/ha]
        'KAVAILI': 20,   # Amount of K available in the pool at initialization of the system [kg/ha]
        'crop_start_date': dt.date(2020, 11, 20),
        'N_FIRST': 60,   # Amount of N applied in first, second and third fertilisation event [kg/ha]. Max: 250 in total
        'N_SECOND': 100, 
        'N_THIRD': 50, 
        'P_FIRST': 3,    # Amount of P applied in first, second and third fertilisation event [kg/ha]. Max: 60 in total
        'P_SECOND': 13, 
        'P_THIRD': 23,  
        'K_FIRST': 4,    # Amount of K applied in first, second and third fertilisation event [kg/ha]. Max: 150 in total
        'K_SECOND': 14, 
        'K_THIRD': 24    
    }

    def __init__(self, params):
        
        year = params['year']
        self._params = params
        self._DEFAULT_RANGES = {
            "WAV": (100, [0.0, 100.0], float),
            "NAVAILI": (80, [0, 250], float),
            "PAVAILI": (10, [0, 50], float),
            "KAVAILI": (20, [0, 250], float),
            "crop_start_date": (dt.date(year, 11, 20).toordinal(), [dt.date(year, 9, 1).toordinal(), dt.date(year, 12, 31).toordinal()]),
            "N_FIRST": (60, [0, 250], float),
            "P_FIRST": (3, [0, 250], float),
            "K_FIRST": (4, [0, 250], float),
            "N_SECOND": (100, [0, 250], float),
            "P_SECOND": (13, [0, 250], float),
            "K_SECOND": (14, [0, 250], float),
            "N_THIRD": (50, [0, 250], float),
            "P_THIRD": (23, [0, 250], float),
            "K_THIRD": (24, [0, 250], float),
        }
    
    def lhs(self, num_each):
        """
        Latin hypercube sampling design on default parameters
        """
        sampling_ranges = np.array([self._DEFAULT_RANGES[key][1] for key in self._DEFAULT_RANGES])
        lhs_design = lhs(len(sampling_ranges), samples=num_each * len(sampling_ranges), criterion="maximin")
        scaled_lhs_sample = np.zeros_like(lhs_design)
        for i in range(len(sampling_ranges)):
            scaled_lhs_sample[:, i] = sampling_ranges[i, 0] + lhs_design[:, i] * (sampling_ranges[i, 1] - sampling_ranges[i, 0])
        output_params = self._build_output(scaled_lhs_sample)
        return output_params
        

    def _build_output(self, sample_array):
        """
        Format data for output
        """

        parameter_names = list(self._DATA_TEMPLATE.keys())
        output_sample = []
        for i in range(len(sample_array)):
            parameter_dict = {}
            for j in range(len(parameter_names)):
                if parameter_names[j] == "crop_start_date":
                    parameter_dict[parameter_names[j]] = int(sample_array[i][j])
                else:
                    parameter_dict[parameter_names[j]] = sample_array[i][j]
            parameter_dict.update(self._params)
            output_sample.append(parameter_dict)
        return output_sample
    
    def __str__(self):
        msg = "======================================================\n"
        msg += "             Sampler characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += "Sampler for crop \'" + self._params['crop'] + "\'\n"
        msg += "Variety: \'" + self._params['variety'] + "\'\n"
        msg += "Year: \'" + str(self._params['year']) + "\'\n"
        msg += "------------------------------------------------------\n"
        msg += "Output name: \'" + self._params['name'] + "\'\n"
        return msg




    



