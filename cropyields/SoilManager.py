from cropyields import data_dirs
from cropyields.utils import osgrid2lonlat, water_retention, water_conductivity, nearest
import xarray as xr
from rosetta import rosetta, SoilData
from soiltexture import getTexture
import numpy as np
from math import log10


class SoilGridsDataProvider(dict):
    """
    Read soil data from netcdf file. This data provider is set to
    work with the SoilGrids data retrieved using the script 
    'bulk_SoilGrids_downloader.py'. 
    
    INPUT DATA     
    :param osgrid_code: the OS Grid Code of the parcel for which soil
           soil data is required.
    :param opt_soilvars: list of optional soil parameters to be used 
           for the calculations of the hydrological characteristics of
           the soil. This is at the moment left blank and does nothing
    -------------------------------------------------------------------
    NB: This is a temporary class specifically created to deal with
        SoilGrids soil data combined with the USDA Rosetta pedotransfer
        functions (Require sand, silt and clay fractions). 
        As we want to be able to import and use a variety of soil data, 
        we will create a parent soildataprovider class that will allow 
        to deal with whichever soil input we want and a set of child 
        classes for each specific soil data provider.
    """

    # class attributes
    _DEFAULT_SOILVARS   = ["sand", "silt", "clay"]
    _SOIL_PATH          = data_dirs["soils_dir"] + "GB_soil_data.nc"
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

    def __init__(self, osgrid_code, opt_soilvars=None):
        dict.__init__(self)
        self.update(self._return_soildata(osgrid_code))
        self.update(self._defaults)

    # @staticmethod   
    # def _def_soilvars(opt_soilvars=None):
    #     default_vars = SoilGridsDataProvider._DEFAULT_SOILVARS
    #     opt_vars = [opt_soilvars] if isinstance(opt_soilvars, str) else opt_soilvars or []
    #     return default_vars + [var for var in opt_vars if isinstance(var, str)]
    
    # def _return_locationdata(self, osgrid_code):
    #     """Return lon and lat info from os grid code"""
    #     lon, lat = osgrid2lonlat(osgrid_code, EPSG=4326)
    #     return {
    #         'osgrid_code': osgrid_code,
    #         'lon': lon,
    #         'lat': lat
    #     }
    
    def _return_soildata(self, osgrid_code):
        lon, lat = osgrid2lonlat(osgrid_code, EPSG=4326)
        soil_array = xr.open_dataset(SoilGridsDataProvider._SOIL_PATH)
        soil_df = soil_array.sel(x=lon, y=lat, method="nearest").to_dataframe().reset_index()[self._DEFAULT_SOILVARS]
        # rosetta requires [%sand, %silt, %clay, bulk density, th33, th1500] in this order. Last 3 optional
        soil_df = soil_df.iloc[0].tolist()
        rosettasoil = SoilData.from_array([soil_df])
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
        SOLNAM = getTexture(soil_df[0], soil_df[2], classification='INTERNATIONAL')

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
        msg += "Data Source: SoilGrids\nhttps://www.isric.org/explore/soilgrids\n"
        msg += "============================================\n\n"
        for key, value in self.items():
            msg += ("%s: %s %s\n" % (key, value, type(value)))
        return msg

# a = SoilGridsDataProvider('NT2755072950')         
# print(a)
    