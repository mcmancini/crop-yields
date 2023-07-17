from pcse.fileinput import YAMLAgroManagementReader
import datetime as dt
import yaml

class SingleRotationAgroManager(YAMLAgroManagementReader):
    """
    Class based on the YAMLAgromanagementReader that 
    allows to easily alter agromanagement parameters without 
    having to create a new YAML file
    --------------------------------------------------------
    Methods:
    - change_year: Change calendar year of single rotation crop. It takes
        the following parameters:
        :param new_year: how many years to sum to the base year. 
               Base year can be retrieved using the retrieve_year property
    - change_variety: Change calendar year of single rotation crop. It takes
        the following parameters:
        :param new_variety: new variety to replace the base one
               Base variety can be retrieved using the retrieve_variety property
    """
    def __init__(self, fname):
        YAMLAgroManagementReader.__init__(self, fname)

    @property
    def retrieve_year(self):
        calendar_years = [date.year for dictionary in self for date in dictionary.keys() if isinstance(date, dt.date)]
        return calendar_years[0]
    
    @property
    def retrieve_variety(self):
        variety_names = [item[date_key]['CropCalendar']['variety_name'] if item[date_key]['CropCalendar'] else None for item in self for date_key in item]
        variety_names = [item for item in variety_names if item is not None]
        return variety_names[0]

    
    def change_year(self, new_year):
        """
        Change calendar year of single rotation crop.
        """
        calendar_year = self.retrieve_year
        year_increment = new_year - calendar_year
        modified_list = []
        for item in self:
            modified_item = {}
            for key, value in item.items():
                if isinstance(key, dt.date):
                    new_date = key.replace(year=key.year + year_increment)
                    modified_item[new_date] = self._recursively_change_year(value, year_increment)
                else:
                    modified_item[key] = self._recursively_change_year(value, year_increment)
            modified_list.append(modified_item)
        self.clear()
        self.extend(modified_list)

    def _recursively_change_year(self, obj, year_increment):
        if isinstance(obj, dict):
            modified_dict = {}
            for k, v in obj.items():
                if isinstance(k, dt.date):
                    new_key = k.replace(year=k.year + year_increment)
                else:
                    new_key = k

                if isinstance(v, (dict, list)):
                    modified_dict[new_key] = self._recursively_change_year(v, year_increment)
                elif isinstance(v, dt.date):
                    new_date = v.replace(year=v.year + year_increment)
                    modified_dict[new_key] = new_date
                else:
                    modified_dict[new_key] = v
            return modified_dict
        elif isinstance(obj, list):
            modified_list = []
            for item in obj:
                modified_item = self._recursively_change_year(item, year_increment)
                modified_list.append(modified_item)
            return modified_list
        else:
            return obj
        
    def change_variety(self, new_variety):
        """
        Change variety for the crop to be run in a single rotation
        """
        for item in self:
            for date_key in item:
                if 'CropCalendar' in item[date_key] and item[date_key]['CropCalendar'] is not None:
                    item[date_key]['CropCalendar']['variety_name'] = new_variety

        
