from cropyields import data_dirs
from cropyields.utils import osgrid2lonlat, water_retention, water_conductivity, nearest
from cropyields.db_manager import get_whsd_data
import xarray as xr
from rosetta import rosetta, SoilData
from soiltexture import getTexture
import numpy as np
from math import log10

class SoilDataProvider(dict):
    """
    Base class for all soil data providers
    """
    # class attributes
    _DEFAULT_SOILVARS   = ["sand", "silt", "clay"]
    _WILTING_POTENTIAL  = log10(1.5e4)
    _FIELD_CAPACITY     = log10(150)
    
    _defaults = {
        'CRAIRC' : 0.060,
        'SOPE' : 1.47,
        'KSUB' : 1.47,
        'RDMSOL' : 80,
        'SPADS' : 0.100,
        'SPODS' : 0.030,
        'SPASS' : 0.200,
        'SPOSS' : 0.050,
        'DEFLIM' : -0.300
    }

    def __init__(self, osgrid_code):
        dict.__init__(self)
        self.update(self._defaults)
    
    def _return_soildata(self, osgrid_code, soil_texture_list):
        lon, lat = osgrid2lonlat(osgrid_code, EPSG=4326)
        rosettasoil = SoilData.from_array([soil_texture_list])
        mean, std, codes = rosetta(3,rosettasoil) #int=rosetta version
        theta_r, theta_s, alpha, npar, K0 = mean[0][0], mean[0][1], 10**mean[0][2], 10**mean[0][3], 10**mean[0][4]
        psi = [x for x in np.arange(0, 6.1, 0.1).tolist()]
        psi = [-1] + psi# saturation
        wr = [water_retention(x, theta_r, theta_s, alpha, npar) for x in psi]
        wc = [water_conductivity(x, theta_r, theta_s, alpha, npar, K0) for x in psi]
        SMTAB = [x for pair in zip(psi, wr) for x in pair]
        # Permanent wilting point conventianally at 1500 kPa, fc between 10-30kPa
        wp_idx = psi.index(nearest(self._WILTING_POTENTIAL, psi))
        fc_idx = psi.index(nearest(self._FIELD_CAPACITY, psi))
        SMW = wr[wp_idx]
        SMFCF = wr[fc_idx]
        SM0 = wr[0]
        CONTAB = [x for pair in zip(psi, wc) for x in pair]
        # Provide soil texture given percentage of sand and clay
        SOLNAM = getTexture(soil_texture_list[0], soil_texture_list[2], classification='INTERNATIONAL')

        return {
            "osgrid_code": osgrid_code,
            "lon": lon,
            "lat": lat,
            "SOLNAM": SOLNAM,
            "SMTAB": SMTAB,
            "SMW": SMW,
            "SMFCF": SMFCF,
            "SM0": SM0,
            "CONTAB": CONTAB,
            "K0": K0
        }

    def __str__(self):
        msg = "============================================\n"
        msg +=  "Soil data provided by: %s\n" % self.__class__.__name__
        msg += "----------------Description-----------------\n"
        msg += "Soil data for parcel in OS cell %s \n" % self['osgrid_code']
        msg += "Lon: %.3f; Lat: %.3f\n" % (self['lon'], self['lat'])
        msg += "Data Source: %s\n" % self._DATA_SOURCE
        msg += "============================================\n\n"
        for key, value in self.items():
            if isinstance(value, list):
                rounded_list = [round(x, 2) for x in value[0:20]]  # only print first 20 elements of list
                msg += "%s: %s %s\n" % (key, rounded_list, type(value))
            else:
                msg += "%s: %s %s\n" % (key, value, type(value))
        return msg


class SoilGridsDataProvider(SoilDataProvider):
    """
    Read soil data from netcdf file. This data provider is set to
    work with the SoilGrids data retrieved using the script 
    'bulk_SoilGrids_downloader.py'. 
    
    INPUT DATA     
    :param osgrid_code: the OS Grid Code of the parcel for which soil
           soil data is required.
    """

    # class attributes
    _SOIL_PATH   = data_dirs["soils_dir"] + "GB_soil_data.nc"
    _DATA_SOURCE = "SoilGrids\nhttps://www.isric.org/explore/soilgrids"
    
    def __init__(self, osgrid_code):
        super().__init__(osgrid_code)
        soil_texture_list = self._load_soil_data(osgrid_code)
        self.update(self._return_soildata(osgrid_code, soil_texture_list))
    
    def _load_soil_data(self, osgrid_code):
        lon, lat = osgrid2lonlat(osgrid_code, EPSG=4326)
        soil_array = xr.open_dataset(SoilGridsDataProvider._SOIL_PATH)
        soil_df = soil_array.sel(x=lon, y=lat, method="nearest").to_dataframe().reset_index()[self._DEFAULT_SOILVARS]
        # rosetta requires [%sand, %silt, %clay, bulk density, th33, th1500] in this order. Last 3 optional
        soil_df = soil_df.iloc[0].tolist()
        return soil_df
    
class WHSDDataProvider(SoilDataProvider):
    """
    Read soil data from the WHSD. This data is currently stored after
    processing in a postgreSQL database at a 2km spatial resolution 
    (NEV SEER grid.)
    
    INPUT DATA     
    :param osgrid_code: the OS Grid Code of the parcel for which soil
           soil data is required.
    """

    # class attributes
    _DATA_SOURCE = "WHSD: https://shorturl.at/yRT37"
    
    def __init__(self, osgrid_code):
        super().__init__(osgrid_code)
        soil_texture_list = self._load_soil_data(osgrid_code)
        self.update(self._return_soildata(osgrid_code, soil_texture_list))
    
    def _load_soil_data(self, osgrid_code):
        soil_dict = get_whsd_data(osgrid_code, self._DEFAULT_SOILVARS)
        return [soil_dict[x] for x in soil_dict.keys()]