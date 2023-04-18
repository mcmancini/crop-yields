from math import exp, log, cos, sin, acos, asin, tan, floor 
from math import degrees as deg, radians as rad  
from datetime import date, datetime, time
from pyproj import Transformer
import re

class BNGError(Exception):
    """Exception raised by bng.py module"""
    pass

def _init_regions_and_offsets():
    # Region codes for 100 km grid squares.
    regions = [['HL', 'HM', 'HN', 'HO', 'HP', 'JL', 'JM'],
               ['HQ', 'HR', 'HS', 'HT', 'HU', 'JQ', 'JR'],
               ['HV', 'HW', 'HX', 'HY', 'HZ', 'JV', 'JW'],
               ['NA', 'NB', 'NC', 'ND', 'NE', 'OA', 'OB'],
               ['NF', 'NG', 'NH', 'NJ', 'NK', 'OF', 'OG'],
               ['NL', 'NM', 'NN', 'NO', 'NP', 'OL', 'OM'],
               ['NQ', 'NR', 'NS', 'NT', 'NU', 'OQ', 'OR'],
               ['NV', 'NW', 'NX', 'NY', 'NZ', 'OV', 'OW'],
               ['SA', 'SB', 'SC', 'SD', 'SE', 'TA', 'TB'],
               ['SF', 'SG', 'SH', 'SJ', 'SK', 'TF', 'TG'],
               ['SL', 'SM', 'SN', 'SO', 'SP', 'TL', 'TM'],
               ['SQ', 'SR', 'SS', 'ST', 'SU', 'TQ', 'TR'],
               ['SV', 'SW', 'SX', 'SY', 'SZ', 'TV', 'TW']]

    # Transpose so that index corresponds to offset
    regions = list(zip(*regions[::-1]))

    # Create mapping to access offsets from region codes
    offset_map = {}
    for i in range(len(regions)):
        for j in range(len(regions[0])):
            region = regions[i][j]
            offset_map[region] = (1e5 * i, 1e5 * j)

    return regions, offset_map

_regions, _offset_map = _init_regions_and_offsets()

def lonlat2osgrid(coords, figs=4):
    """
    Convert WGS84 lon-lat coordinates to British National Grid references.
    Grid references can be 4, 6, 8 or 10 fig, specified by the figs keyword.
    Adapted from John A. Stevenson's 'bng' package that can be found at
    https://pypi.org/project/bng/

    :param coords: tuple - x, y coordinates to convert
    :param figs: int - number of figures to output
    :return gridref: str - BNG grid reference

    Examples:

    Single value
    >>> lonlat2osgrid((-5.21469 49.96745))

    For multiple values, use Python's zip function and list comprehension
    >>> x = [-5.21469, -5.20077, -5.18684]
    >>> y = [49.96745, 49.96783, 49.96822]
    >>> [lonlat2osgrid(coords, figs=4) for coords in zip(x, y)]
    """
    # Validate input
    bad_input_message = ('Valid inputs are x, y tuple e.g. (-5.21469, 49.96783),'
                         ' or list of x, y tuples. [{}]'.format(coords))

    if not isinstance(coords, tuple):
        raise BNGError(bad_input_message)

    try:
        # convert to WGS84 to OSGB36 (EPSG:27700)
        transformer = Transformer.from_crs(4326, 27700, always_xy=True)
        x1, y1 = coords[0], coords[1]
        x2, y2 = transformer.transform(x1, y1)
        coords_reproj = (x2, y2)
        x, y = coords_reproj
    except ValueError:
        raise BNGError(bad_input_message)

    out_of_region_message = (
        'Coordinate location outside UK region: {}'.format(coords))
    if (x < 0) or (y < 0):
        raise BNGError(out_of_region_message)

    # Calculate region and SW corner offset
    x_index = int(floor(x / 100000.0))
    y_index = int(floor(y / 100000.0))
    try:
        region = _regions[x_index][y_index]
        x_offset, y_offset = _offset_map[region]
    except IndexError:
        raise BNGError(out_of_region_message)

    # Format the output based on figs
    templates = {4: '{}{:02}{:02}', 6: '{}{:03}{:03}',
                 8: '{}{:04}{:04}', 10: '{}{:05}{:05}'}
    factors = {4: 1000.0, 6: 100.0, 8: 10.0, 10: 1.0}
    try:  # Catch bad number of figures
        coords = templates[figs].format(
            region,
            int(floor((x - x_offset) / factors[figs])),
            int(floor((y - y_offset) / factors[figs]))
        )
    except KeyError:
        raise BNGError('Valid inputs for figs are 4, 6, 8 or 10')

    return coords

