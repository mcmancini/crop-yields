# -*- coding: utf-8 -*-
# Copyright (c) 2023 LEEP, University of Exeter (UK)
# Mattia Mancini (m.c.mancini@exeter.ac.uk), June 2023
# ====================================================
"""
FARM MANAGER
"""
import datetime as dt
import geopandas as gpd
import numpy as np
import pandas as pd
from pcse.base import ParameterProvider
from pcse.models import Wofost72_WLP_FD
from cropyields import config
from cropyields.SoilManager import SoilGridsDataProvider, WHSDDataProvider
from cropyields.WeatherManager import NetCDFWeatherDataProvider
from cropyields.db_manager import find_farm, get_farm_data


class Farm:
    """
    Base farm class that allows to define and manage farms (i.e., sets of fields under
    same landholder). This class deals with the definition of farm rotations,
    calculations of farm yields from the run of Wofost, definitions and changes in
    agromanagement.

    :param identifier: either a parcel centroid in the OSGrid code form, or a farm
           identifier (farm_id) in the RPA database or derived. If a centroid OSGrid code
           is passed, then the farm identifier of the parcel referring to that location
           is retrieved
    """

    # Class defaults for Wofost runs
    rcp = config.rcp
    ensemble = config.ensemble
    soilsource = config.soilsource
    cropd = config.cropd
    sitedata = config.sitedata
    output_dir = config.output_dir

    def __init__(self, identifier):
        self.farm_id = self._get_farm_id(identifier)
        (
            self.farm_area,
            self.num_parcels,
            self.parcel_ids,
            self.parcel_data,
            self.lon,
            self.lat,
        ) = self._get_farm_data(identifier)
        self.yields = []

    def run_rotation(self, **kwargs):
        """
        Run Wofost on an instance of the class 'Farm'.
        :param **kwargs: a dictionary that contains parcel-rotation
               key-value pairs. Rotations are instances of the CropRotation
               class, which takes consecutive instances of the Crop class.
               e.g.:
               {'SX123456': rotation_1, 'SW123123': rotation_2, ...}

               potatoes = Crop('potato', 'Potato_701', 2023, **potato_args)
               wheat = Crop('wheat', 'Winter_wheat_06', 2023, **wheat_args)
               maize = Crop('maize', 'maize_01', 2025, **maize_args)
               rotation_1 = CropRotation(potatoes, wheat, maize)
               rotation_2 = CropRotation(x, y, x)
               print(rotation_1.rotation)
        """
        rcp = kwargs.get("rcp") or Farm.rcp
        ensemble = kwargs.get("ensemble") or Farm.ensemble
        soilsource = kwargs.get("soilsource") or Farm.soilsource
        cropd = kwargs.get("cropd") or Farm.cropd
        sitedata = kwargs.get("sitedata") or Farm.sitedata

        # years = self._check_input_year(years)
        result_dict = {}

        for x, row in self.parcel_data.iterrows():
            parcel_id = row["nat_grid_ref"]
            geometry = row["geometry"]
            area = self.parcel_data.iloc[[x]].to_crs(27700).area[x] / 10000
            result_dict[parcel_id] = {"geometry": geometry, "area": area, "crop": {}}

        farmed_parcels = kwargs.keys()
        for parcel_id in self.parcel_ids:
            if parcel_id in farmed_parcels:
                if soilsource == "SoilGrids":
                    soildata = SoilGridsDataProvider(parcel_id)
                else:
                    soildata = WHSDDataProvider(parcel_id)
                try:
                    wdp = NetCDFWeatherDataProvider(
                        parcel_id, rcp, ensemble, force_update=False
                    )
                except Exception as e:
                    print(
                        f"Failed to retrieve weather data for parcel at '{parcel_id}'"
                        f" due to {e}"
                    )

                # agromanagement
                rotation = kwargs[parcel_id]
                agromanagement = rotation.rotation
                crop_list = rotation.find_value("crop_name")
                crop_name = next(iter(rotation.crop_list[0]))
                crop_variety = rotation.crop_list[0][crop_name]
                crop_start_date = rotation.find_value("crop_start_date")
                cropd.set_active_crop(crop_name, crop_variety)
                parameters = ParameterProvider(
                    cropdata=cropd, soildata=soildata, sitedata=sitedata
                )
                wofsim = Wofost72_WLP_FD(parameters, wdp, agromanagement)
                try:
                    wofsim.run_till_terminate()
                except Exception as e:
                    print(
                        f"failed to run the WOFOST crop yield model for parcel '{parcel_id}'"
                        f" due to {e}"
                    )
                output = wofsim.get_output()

                df = pd.DataFrame(output)
                df.set_index("day", inplace=True, drop=True)

                range_lst = crop_start_date + [df.index.max()]

                for i in range(len(range_lst) - 1):
                    crop = crop_list[i]
                    start_date = range_lst[i]
                    end_date = range_lst[i + 1] - dt.timedelta(days=1)
                    crop_df = df[start_date:end_date]
                    if not np.isnan(crop_df["TWSO"]).all():
                        result_dict[parcel_id]["crop"][crop] = {
                            "yield_ha": round(crop_df["TWSO"].max() / 1e3, 3) * 1.14,
                            "yield_parcel": round(
                                (crop_df["TWSO"].max() / 1e3)
                                * 1.14
                                * result_dict[parcel_id]["area"],
                                3,
                            ),
                            "harvest_date": crop_df["TWSO"]
                            .idxmax()
                            .strftime("%Y-%m-%d"),
                        }
                    else:
                        result_dict[parcel_id]["crop"][crop] = {
                            "yield_ha": 0,
                            "yield_parcel": 0,
                            "harvest_date": "N/A",
                        }
        self.yields.append(result_dict)

    @staticmethod
    def _check_html_extension(filename):
        if not filename.endswith(".html"):
            raise ValueError(
                "Invalid file extension. File must have an '.html' extension."
            )
        return filename

    @staticmethod
    def _check_tiff_extension(filename):
        if not filename.endswith(".tiff"):
            raise ValueError(
                "Invalid file extension. File must have a '.tiff' extension."
            )
        else:
            return filename

    @staticmethod
    def _check_input_year(years):
        if not isinstance(years, list):
            years = [years]
        return years

    @staticmethod
    def _get_yield_data(yield_dict, year, col):
        selected_data = [
            (key, value["geometry"], value[col][year])
            for key, value in yield_dict.items()
        ]
        df = pd.DataFrame(selected_data, columns=["parcel", "geometry", col])
        gdf = gpd.GeoDataFrame(df, geometry="geometry")
        return gdf

    @staticmethod
    def _get_farm_id(identifier):
        """
        Find ID of farm where 'identifier' is located
        """
        if not isinstance(identifier, int):
            farm = find_farm(identifier)["farm"]
        else:
            farm = identifier
        return farm

    @staticmethod
    def _get_farm_data(identifier):
        """
        Find tot area in hectares, number of parcels parcel IDs
        and long and lat of the centre for an instance of the
        class Farm
        """
        farm = get_farm_data(identifier)
        farm = farm.set_crs("EPSG:4326")
        farm_repr = farm.to_crs(27700)
        tot_area = farm_repr.geometry.area.sum() / 1e4  # area in hectares
        tot_parcels = len(farm_repr)
        parcel_ids = farm_repr["nat_grid_ref"]
        centroids = farm_repr.centroid.to_crs("EPSG:4326")
        x = centroids.x.mean()
        y = centroids.y.mean()
        return tot_area, tot_parcels, parcel_ids, farm, x, y

    def __str__(self):
        msg = "============================================\n"
        msg += "Farm characteristics for farm with ID %s \n" % str(self.farm_id)
        msg += "----------------Description-----------------\n"
        msg += "Lat: %.3f; Lon: %.3f\n" % (self.lat, self.lon)
        msg += "Total farm area: %.1f hectares \n" % self.farm_area
        msg += "%d parcels \n" % self.num_parcels
        msg += "============================================\n\n"
        return msg
