"""
A weather data provider reading its data from netCDF files.
Code based on the 'excelweatherdataprovider contained in the
fileinput of the PCSE module
"""
import os
import xarray as xr
import pandas as pd
import datetime as dt
from pcse.base import WeatherDataContainer, WeatherDataProvider
from pcse.util import reference_ET, check_angstromAB
from pcse.exceptions import PCSEError
from pcse.db import NASAPowerWeatherDataProvider
from pcse.settings import settings
from cropyields import data_dirs
from cropyields.utils import osgrid2lonlat, rh_to_vpress, sun, calc_doy, nearest, find_closest_point
from cropyields.db_manager import get_parcel_data
import logging

# Conversion functions
NoConversion = lambda x: x
K_to_C = lambda x: x-273.15
kJ_to_J = lambda x: x*1000.
W_to_J = lambda x: x*86400.
kPa_to_hPa = lambda x: x*10.
mm_to_cm = lambda x: x/10.

# Declare NetCDFWeatherDataProvider class
class NetCDFWeatherDataProvider(WeatherDataProvider):
    """Reading weather data from a NetCDF file (.nc).

    :param osgrid_code: code of the OS tile for which weather projections are required
    :param rcp: the rcp scenario for which weather projections are required   
    :param ensemble: the ensemble for the rcp for which weather projections are required     
    :param mising_snow_depth: the value that should use for missing SNOW_DEPTH values,
           the default value is `None`.
    :param force_update: bypass the cache file, reload data from the netcdf files and
           write a new cache file. Cache files are written under `$HOME/.pcse/meteo_cache`

    The NetCDFWeatherDataProvider takes care of the adjustment of solar radiation to the 
    length of the day (AAA: need to verify that the solar radiation data passed to
    compute ETs is the data expected by the functions implemented in Wofost!!!) and 
    deals with the fact that the length of a year in ChessScape is 360 days, which 
    Wofost cannot handle. 
    """
    obs_conversions = {
        "TMAX": K_to_C,
        "TMIN": K_to_C,
        "IRRAD": NoConversion,
        "VAP": NoConversion,
        "WIND": NoConversion,
        "RAIN": mm_to_cm,
        "SNOWDEPTH": NoConversion
    }

    def __init__(self, osgrid_code, rcp, ensemble, missing_snow_depth=None, nodata_value = -999, force_update=False):
        WeatherDataProvider.__init__(self)

        os_digits = [int(s) for s in osgrid_code if s.isdigit()]
        os_digits_1k = os_digits[0:2] + os_digits[int(len(os_digits)/2):int(len(os_digits)/2+2)]
        os_digits_10k = os_digits[0:1] + os_digits[int(len(os_digits)/2):int(len(os_digits)/2+1)]
        os_digits_1k = ''.join(str(s) for s in os_digits_1k)
        os_digits_10k = ''.join(str(s) for s in os_digits_10k)
        self.osgrid_1km = osgrid_code[0:2].upper() + os_digits_1k
        self.osgrid_10km = osgrid_code[0:2].upper() + os_digits_10k
        self.nc_fname = os.path.abspath(data_dirs['OSGB_dir']+f'{self.osgrid_10km.upper()}_{rcp}_{ensemble:02d}.nc')
        self.rcp, self.ensemble = rcp, ensemble
        self.missing_snow_depth = missing_snow_depth
        self.nodata_value = nodata_value
        self.cache_fname = f'{self.osgrid_1km}_{self.rcp}_{self.ensemble:02d}'
        if not os.path.exists(self.nc_fname):
            msg = "Cannot find weather file at: %s" % self.nc_fname
            raise PCSEError(msg)

        self.longitude, self.latitude = osgrid2lonlat(self.osgrid_1km, EPSG=4326)

        # Retrieve altitude
        self.elevation = get_parcel_data(osgrid_code, ['elevation'])['elevation']

        # Retrieve Angstrom coefficients A and B
        w = NASAPowerWeatherDataProvider(self.longitude, self.latitude)
        angstA, angstB = w.angstA, w.angstB
        self.angstA, self.angstB = check_angstromAB(angstA, angstB)
        self.has_sunshine = False # data has radiation values, not sunshine hours

        # Check for existence of a cache file
        cache_file = self._find_cache_file(self.cache_fname)
        if cache_file is None or force_update is True:
            msg = "No cache file or forced update, getting data from Chess-Scape nc files."
            self.logger.debug(msg)
            # No cache file, we really have to get the data from the Chess-Scape nc files
            self._get_and_process_ChessScape()
            return

        # get age of cache file, if age < 90 days then try to load it. If loading fails retrieve data
        # from the Chess-Scape nc files.
        r = os.stat(cache_file)
        cache_file_date = dt.date.fromtimestamp(r.st_mtime)
        age = (dt.date.today() - cache_file_date).days
        if age < 90:
            msg = "Start loading weather data from cache file: %s" % cache_file
            self.logger.debug(msg)

            status = self._load_cache_file(self.cache_fname)
            if status is not True:
                msg = "Loading cache file failed, reloading data from Chess-Scape nc files."
                self.logger.debug(msg)
                # Loading cache file failed!
                self._get_and_process_ChessScape()
        else:
            # Cache file is too old. Try loading new data from ChessScape
            try:
                msg = "Cache file older then 90 days, reloading from Chess-Scape nc files."
                self.logger.debug(msg)
                self._get_and_process_ChessScape()
            except Exception as e:
                msg = ("Reloading data from Chess-Scape nc files failed, reverting to (outdated) " +
                       "cache file")
                self.logger.debug(msg)
                status = self._load_cache_file(self.cache_fname)
                if status is not True:
                    msg = "Outdated cache file failed loading."
                    raise PCSEError(msg)
        
    def _create_header(self):
        country = 'Great Britain'
        station = self.osgrid_1km
        desc =  f'Projected weather for OS tile \'{self.osgrid_1km}\', {self.rcp} and ensemble {self.ensemble}'
        src = 'UK Centre for Ecology and Hydrology'
        contact = 'Emma Robinson at emrobi@ceh.ac.uk'
        self.description = [u"Weather data for:",
                            u"Country: %s" % country,
                            u"Station: %s" % station,
                            u"Description: %s" % desc,
                            u"Source: %s" % src,
                            u"Contact: %s" % contact]
    
    def _get_and_process_ChessScape(self):

        # Initial preparation of weather data
        x, y = osgrid2lonlat(self.osgrid_1km)
        os_array = xr.open_dataset(self.nc_fname)

        os_dataframe = os_array.sel(x=x, y=y, method="nearest").to_dataframe().reset_index()
        # There is  a posibility that the assignment of weather data to parcels  near the coastline 
        # could result in empty data (nan). This is because the .sel("closest") method in xarray is 
        # based on the x-y coordinates, regardless of whether the arrays at those coordinates are 
        # empty or not. Deal with this selecting the closest non-null cell. (Euclidean distance)
        if os_dataframe.isnull().any().any():
            os_array.sel(x=x, y=y, method="nearest").to_dataframe().reset_index()
            os_dataframe = os_array.where((os_array.x >= x-5000) & 
                                          (os_array.x < x+5000) &
                                          (os_array.y >= y-5000) &
                                          (os_array.y < y+5000), drop=True).to_dataframe().reset_index()
            os_dataframe = os_dataframe.dropna()
            unique_combinations = os_dataframe[['y', 'x']].drop_duplicates().to_dict(orient='records') 
            closest = find_closest_point(unique_combinations, x, y)
            os_dataframe = os_dataframe[(os_dataframe['x'] == closest['x']) & (os_dataframe['y'] == closest['y'])]
        # rh to vapour pressure in hPa
        vap = [rh_to_vpress(x, y) for x, y in zip(os_dataframe['hurs'], os_dataframe['tas'] - 273.15)]
        # remove unnecesary columns and rename the remaining ones
        os_dataframe = os_dataframe[os_dataframe.columns.drop(['lat', 'lon', 'x', 'y', 'tas', 'rlds', 'rsds', 'hurs'])]
        os_dataframe.columns = ['DAY', 'TMAX', 'TMIN', 'RAIN', 'WIND', 'IRRAD']
        os_dataframe['SNOWDEPTH'] = -999
        os_dataframe['VAP'] = vap

        # chess-scape data is based on 360 day years, which breaks Wofost. 
        # Convert to datetime and interpolate missing data
        os_dataframe['DAY'] = [calc_doy(x) for x in os_dataframe['DAY']]
        os_dataframe.set_index(['DAY'], inplace=True)   
        date_rng = pd.date_range(os_dataframe.index[0], os_dataframe.index[-1], freq='D')
        date_rng = [x.date() for x in date_rng]
        missing_days = list(set(date_rng).difference(os_dataframe.index))
        for day in missing_days:
            nearest_day = nearest(day, os_dataframe.index)
            nearest_vals = os_dataframe.loc[nearest_day,:].to_frame().transpose().reset_index()
            nearest_vals['index'] = day
            nearest_vals.set_index('index', inplace=True)
            nearest_vals.index.rename('DAY', inplace=True)
            os_dataframe = pd.concat([os_dataframe, nearest_vals])
        
        os_dataframe.sort_index(ascending=True, inplace=True)

        # adjust irradiation for lenght of the day
        daylength = sun(lat=self.latitude, long=self.longitude)
        os_dataframe['IRRAD'] = os_dataframe['IRRAD'] * [daylength.daylength(day)*3600 for day in os_dataframe.index]
        self._read_observations(os_dataframe)

        # dump contents to a cache file
        cache_filename = self._get_cache_filename(self.cache_fname)
        self._dump(cache_filename)


    def _read_observations(self, os_dataframe):
        df = os_dataframe.reset_index()

        # First get the column labels
        labels = list(df.columns)

        # Start reading all rows with data
        # rownums = list(range(sheet.nrows))
        for row in range(len(df)):
            try:
                d = {}
                for label in labels:
                    if label == "DAY":
                        if df.iloc[row,:][label] is None:
                            raise ValueError
                        else:
                            doy = df.iloc[row,:][label]
                            d[label] = doy
                            continue

                    # explicitly convert to float. If this fails a ValueError will be thrown
                    value = df.iloc[row,:][label]

                    # Check for observations marked as missing. Currently only missing
                    # data is allowed for SNOWDEPTH. Otherwise raise an error
                    if self._is_missing_value(value):
                        if label == "SNOWDEPTH":
                            value = self.missing_snow_depth
                        else:
                            raise ValueError()

                    func = self.obs_conversions[label]
                    d[label] = func(value)

                # Reference ET in mm/day
                e0, es0, et0 = reference_ET(LAT=self.latitude, ELEV=self.elevation, ANGSTA=self.angstA,
                                            ANGSTB=self.angstB, **d)
                # convert to cm/day
                d["E0"] = e0/10.; d["ES0"] = es0/10.; d["ET0"] = et0/10.

                wdc = WeatherDataContainer(LAT=self.latitude, LON=self.longitude, ELEV=self.elevation, **d)
                self._store_WeatherDataContainer(wdc, d["DAY"])

            except ValueError as e:  # strange value in cell
                msg = "Failed reading row: %i. Skipping..." % (row)
                self.logger.warn(msg)
                print(msg)


    def _find_cache_file(self, cache_fname):
        """Try to find a cache file for given latitude/longitude.

        Returns None if the cache file does not exist, else it returns the full path
        to the cache file.
        """
        cache_filename = self._get_cache_filename(cache_fname)
        if os.path.exists(cache_filename):
            return cache_filename
        else:
            return None
    
    def _get_cache_filename(self, cache_fname):
        """Constructs the filename used for cache files given latitude and longitude

        The file name is constructed combining the class name, the OS 1km tile
        code, the rcp code and the ensemble 
        (i.e.: NetCDFWeatherDataProvider_SX7347_rcp26_01.cache)
        """
        fname = "%s_%s.cache" % (self.__class__.__name__, cache_fname)
        cache_filename = os.path.join(settings.METEO_CACHE_DIR, fname)
        return cache_filename

    def _load_cache_file(self, cache_fname):
        """Loads the data from the cache file. Return True if successful.
        """
        cache_filename = self._get_cache_filename(cache_fname)
        try:
            self._load(cache_filename)
            msg = "Cache file successfully loaded."
            self.logger.debug(msg)
            return True
        except (IOError, EnvironmentError, EOFError) as e:
            msg = "Failed to load cache from file '%s' due to: %s" % (cache_filename, e)
            self.logger.warning(msg)
            return False

    def _is_missing_value(self, value):
        """Checks if value is equal to the value specified for missing date
        :return: True|False
        """
        eps = 0.0001
        if abs(value - self.nodata_value) < eps:
            return True
        else:
            return False

# construct a class to deal with soil data from a variety of providers
class SoilDataProvider(object):
    """
    Base class for all soil data providers.
    """
    pass