def osgrid2bbox(gridref, OS_cellsize):
    """
    Convert British National Grid references to OSGB36 numeric coordinates.
    of the bounding box of the 10km grid or 100km grid squares.
    Grid references can be 2, 4, 6, 8 or 10 figures.

    :param gridref: str - BNG grid reference
    :returns coords: dictionary {xmin, xmax, ymin, ymax}

    Examples:

    Single value
    >>> osgrid2bbox('NT2755072950', '10km')
    {'xmin': 320000, 'xmax': 330000, 'ymin': 670000, 'ymax': 680000}

    For multiple values, use Python's zip function and list comprehension
    >>> gridrefs = ['HU431392', 'SJ637560', 'TV374354']
    >>> [osgrid2bbox(g, '10km') for g in gridrefs]
    >>> [{'xmin': 440000, 'xmax': 450000, 'ymin': 1130000, 'ymax': 1140000}, 
        {'xmin': 360000, 'xmax': 370000, 'ymin': 330000, 'ymax': 340000}, 
        {'xmin': 530000, 'xmax': 540000, 'ymin': 70000, 'ymax': 80000}]
    """
    # Validate input
    bad_input_message = (
        'Valid gridref inputs are 2 characters and none, 2, 4, 6, 8 or 10-fig references as strings '
        'e.g. "NN123321", or lists/tuples/arrays of strings. '
        '[{}]'.format(gridref))

    gridref = gridref.upper()
    if OS_cellsize == '10km':
        try:
            pattern = r'^([A-Z]{2})(\d{2}|\d{4}|\d{6}|\d{8}|\d{10})$'
            match = re.match(pattern, gridref)
            # Extract data from gridref
            region, coords = match.groups()
        except (TypeError, AttributeError):
            # Non-string values will throw error
            raise BNGError(bad_input_message)
    elif OS_cellsize == '100km':
        try:
            pattern = r'^([A-Z]{2})'
            match = re.match(pattern, gridref)
            # Extract data from gridref
            region = match.groups()[0]
        except (TypeError, AttributeError):
            raise BNGError(bad_input_message)
    else:
        raise BNGError('Invalid argument \'OS_cellsize\' supplied: values can only be \'10km\' or \'100km\'')

    # Get offset from region
    try:
        x_offset, y_offset = _offset_map[region]
    except KeyError:
        raise BNGError('Invalid grid square code: {}'.format(region))
    
    # Get easting and northing from text and convert to coords
    if OS_cellsize == '10km':
        coords = coords[0:2] # bbox is for each 10km cell!
        half_figs = len(coords) // 2
        easting, northing = int(coords[:half_figs]), int(coords[half_figs:])
        scale_factor = 10 ** (5 - half_figs)
        x_min = int(easting * scale_factor + x_offset)
        y_min = int(northing * scale_factor + y_offset)
        x_max = int(easting * scale_factor + x_offset + 1e4)
        y_max = int(northing * scale_factor + y_offset + 1e4)
    elif OS_cellsize == '100km':
        x_min = int(x_offset)
        y_min = int(y_offset)
        x_max = int(x_offset + 1e5)
        y_max = int(y_offset + 1e5)
    else:
        raise BNGError('Invalid argument \'OS_cellsize\' supplied: values can only be \'10km\' or \'100km\'')

    return {
        'xmin': x_min,
        'xmax': x_max,
        'ymin': y_min,
        'ymax': y_max
    }

def osgrid2lonlat(gridref, EPSG=None):
    """
    Convert British National Grid references to OSGB36 numeric coordinates.
    Grid references can be 4, 6, 8 or 10 figures.

    :param gridref: str - BNG grid reference
    :returns coords: tuple - x, y coordinates

    Examples:

    Single value
    >>> osgrid2lonlat('NT2755072950')
    (327550, 672950)

    For multiple values, use Python's zip function and list comprehension
    >>> gridrefs = ['HU431392', 'SJ637560', 'TV374354']
    >>> x, y = zip(*[osgrid2lonlat(g) for g in gridrefs])
    >>> x
    (443100, 363700, 537400)
    >>> y
    (1139200, 356000, 35400)
    """
    # Validate input
    bad_input_message = (
        'Valid gridref inputs are 4, 6, 8 or 10-fig references as strings '
        'e.g. "NN123321", or lists/tuples/arrays of strings. '
        '[{}]'.format(gridref))

    try:
        gridref = gridref.upper()
        pattern = r'^([A-Z]{2})(\d{4}|\d{6}|\d{8}|\d{10})$'
        match = re.match(pattern, gridref)
    except (TypeError, AttributeError):
        # Non-string values will throw error
        raise BNGError(bad_input_message)

    if not match:
        raise BNGError(bad_input_message)

    # Extract data from gridref
    region, coords = match.groups()

    # Get offset from region
    try:
        x_offset, y_offset = _offset_map[region]
    except KeyError:
        raise BNGError('Invalid 100 km grid square code: {}'.format(region))

    # Get easting and northing from text and convert to coords
    half_figs = len(coords) // 2
    easting, northing = int(coords[:half_figs]), int(coords[half_figs:])
    scale_factor = 10 ** (5 - half_figs)
    x = int(easting * scale_factor + x_offset)
    y = int(northing * scale_factor + y_offset)

    if EPSG == None:
        return x, y
    elif EPSG == 27700:
        transformer = Transformer.from_crs(27700, 4326, always_xy=True)
        x1, y1 = transformer.transform(x, y)
        coords_reproj = (x1, y1)
        x1, y1 = coords_reproj
        return x1, y1
    else:
        print('Optional EPSG argument can only take value of 27700')