class YamlAgromanager:
    """
    Class based on the definition of a standard YAML template 
    that allows to easily access and alter agromanagement 
    parameters programmatically
    """
    DEFAULT_START_YEAR = 2022

    DEFAULT_ARGS = {
        'start_year': DEFAULT_START_YEAR,
        'crop': "wheat",
        'variety': "Winter_wheat_106",
        'crop_start_date': dt.date(DEFAULT_START_YEAR, 9, 1),
        'year': DEFAULT_START_YEAR + 1,
        'month_1': 3,
        'month_2': 4,
        'month_3': 5,
        'day_1': 20, 
        'day_2': 1, 
        'day_3': 1,
        'N_amount_1': 60, 
        'N_amount_2': 100, 
        'N_amount_3': 50,
        'P_amount_1': 3, 
        'P_amount_2': 13, 
        'P_amount_3': 23,
        'K_amount_1': 4, 
        'K_amount_2': 14, 
        'K_amount_3': 24
    }

    _agromanagement_yaml = f"""
    AgroManagement:
    - {DEFAULT_ARGS['start_year']}-09-01:
        CropCalendar:
            crop_name: {DEFAULT_ARGS['crop']}
            variety_name: {DEFAULT_ARGS['variety']}
            crop_start_date: {DEFAULT_ARGS['crop_start_date']}
            crop_start_type: sowing
            crop_end_date:
            crop_end_type: maturity
            max_duration: 365
        TimedEvents:
        -   event_signal: apply_npk
            name:  Timed N/P/K application table
            comment: All fertilizer amounts in kg/ha
            events_table:
            - {DEFAULT_ARGS['year']}-{DEFAULT_ARGS['month_1']:02d}-{DEFAULT_ARGS['day_1']:02d}: {{N_amount: {DEFAULT_ARGS['N_amount_1']}, P_amount: {DEFAULT_ARGS['P_amount_1']}, K_amount: {DEFAULT_ARGS['K_amount_1']}}}
            - {DEFAULT_ARGS['year']}-{DEFAULT_ARGS['month_2']:02d}-{DEFAULT_ARGS['day_2']:02d}: {{N_amount: {DEFAULT_ARGS['N_amount_2']}, P_amount: {DEFAULT_ARGS['P_amount_2']}, K_amount: {DEFAULT_ARGS['K_amount_2']}}}
            - {DEFAULT_ARGS['year']}-{DEFAULT_ARGS['month_3']:02d}-{DEFAULT_ARGS['day_3']:02d}: {{N_amount: {DEFAULT_ARGS['N_amount_3']}, P_amount: {DEFAULT_ARGS['P_amount_3']}, K_amount: {DEFAULT_ARGS['K_amount_3']}}}
        StateEvents: Null
    - {DEFAULT_ARGS['year']}-09-01:
    """


    def __init__(self, yaml_string=None):
        if yaml_string is None:
            yaml_string = self._agromanagement_yaml
        else:
            yaml_string = yaml_string
        self.yaml_dict = yaml.safe_load(yaml_string)


    def find_value(self, key):
        """
        Find value associated to 'key', if existing
        """
        result = self._recursive_search(self.yaml_dict, key)
        if result is None:
            print(f"Key '{key}' not found in the dictionary.")
        return result

    def _recursive_search(self, data, key):
        """
        Recursive search into yaml_dict to find specified key
        regardless of level of nesting into yaml_dict
        """
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key:
                    return v
                elif isinstance(v, (dict, list)):
                    result = self._recursive_search(v, key)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    result = self._recursive_search(item, key)
                    if result is not None:
                        return result
        return None


