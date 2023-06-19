from pcse.fileinput import YAMLAgroManagementReader
import datetime as dt

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

        