class sun:  
    """  
    Calculate duration of the day based on NOAA
    https://gml.noaa.gov/grad/solcalc/calcdetails.html

    Typical use 
    -----------
    from datetime import date
    a = sun(lat=41.0082, long=28.9784)
    when = date(2022, 10, 14)
    print('sunrise at ', a.sunrise(when))
    print('sunset at ', a.sunset(when)) 
    print(f'day length of {a.daylength(when)} hours')

    """  
    def __init__(self,lat=50.7260,long=3.5275): # default Exeter  
        self.lat=lat  
        self.long=long  
    
    def daylength(self, when):
        """ 
        return the length in hours (decimal) of the day 
        specified in 'when', for lat and long, and passed
         as a datetime.date object.
        """
        self.__preptime(when)
        self.__calc()  
        return sun.__lengthfromdecimaldiff(self.daylength_t)
    
    def sunrise(self, when):
        '''Return time of sunrise, UTC'''
        self.__preptime(when)
        self.__calc()  
        return sun.__timefromdecimal(self.sunrise_t)
    
    def sunset(self, when):
        '''Return time of sunset, UTC'''
        self.__preptime(when)
        self.__calc()  
        return sun.__timefromdecimal(self.sunset_t)
    
    def noon(self, when):
        '''Return time of solar noon, UTC'''
        self.__preptime(when)
        self.__calc()  
        return sun.__timefromdecimal(self.solarnoon_t)

    @staticmethod
    def __timefromdecimal(day):  
        """ 
        returns a datetime.time object. 
        day is a decimal day between 0.0 and 1.0, e.g. noon = 0.5 
        """  
        hours   = 24.0*day  
        h       = int(hours)  
        minutes = (hours-h)*60  
        m       = int(minutes)  
        seconds = (minutes-m)*60  
        s       = int(seconds)  
        return time(hour=h,minute=m,second=s) 

    @staticmethod  
    def __lengthfromdecimaldiff(hours):
        '''Return a number of hours from a decimal length of a day'''
        return hours*24  

    def __preptime(self,when):  
        """ 
        Extract information in a suitable format from when,  
        a datetime.date object. 
        """  
        # datetime days are numbered in the Gregorian calendar  
        # while the calculations from NOAA are distibuted as  
        # OpenOffice spreadsheets with days numbered from  
        # 1/1/1900. The difference are those numbers taken for   
        # 18/12/2010  
        dtime = datetime.combine(when, time(12, 0, 0))
        self.day = dtime.toordinal()-(734123-40529)
        t = dtime.time()  
        self.time = (t.hour + t.minute/60.0 + t.second/3600.0)/24.0  
    
        self.timezone=0  
        offset=dtime.utcoffset()  
        if not offset is None:  
            self.timezone=offset.seconds/3600.0  

    def __calc(self):  
        """ 
        Perform the actual calculations for sunrise, sunset and 
        a number of related quantities. 
        The results are stored in the instance variables 
        sunrise_t, sunset_t and solarnoon_t 
        """  
        timezone  = self.timezone # in hours, east is positive  
        longitude = self.long     # in decimal degrees, east is positive  
        latitude  = self.lat      # in decimal degrees, north is positive  

        time      = self.time # percentage past midnight, i.e. noon  is 0.5  
        day       = self.day     # daynumber 1=1/1/1900  
        Jday      = day+2415018.5+time-timezone/24  
        Jcent     = (Jday-2451545)/36525    # Julian century  
        GMLS      = (280.46646+Jcent*(36000.76983 + Jcent*0.0003032)) % 360
        GMAS      = 357.52911+Jcent*(35999.05029 - 0.0001537*Jcent)
        EEO       = 0.016708634-Jcent*(0.000042037+0.0000001267*Jcent)
        Seqcent   = sin(rad(GMAS))*(1.914602-Jcent*(0.004817+0.000014*Jcent))+sin(rad(2*GMAS))*(0.019993-0.000101*Jcent)+sin(rad(3*GMAS))*0.000289
        Struelong = GMLS + Seqcent
        Sapplong  = Struelong-0.00569-0.00478*sin(rad(125.04-1934.136*Jcent))
        Mobec     = 23+(26+((21.448-Jcent*(46.815+Jcent*(0.00059-Jcent*0.001813))))/60)/60
        Obcorr    = Mobec+0.00256*cos(rad(125.04-1934.136*Jcent))
        Sdec      = deg(asin(sin(rad(Obcorr))*sin(rad(Sapplong))))
        var_y     = tan(rad(Obcorr/2))*tan(rad(Obcorr/2))
        T_eq      = 4*deg(var_y*sin(2*rad(GMLS))-2*EEO*sin(rad(GMAS))+4*EEO*var_y*sin(rad(GMAS))*cos(2*rad(GMLS))-0.5*var_y*var_y*sin(4*rad(GMLS))-1.25*EEO*EEO*sin(2*rad(GMAS)))
        HA_srise  = deg(acos(cos(rad(90.833))/(cos(rad(latitude))*cos(rad(Sdec)))-tan(rad(latitude))*tan(rad(Sdec))))
        self.solarnoon_t  = (720-4*longitude-T_eq+timezone*60)/1440
        self.sunrise_t    = (self.solarnoon_t*1440-HA_srise*4)/1440
        self.sunset_t     = (self.solarnoon_t*1440+HA_srise*4)/1440
        self.daylength_t  = self.sunset_t - self.sunrise_t