class Crop:
    """
    General crop class that includes standard agromanagement
    which can be altered if in a rotation, or due to 
    specific farm management practices. This class handles 
    both arable crops and grasslands (for the time being only 
    rye grass has been parametrised). A crop is instantiated 
    as follows: wheat = Crop(2023, 'wheat', **wheat_args)
    ------------------------------------------------------------
    The required parameters are as follows:
    : param calendar_year: the year in which the crop is grown.
            For a winter crop, the calendar year is the year in 
            which the crop is established in the ground; harvest
            will happen the following year. For spring crops, 
            the entire crop cycle happens in the calendar_year.
    : param crop: name of the crop to be cultivated. It needs to 
            match the name of any of the parametrised WOFOST crops
    : param **kwargs: these are key-value pairs of parameters, some
            of which are required, some optional.
    - Required **kwargs:
    : param 'variety': required only for arable crops and grassland,
        but not for 'fallow' crop. The variety name must match
        the varieties included in the parametrised WOFOST crops.
    - Optional **kwargs:
    : param 'apply_npk': a dictionary of dictionaries containing
            fertilisation events defined as follows:
            kwargs['apply_npk'] = [npk_1, ...] where
            npk_1 = {
                'month': 5,
                'day': 1,
                'N_amount': 40, #kg/ha
                'P_amount': 40, #kg/ha
                'K_amount': 40  #kg/ha
            }
            Multiple fertilisation events can be defined
    : param 'mowing': for grassland. A list of dictionaries
            containing grass defoliation events defined as follows:
            kwargs['mowing'] = [mowing_1, ...] where
            mowing_1 = {
                'month': 5,
                'day': 1,
                'biomass_remaining': 320 #kg/ha
            } 
            Multiple grass defoliation events can be defined.
    : param 'num_years' for grassland: Duration in years of the grassland
            crop. If grass is in a rotation with other crops, then the crops
            after grassland need to be planted after 'num_years' of the grassland
    Any other aprameter in the agromanagement can be overwritten: e.g.:
    : param 'crop_start_date': sowing date of a crop (dt.date format)
    : param 'crop_end_date': harvest time if timed, rather than dependent
            on the phenological development of the crop
    : param 'max_duration': max duration of the crop in days
    : params 'TimedEvents': list of events defined by their timing
    : params 'StateEvents': list of events depending on phenology rather than 
             timing. More information on agromanagment can be found on 
             https://github.com/ajwdewit/pcse_notebooks/blob/master/06_advanced_agromanagement_with_PCSE.ipynb
    """

    DEFAULT_ARGS = {
        'TimedEvents': 'Null'
    }

    
    def __init__(self, calendar_year, crop, **kwargs):
        self.crop = crop
        self.crop_type = self._categorize_crop()
        self.calendar_year = calendar_year
        self.agromanagement = self._generate_agromanagement(**kwargs)
    

    def _generate_agromanagement(self, **kwargs):
        """
        Generate agromanagement data for a specified crop. This includes 
        crop calendar year, sowing timing, and timing of agromanagement 
        practices (fertilisation, mowing, irrigation). Agromanagement
        events can be define thrugh **kwargs or can be default ones for 
        specified crops. Defaults are contained in the config.py file, and 
        called in the creation of crop instances
        """
        args = self.DEFAULT_ARGS.copy()
        args.update(kwargs)

        # Variety
        if  self.crop.lower() != 'fallow':
            if 'variety'not in args or args['variety'] is None:
                raise ValueError("Missing argument: \'variety\' argument is required.") 
            else:
                self.variety = args['variety']

        # Start of the crop
        if self.crop.lower() != 'fallow':
            if 'crop_start_date'not in args:
                if ('crop_start_month' not in args and 'crop_start_day' not in args):
                    raise ValueError(f"Please provide a crop start date for {self.crop} as kwargs['crop_start_day'] and kwargs['crop_start_month'] or kwargs['crop_start_date']")
                else:
                    start_crop_calendar = dt.date(self.calendar_year, args['crop_start_month'], 1)
                    crop_start_date = dt.date(self.calendar_year, args['crop_start_month'], args['crop_start_day'])
                    args['start_crop_calendar'] = start_crop_calendar
                    args['crop_start_date'] = crop_start_date
            else:
                crop_start_date = args['crop_start_date']
                args['start_crop_calendar'] = dt.date(crop_start_date.year, crop_start_date.month, 1)
        else:
            if 'start_crop_calendar' not in args:
                if ('crop_start_month' not in args and 'crop_start_day' not in args):
                    raise ValueError("Please provide a calendar start date for \'fallow\' as kwargs['start_crop_calendar'] or kwargs['crop_start_day'] and kwargs['crop_start_month']")
            else:
                 args['crop_start_date'] = "None"
        
        event_types = {
            'apply_npk': {
                'event_signal': 'apply_npk',
                'name': 'Timed N/P/K application table',
                'comment': 'All fertilizer amounts in kg/ha',
                'line_template': "- {timing}: {{N_amount: {event[N_amount]}, P_amount: {event[P_amount]}, K_amount: {event[K_amount]}}}"
            },
            'mowing': {
                'event_signal': 'mowing',
                'name': 'Schedule a grass mowing event',
                'comment': 'Remaining biomass in kg/ha',
                'line_template': "- {timing}: {{biomass_remaining: {event[biomass_remaining]}}}"
            }
        }

        event_yaml_lines = []

        for event_type, event_data in event_types.items():
            if event_type in args and args[event_type] is not None:
                event_lines = []
                for event in args[event_type]:
                    timing = self._def_timing_event(self.variety, args['crop_start_date'], event)
                    line = event_data['line_template'].format(timing=timing, event=event)
                    event_lines.append(line)
                events_table = '\n                    '.join(event_lines)

                event_yaml = f"""
                -   event_signal: {event_data['event_signal']}
                    name: {event_data['name']}
                    comment: {event_data['comment']}
                    events_table:
                    {events_table}
                """
                event_yaml_lines.append(event_yaml)

        # Combine all event YAMLs
        events_yaml = '\n'.join(event_yaml_lines)

        # Combine all in agromanagement
        if self.crop != 'fallow':
            _agromanagement_yaml = f"""
            - {args['start_crop_calendar']}:
                CropCalendar:
                    crop_name: {self.crop}
                    variety_name: {self.variety}
                    crop_start_date: {args['crop_start_date']}
                    crop_start_type: sowing
                    crop_end_date:
                    crop_end_type: {args['crop_end_type']}
                    max_duration: {args['max_duration']}
                TimedEvents:
                    {events_yaml}
                StateEvents: Null
            """
        else:
            _agromanagement_yaml = f"""
            - {args['start_crop_calendar']}:
                CropCalendar: null
                TimedEvents: null
                StateEvents: null
            """

        # Remove empty lines
        _agromanagement_yaml = '\n'.join([line for line in _agromanagement_yaml.split('\n') if line.strip()])
        return _agromanagement_yaml
    

    @staticmethod
    def _def_timing_event(variety, crop_start_date, event):
        """
        Generate date of timing event combining calendar year of a crop and 
        timing (month and day) passed trough crop **kwargs. These can be
        fertilisation, mowing or irrigation events. 
        """
        if 'winter' in variety.lower():
            if 'date' not in event:
                timing = dt.date(crop_start_date.year + 1, event['month'], event['day'])
            else:
                timing = event['date']
        else:
            if 'date' not in event:
                timing = dt.date(crop_start_date.year, event['month'], event['day'])
                if timing < crop_start_date:
                    timing = timing.replace(year=timing.year + 1) # this deals with a crop calendar year starting in the fall and timing events in the following year
            else:
                timing = event['date']
        return timing
    
    @property
    def crop_type(self):
        """
        Define crop type (arable crop or grass) from name
        """
        return self._crop_type

    @crop_type.setter
    def crop_type(self, value):
        self._crop_type = value

    def _categorize_crop(self):
        """
        Assign crop type based on input: either crop, grass, or fallow
        """
        if 'grass' in self.crop.lower():
            return 'grass'
        else:
            return 'crop'
    

    def __str__(self):
        msg = "======================================================\n"
        msg += "               Crop characteristics\n"
        msg += "---------------------Description----------------------\n"
        msg += "Crop: " + self.crop + "\n"
        if self.variety is not None:
            msg += "Variety: " + self.variety + "\n"
        msg += "Crop type: " + self.crop_type + "\n"
        msg += "-------------------Agro-management--------------------\n"
        msg += self.agromanagement

        return msg
    

