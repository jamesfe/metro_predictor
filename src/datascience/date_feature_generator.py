# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

import json
from datetime import datetime
from os.path import isdir, splitext, join
from os import listdir

from src.lib import timestamp_to_minutes_from_midnight


class DateFeatureGenerator(object):

    @classmethod
    def timestamp_to_minutes_from_midnight(unix_timestamp=0):
        unix_timestamp = int(unix_timestamp)
        datetime_object = datetime.utcfromtimestamp(unix_timestamp)
        return datetime_object.hour * 60 + datetime_object.minute

    def load_files(self):
        for file_name in listdir(self.in_dir):
            if splitext(file_name)[1].lower() != '.json' or file_name in self.loaded_files:
                continue
            with open(join(self.in_dir, file_name), 'r') as in_file:
                self.wx_data_by_day[splitext(file_name)[0]] = json.load(in_file)
                self.loaded_files.add(file_name)

    def __init__(self, in_dir=None):
        if in_dir is None or not isdir(in_dir):
            raise OSError
        else:
            self.in_dir = in_dir
        self.wx_data_by_day = {}
        self.loaded_files = set()

        self.load_files()

    def get_feature_data(self, date_desired):
        dict_key = "{0}_{1}_{2}".format(date_desired.year, date_desired.month, date_desired.day)
        if dict_key in self.wx_data_by_day:
            return self.wx_data_by_day[dict_key]

    @staticmethod
    def process_daily_data(data):
        rval = []
        daily_fields = ['sunriseTime', 'temperatureMaxTime', 'apparentTemperatureMinTime',
                        'apparentTemperatureMaxTime', 'sunsetTime', 'temperatureMinTime']
        for field in daily_fields:
            rval.append(timestamp_to_minutes_from_midnight(unix_timestamp=data[field]))

        desired_fields = ['windBearing', 'cloudCover', 'visibility', 'precipProbability',
                          'pressure', 'temperatureMin', 'apparentTemperatureMax',
                          'precipIntensity', 'temperatureMax', 'windSpeed', 'dewPoint',
                          'precipIntensityMax', 'humidity', 'moonPhase', 'apparentTemperatureMin']

        for field in desired_fields:
            try:
                rval.append(data[field])
            except KeyError:
                raise KeyError
                # We want to know about these errors because they're bad....later on we can replace
                # with -1 or something.

        return rval

    def date_to_feature_row(self, date_data):
        daily_array = []
        daily_data = self.get_feature_data(date_data)
        for station in daily_data:
            daily_array += self.process_daily_data(daily_data[station]['daily']['data'][0])
        return daily_array