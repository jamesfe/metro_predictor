# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

from datetime import date, datetime, timedelta
import json
import pickle

import logging
import sys
from os import mkdir
from os.path import isdir, isfile, join
from json import load as json_load

from src.datascience.date_feature_generator import DateFeatureGenerator
from src.datascience.gather_historic_values import gather_metro_stations_from_tempfile, \
    gather_metro_station_coords, gather_forecast_io_past_data
from src.datascience.build_delay_model import append_ancillary_data

APP_DIR = '/home/ubuntu/Code/metro_failcast'
TEMP_METRO_STATION_FILE = join(APP_DIR, './src/datascience/data_files/interim_station_list.json')
BASE_STATION_LIST = join(APP_DIR, './src/datascience/data_files/base_wx_stations.txt')

PREDICTION_DIR = join(APP_DIR, './predictions/')
WEATHER_DIR = join(APP_DIR, './src/datascience/data_files/forecasts')
MODEL_FILE = join(APP_DIR, './prediction_models/clf_22feb2016_single_line.pickle')


def load_prediction(file_name):
    with open(file_name, 'r') as in_prediction_file:
        json_data = json.load(in_prediction_file)
    return json_data


def gather_weather_data():
    metro_station_json = gather_metro_stations_from_tempfile(TEMP_METRO_STATION_FILE)
    with open(BASE_STATION_LIST, 'r') as station_wx_file:
        station_list = json_load(station_wx_file)

    metro_stations_geolist = gather_metro_station_coords(
        metro_station_json, station_list)
    today = date.today()
    tgt_day = datetime(year=today.year, month=today.month, day=today.day)
    success = gather_forecast_io_past_data(metro_stations_geolist,
                                           tgt_day,
                                           out_dir=WEATHER_DIR)
    return success


def build_prediction():
    # TODO: Make this a library function so it matches feature gen in build_model.
    if gather_weather_data():
        today = date.today()
        tgt_day = datetime(year=today.year, month=today.month, day=today.day)

        wx_data = DateFeatureGenerator(WEATHER_DIR)
        new_feature = wx_data.date_to_feature_row(tgt_day)
        prev_2day_feature = wx_data.date_to_feature_row(tgt_day - timedelta(days=2))
        prev_day_feature = wx_data.date_to_feature_row(tgt_day - timedelta(days=1))
        new_feature = append_ancillary_data(tgt_day, new_feature)
        new_feature += prev_day_feature
        new_feature += prev_2day_feature

        with open(MODEL_FILE, 'rb') as clf_file:
            clf = pickle.load(clf_file)
            predicted = clf.predict_proba(new_feature)
    else:
        raise RuntimeError
    return predicted[0].tolist()


def return_prediction():
    today = date.today()
    fname = "{0}_{1}_{2}.json".format(today.year, today.month, today.day)
    if isfile(join(PREDICTION_DIR, fname)):
        return load_prediction(join(PREDICTION_DIR, fname))
    else:
        prediction = build_prediction()
        with open(join(PREDICTION_DIR, fname), 'w') as pred_file:
            json.dump(prediction, pred_file)
        return prediction


def format_prediction(in_prediction, minutes=5):
    """
    :param in_prediction: np array summing to one
    :param minutes: number of minutes in each class
    :return:
    """
    ret_predictions = []
    for index, prediction in enumerate(in_prediction):
        minute_delay_label = "{0} to {1} min".format(index * minutes, (index + 1) * minutes)
        ret_dict = dict()
        ret_dict['prediction'] = str(round(prediction * 100, 2)) + '%'
        ret_dict['label'] = minute_delay_label
        ret_dict['value'] = round(prediction, 4)
        ret_predictions.append(ret_dict)
    return ret_predictions


def provide_weather():
    if gather_weather_data():
        tgt_day = date.today()
        wx_filename = '{0}_{1}_{2}.json'.format(tgt_day.year, tgt_day.month, tgt_day.day)
        with open(join(WEATHER_DIR, wx_filename), 'r') as wfile:
            weather_json = json.load(wfile)
        try:
            return weather_json['Metro Center']
        except KeyError:
            return None
    else:
        return None


def present_prediction():
    try:
        predicted_value = return_prediction()
    except RuntimeError:
        values = [{'prediction': 'Null', 'label': 'There was an error'}]
    else:
        values = format_prediction(predicted_value)

    weather = provide_weather()
    prediction_json = []
    for item in values:
        prediction_json.append({'label': item['label'], 'probability': item['value']})

    ordered_vals = sorted(values, key=lambda k: k['value'], reverse=True)

    return render_template('index_full_pics.html',
                           values=values,
                           weather=weather,
                           prediction_json=json.dumps(prediction_json),
                           ordered_predictions=ordered_vals)


def make_preset_dirs():
    if not isdir(PREDICTION_DIR):
        mkdir(PREDICTION_DIR)
    if not isdir(WEATHER_DIR):
        mkdir(WEATHER_DIR)


if __name__ == "__main__":
    make_preset_dirs()