class CropRotation:
    """
    Class generating crop rotations combining agromanagement
    from a succession of crops and/or grasses
    """

    def __init__(self, *crops):
        self.rotation =  yaml.safe_load(self._generate_rotation(crops))
        self.crop_list = self._list_crops()
        self.yaml_rotation = self._generate_rotation(crops)

    def _generate_rotation(self, crops):
        rotation_yaml = ""
        for crop in crops:
            rotation_yaml += crop.agromanagement + "\n"
        return rotation_yaml
    

    def _list_crops(self):
        crops = self.find_value('crop_name')
        varieties = self.find_value('variety_name')
        return [{crop: variety} for crop, variety in zip(crops, varieties)]
    

    def find_value(self, key):
        """
        Find value associated to 'key', if existing
        """
        result = self._recursive_search(self.rotation, key)
        if result is None:
            print(f"Key '{key}' not found in the dictionary.")
        return result


    def _recursive_search(self, data, key):
        """
        Recursive search into yaml_dict to find specified key
        regardless of level of nesting into yaml_dict
        """
        results = []

        if isinstance(data, dict):
            for k, v in data.items():
                if k == key:
                    results.append(v)
                elif isinstance(v, (dict, list)):
                    results.extend(self._recursive_search(v, key))

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    results.extend(self._recursive_search(item, key))

        return results
    
    def __str__(self):
        msg = "======================================================\n"
        msg +=  "               Rotation characteristics\n"
        msg += "---------------------Description----------------------\n"
        crop_succession = ", ".join(", ".join(crop_dict.keys()) for crop_dict in self.crop_list)
        msg += "Crop succession: " + crop_succession + "\n"
        crop_varieties = ", ".join(", ".join(crop_dict.values()) for crop_dict in self.crop_list)
        msg += "Crop varieties: " + crop_varieties + "\n"
        msg += "======================================================\n\n"
        msg += self.yaml_rotation
        
        return msg