from cropyields.db_manager import find_farm, get_farm_data

class Farm:
    """
    Base farm class that allows to define and manage farms (i.e., sets of fields under 
    same management). This class deals with the definition of farm rotations, 
    calculations of farm yields from the run of Wofost, definitions and changes in 
    agromanagement.

    :param identifier: either a parcel centroid in the OSGrid code form, or a farm 
           identifier (farm_id) in the RPA database or derived. If a centroid OSGrid code
           is passed, then the farm identifier of the parcel referring to that location 
           is retrieved
    ======================================================================================
    AAA: This class is for now only used as a container, which allows to retrieve and 
         store in an instance the characteristics of the farm. This allows to retrieve
         the listof parcels for a farm to run WOFOST.
         In the future, this will be set up to have a method that runs WOFOST within
         defining agromanagement and temporal scales of interest.
    """

    def __init__(self, identifier):
        self.farm_id = self._get_farm_id(identifier)
        self.farm_area, self.num_parcels, self.parcel_ids, self.parcel_data = self._get_farm_data(identifier)
        self.lon, self.lat = self._get_farm_location(identifier)

    
    @staticmethod
    def _get_farm_id(identifier):
        """
        Find ID of farm where 'identifier' is located
        """
        if not isinstance(identifier, int):
            farm = find_farm(identifier)['farm']
        else:
            farm = identifier
        return farm
    

    @staticmethod
    def _get_farm_data(identifier):
        """
        Find tot area in hectares, number of parcels and parcel IDs
        for an instance of the class Farm
        """
        farm = get_farm_data(identifier)
        farm = farm.set_crs('EPSG:4326')
        farm = farm.to_crs(27700)
        tot_area = farm.geometry.area.sum() / 1e4 #area in hectares
        tot_parcels = len(farm)
        parcel_ids = farm['nat_grid_ref']
        return tot_area, tot_parcels, parcel_ids, farm
    

    @staticmethod
    def _get_farm_location(identifier):
        farm = get_farm_data(identifier)
        farm = farm.set_crs('EPSG:4326')
        farm = farm.to_crs('EPSG:27700')
        farm['centroid'] = farm.centroid.to_crs('EPSG:4326')
        x = farm['centroid'].x.mean()
        y = farm['centroid'].y.mean()
        return(x, y)      

    
    def __str__(self):
        msg = "============================================\n"
        msg +=  "Farm characteristics for farm with ID %s \n" % str(self.farm_id)
        msg += "----------------Description-----------------\n"
        msg += "Lon: %.3f; Lat: %.3f\n" % (self.lon, self.lat)
        msg += "Total farm area: %.1f hectares \n" % self.farm_area 
        msg += "%d parcels \n" %self.num_parcels
        msg += "============================================\n\n"
        return msg
