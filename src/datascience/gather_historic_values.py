# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

import json
from os.path import isfile, join
from datetime import datetime, timedelta

import requests

APP_DIR = '/home/ubuntu/Code/metro_failcast'

METRO_DATA_FILE = join(APP_DIR, './data_files/interim_station_list.json')
BASE_STATION_LIST = join(APP_DIR, './data_files/base_wx_stations.txt')
FORECAST_API_KEY = open(join(APP_DIR, './secrets/forecast_io_secret'), 'r').read().strip()
# FORECAST_API_KEY = os.environ['FORECAST_IO_SECRET']
OUT_WX_DATA_DIR = join(APP_DIR, "./data_files/forecasts/")


def gather_metro_station_coord_data(tgt_url):
    """
    Visit the WMATA API and grab a list of URLs
    """
    # TODO: Write this function.  Blah.
    pass


def gather_metro_stations_from_tempfile(tgt_file=METRO_DATA_FILE):
    with open(tgt_file, 'r') as in_file:
        json_interpretation = json.load(in_file)
    return json_interpretation


def gather_metro_station_coords(json_data, needed_stations):
    station_geolist = {}
    for item in json_data['Stations']:
        station_geolist[item['Name']] = {'lat': item['Lat'],
                                         'lon': item['Lon'],
                                         'name': item['Name']}

    ret_stations = []
    for station in needed_stations:
        ret_stations.append(station_geolist[station])
    return ret_stations


def gather_forecast_io_past_data(metro_stn_geolist, tgt_day, out_dir=OUT_WX_DATA_DIR):
    outfile_name = '{0}_{1}_{2}.json'.format(tgt_day.year, tgt_day.month, tgt_day.day)
    if isfile(join(out_dir, outfile_name)):
        return True

    ret_vals = {}
    gather_time = tgt_day.isoformat()

    for station in metro_stn_geolist:
        weather_data = gather_forecast_io_historic_datapoint(str(station['lat']),
                                                             str(station['lon']),
                                                             gather_time)
        ret_vals[station['name']] = weather_data
    with open(join(out_dir, outfile_name), 'w') as out_json:
        json.dump(ret_vals, out_json)

    return True


def gather_forecast_io_historic_datapoint(lat, lon, tgt_time):
    # https://api.forecast.io/forecast/APIKEY/LATITUDE,LONGITUDE,TIME
    tgt_url = 'https://api.forecast.io/forecast/' + FORECAST_API_KEY + '/' + lat + ',' + lon + ',' + tgt_time
    payload = {'exclude': 'currently,minutely,hourly,alerts,flags'}
    result = requests.get(tgt_url, params=payload)
    if result.status_code == 200:
        return result.json()


def scrape_data_from_date(start_date):
    assert isinstance(start_date, datetime) is True

    metro_station_json = gather_metro_stations_from_tempfile()
    with open(BASE_STATION_LIST, 'r') as station_wx_file:
        station_list = json.load(station_wx_file)

    metro_stations_geolist = gather_metro_station_coords(metro_station_json, station_list)

    for days in range((datetime.now - start_date).days):
        tgt_day = start_date + timedelta(days=days)
        gather_forecast_io_past_data(metro_stations_geolist, tgt_day)
