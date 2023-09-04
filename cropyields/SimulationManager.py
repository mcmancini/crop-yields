from cropyields.WeatherManager import NetCDFWeatherDataProvider
from cropyields.utils import lonlat2osgrid
from cropyields.SoilManager import SoilGridsDataProvider
from cropyields.config import crop_parameters, cropd
from cropyields.CropManager import Crop, CropRotation
from pcse.util import WOFOST80SiteDataProvider
from pcse.base import ParameterProvider
from pcse.models import Wofost80_NWLP_FD_beta, Wofost72_WLP_FD, Wofost72_PP, Wofost80_PP_beta

class WofostSimulator:
    """
    Class generating a Wofost simulator that allows to 
    run Wofost on any location in GB and multiple times 
    based on a list of input parameter sets.
    This is useful to perform sensitivity analysis or 
    to build a Wofost emulator
    --------------------------------------------------
    
    Input parameters for initialisation:
    :param lon: longitude of the location of interest
    :param lat: latitude of the location of interest
    :param year: year for which to run the simulator
    :param rcp: RCP scenario (default is '_DEFAULT_RCP')
    :param ensemble: Ensemble number (default is '_DEFAULT_ENSEMBLE')

    Methods defined here:

    __str__(self, /)
        Return str(self).

    run(self, args)
        run the Wofost simulator one or multiple times based on a 
        list of one or multiple imput parameter combinations defined in 
        args
        Example args:
            [{
                'name': 'test_sample_01',
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
    """

    _DEFAULT_RCP = 'rcp26'
    _DEFAULT_ENSEMBLE = 1


    def __init__(self, lon, lat, rcp=None, ensemble=None):
        self.lon = lon
        self.lat = lat
        self.osgrid_code = lonlat2osgrid((self.lon, self.lat), 10)

        if rcp is None:
            rcp = self._DEFAULT_RCP
        self.rcp = rcp

        if ensemble is None:
            ensemble = self._DEFAULT_ENSEMBLE
        self.ensemble = ensemble
        
        # weather
        self.wdp = NetCDFWeatherDataProvider(self.osgrid_code, self.rcp, self.ensemble)
        
        #soil
        self.soildata = SoilGridsDataProvider(self.osgrid_code)


    def run(self, args):
        """
        Method to run Wofost one or multiple times based on a list of one or
        multiple imput parameter combinations defined in **args                            
        """
        output = {}
        for item in args:

            name = item.get('name')
            crop = item.get('crop')
            variety = item.get('variety')
            year = item.get('year')
            WAV = item.get('WAV')
            NAVAILI = item.get('NAVAILI')
            PAVAILI = item.get('PAVAILI')
            KAVAILI = item.get('KAVAILI')
            crop_start_date = item.get('crop_start_date')
            N_FIRST = item.get('N_FIRST')
            N_SECOND = item.get('N_SECOND')
            N_THIRD = item.get('N_THIRD')
            P_FIRST = item.get('P_FIRST')
            P_SECOND = item.get('P_SECOND')
            P_THIRD = item.get('P_THIRD')
            K_FIRST = item.get('K_FIRST')
            K_SECOND = item.get('K_SECOND')
            K_THIRD = item.get('K_THIRD')

            # GENERATE CROP AND AGROMANAGMENT
            # Fertilisation
            n_variables = [N_FIRST, N_SECOND, N_THIRD]
            p_variables = [P_FIRST, P_SECOND, P_THIRD]
            k_variables = [K_FIRST, K_SECOND, K_THIRD]

            for i, item in enumerate(crop_parameters[crop]['apply_npk']):
                item['N_amount'] = n_variables[i]
                item['P_amount'] = p_variables[i]
                item['K_amount'] = k_variables[i]

            crop_parameters[crop]['crop_start_date'] = crop_start_date
            crop_parameters[crop]['variety'] = variety
            wheat = Crop(year, 'wheat', **crop_parameters[crop])
            cropd.set_active_crop(wheat.crop, wheat.variety)
            rotation = CropRotation(wheat)
            agromanagement = rotation.rotation

            # SITE PARAMETERS
            sitedata = WOFOST80SiteDataProvider(WAV=WAV, 
                                                CO2=360, 
                                                NAVAILI=NAVAILI, 
                                                PAVAILI=PAVAILI, 
                                                KAVAILI=KAVAILI)

            # COMBINE ALL PARAMETERS
            parameters = ParameterProvider(cropdata=cropd, soildata=self.soildata, sitedata=sitedata)

            # Run the model
            wofsim = Wofost80_NWLP_FD_beta(parameters, self.wdp, agromanagement)
            wofsim.run_till_terminate()

            # Collect output
            summary_output = wofsim.get_summary_output()
            output_dict = {
                'DOM': summary_output[0]['DOM'],
                'TWSO': summary_output[0]['TWSO']
            }

            output[f'{name}_01'] = output_dict
            return output


    def __str__(self):
        msg = "======================================================\n"
        msg += "               Simulator characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += "Wofost simulator for location at \'" + self.osgrid_code + "\'" + "\n"
        msg += "Longitude: " + str(self.lon) + "\n"
        msg += "Latitude: " + str(self.lat) + "\n"
        msg += "Elevation: " + str(round(self.wdp.elevation, 2)) + "\n"
        msg += "Soil type: " + self.soildata['SOLNAM'] + "\n"

        return msg

