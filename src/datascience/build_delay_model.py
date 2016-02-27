# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

"""
Functions to squeeze the data into an array
Functions to aggregate delay data into daily totals
"""

from datetime import datetime, timedelta
import json


def build_delay_table(in_file_name):
    with open(in_file_name, 'r') as in_file:
        delay_data = json.load(in_file)

    min_date = datetime(year=2100, month=1, day=1)
    max_date = datetime(year=2000, month=1, day=1)
    for item in delay_data:
        event_dtg = datetime.strptime(item['event_dtg'], '%Y-%m-%dT%H:%M:%S')
        if event_dtg < min_date:
            min_date = event_dtg
        if event_dtg > max_date:
            max_date = event_dtg

    base_date = datetime(year=min_date.year, month=min_date.month, day=min_date.day)
    delays_by_date = [{'date': base_date + timedelta(days=offset),
                       'delays': 0,
                       'num_delays': 0}
                      for offset in
                      range((max_date - min_date).days + 1)]

    for item in delay_data:
        if item['delay'] is not None:
            event_dtg = datetime.strptime(item['event_dtg'], '%Y-%m-%dT%H:%M:%S')
            day_offset = (event_dtg - base_date).days
            delays_by_date[day_offset]['delays'] += item['delay']['minutes']
            delays_by_date[day_offset]['num_delays'] += 1

    return delays_by_date


def get_delay_average(datetime_date, delay_table):
    for event_instance in delay_table:
        if event_instance['date'] == datetime_date:
            if event_instance['num_delays'] == 0:
                return 0
            else:
                return event_instance['delays'] / event_instance['num_delays']


def scale_average_delay(num_minutes, binval):
    return int(num_minutes / binval)


def get_delay_total(datetime_date, delay_table):
    for item in delay_table:
        if item['date'] == datetime_date:
            return item['delays']


def day_of_week_array(target_date):
    arr = [0] * 7
    arr[target_date.weekday()] = 1
    return arr


def julian_date_as_array(target_date):
    return [target_date.timetuple().tm_yday]


def append_ancillary_data(tgt_date, feature_row=list()):
    feature_row.extend(day_of_week_array(tgt_date))
    feature_row.extend(julian_date_as_array(tgt_date))
    return feature_row