# Convert relative humidity to vapour pressure
def rh_to_vpress(rh, temp):
    '''
    Conversion from relative humidity to vapour pressure
    in hPa (or mm) using the Clausius-Clapeyron relationship
    See https://bit.ly/3e4VZKI (Hartmann, 1994). The latent
    heat of vaporization depends on temperature as well. Use
    curve from Osborne et al. (1930, 1937), obtained from
    https://bit.ly/2LXYLAO
    '''
    t = (0.01, 2, 4, 10, 14, 18, 20, 25, 30, 34, 40, 44, 50)
    hvap = (2500.9, 2496.2, 2491.4, 2477.2, 2467.7, 2458.3, 
        2453.5, 2441.7, 2429.8, 2420.3, 2406.0, 2396.4, 2381.9)
    nearest_t_idx = min(range(len(t)), key=lambda i: abs(t[i]-(temp)))
    vps = 6.11 * exp(((hvap[nearest_t_idx]*1E3)/461)*(1/273.15 - 1/(temp+273.15)))
    vp = vps * (rh/100)
    return vp

# rescale windspeed based on measured height to a height of 2m
def rescale_windspeed(windspeed, measured_height):
    '''
    Estimate wind speed at 2m height from wind speed measured
    at 'measured_height'.
    UKCP18 wind speed is been estimated at a height of 10m but
    the Penman equation requires wind values at 2m height.
    Conversion is done with the formula presented in 
    https://bit.ly/3fOP34P
    Notes: windspeeds must be in m/s
    '''
    ws = windspeed * (4.87/log(67.8*measured_height - 5.42))
    return ws

# Calculate net radiation over water from total radiation fluxes (long and short wave)
def net_radiation(shortwave_flux, longwave_flux, day_length):
    '''
    Calculate net radiation at the surface summing total shortwave and 
    longwave fluxes (these are the total downward fluxes: rsds and rlds,
    d for downward). Convert values from W/m2 to J/m2/d based on the
    length of the day in decimal hours. Cloud cover has already been 
    accounted for in the magnitude of fluxes

    '''
    tot_rad = shortwave_flux + longwave_flux
    irrad = tot_rad * day_length * 3600
    return irrad

def find_closest_climcell_ID(parcel_centroid, climate_cells):
    '''
    Given a parcel and its centroid, find the ID of the closest 
    Chess-Scape climate cell.
    Both parcel_centroid and climate_cells must be spatial objects
    (GeoPandas); wihle the parcel centroid is a single point,
    climate_cells is a spatial series of all Chess-Scape cells.
    '''
    dst = [parcel_centroid.distance(climate_cells.values[ind]) for ind in range(climate_cells.shape[0])]
    (val,idx) = min((val,idx) for idx,val in enumerate(dst))
    return idx

# Progress bar
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Progress bar: from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

# Converts 360 day based datetime to 365 day based datetime
def calc_doy(cftime_day):
    """
    Converts a 360-based datetime object (cfttime) to a standard
    datetime object. The assumption here is that hte last 5 days
    of December in a given year are missing.
    """
    doy = date.fromordinal(cftime_day.dayofyr)
    doy = doy.replace(year=cftime_day.year)
    return doy

# find nearest value within a list to a given value
def nearest(item, valuelist):
    """
    Find nearest value to item in valuelist
    """
    return min(valuelist, key=lambda x: abs(x - item))