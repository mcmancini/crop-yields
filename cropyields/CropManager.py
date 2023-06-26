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
    specific farm management practices
    """

    DEFAULT_ARGS = {
        'TimedEvents': 'Null'
    }

    
    def __init__(self, crop, variety, calendar_year, **kwargs):
        self.crop = crop
        self.variety = variety
        self.calendar_year = calendar_year
        self.agromanagement = self._generate_agromanagement(**kwargs)
    

    def _generate_agromanagement(self, **kwargs):
        args = self.DEFAULT_ARGS.copy()
        args.update(kwargs)

        # Start of the crop calendar
        if 'start_crop_calendar'not in args or args['start_crop_calendar'] is None:
            if 'winter' in self.variety.lower():
                args['start_crop_calendar'] = dt.date(self.calendar_year, 9, 1)
            else:
                args['start_crop_calendar'] = dt.date(self.calendar_year, 3, 1)
        
        # End of the crop calendar
        if 'end_crop_calendar'not in kwargs or kwargs['end_crop_calendar'] is None:
            if 'winter' in self.variety.lower():
                args['end_crop_calendar'] = dt.date(self.calendar_year + 1, 9, 1)
            else:
                args['end_crop_calendar'] = dt.date(self.calendar_year, 11, 1)

        # Crop sowing date
        if 'crop_start_date' not in args or args['crop_start_date'] is None:
            if 'winter' in self.variety.lower():
                args['crop_start_date'] = dt.date(self.calendar_year, 11, 5)
            else:
                args['crop_start_date'] = dt.date(self.calendar_year, 4, 1)

        # Fertilisation or irrigation
        if 'apply_npk' in args and args['apply_npk'] is not None:
            events_table_lines = []
            for event in args['apply_npk']:
                timing = self._check_timing_event(args['start_crop_calendar'], event['date'], args['end_crop_calendar'])
                line = f"- {timing.year}-{timing.month:02d}-{timing.day:02d}: {{N_amount: {event['N_amount']}, P_amount: {event['P_amount']}, K_amount: {event['K_amount']}}}"
                events_table_lines.append(line)
            
            events_table = '\n                '.join(events_table_lines)

            timed_events_yaml = f"""
            TimedEvents:
            -   event_signal: apply_npk
                name:  Timed N/P/K application table
                comment: All fertilizer amounts in kg/ha
                events_table:
                {events_table}
            """
        else:
            timed_events_yaml = f"TimedEvents: {self.DEFAULT_ARGS['TimedEvents']}"

        # Combine all in agromanagement
        _agromanagement_yaml = f"""
        - {args['start_crop_calendar']}:
            CropCalendar:
                crop_name: {self.crop}
                variety_name: {self.variety}
                crop_start_date: {args['crop_start_date']}
                crop_start_type: sowing
                crop_end_date:
                crop_end_type: maturity
                max_duration: 365
            {timed_events_yaml}
            StateEvents: Null
        - {args['end_crop_calendar']}:
            CropCalendar: null
            TimedEvents: null
            StateEvents: null
        """

        # remove empty lines
        _agromanagement_yaml = '\n'.join([line for line in _agromanagement_yaml.split('\n') if line.strip()])
        return _agromanagement_yaml

    @staticmethod
    def _check_timing_event(crop_sowing_date, event_timing, end_crop_calendar):
        if event_timing < crop_sowing_date or event_timing > end_crop_calendar:
            raise ValueError(f"The event timing date \'{event_timing}\' falls outside the crop calendar [{crop_sowing_date}, {end_crop_calendar}]")
        else:
            return event_timing
        

class CropRotation:
    """
    Class representing a crop rotation consisting of multiple crops
    """

    def __init__(self, *crops):
        self.crops = crops
        self.rotation = self._generate_rotation()


    def _generate_rotation(self):
        rotation_yaml = ""
        for crop in self.crops:
            rotation_yaml += crop.agromanagement + "\n"
        
        return rotation_yaml