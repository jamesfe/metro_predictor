# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

"""
Functions to squeeze the data into an array
Functions to aggregate delay data into daily totals
"""

from datetime import datetime, timedelta
from pickle import dump

from sklearn.preprocessing import StandardScaler
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn import grid_search

import numpy as np

from src.datascience.date_feature_generator import DateFeatureGenerator
from src.datascience.build_delay_model import build_delay_table, append_ancillary_data, \
    scale_average_delay, get_delay_average


if __name__ == '__main__':
    delays = build_delay_table('./src/datascience/data_files/json_export_cao_02AUG2015.json')
    wx_data = DateFeatureGenerator('./src/datascience/data_files/forecasts')

    min_date = datetime(year=2013, month=1, day=3)
    max_date = datetime(year=2015, month=1, day=1)
    curr_date = min_date

    features = []
    result = []

    """
    TODO:
    Some discussion here about how we do this.
    We have data, by line, for delays.  For each day, we add five features and predict five things, like so:
    [x,y,z,a,redline=1,blueline=0,=0,=0,...]
    [x,y,z,a,redline=0,blueline=1,=0,=0,...]
    So we need to throw an extra argument into date_to_feature_row & grab the appropriate color
    fro the delay table.

    Maybe a new function, generate_color_based_feature_pair(feature, result)??
    """

    while curr_date < max_date:
        curr_date += timedelta(days=1)
        new_feature = wx_data.date_to_feature_row(curr_date)
        prev_2day_feature = wx_data.date_to_feature_row(curr_date - timedelta(days=2))
        prev_day_feature = wx_data.date_to_feature_row(curr_date - timedelta(days=1))
        new_feature = append_ancillary_data(curr_date, new_feature)
        new_feature += prev_day_feature
        new_feature += prev_2day_feature
        features.append(new_feature)
        result.append(scale_average_delay(get_delay_average(curr_date, delays), 5))
    scaled_features = StandardScaler().fit_transform(features)

    print("Feature vector length: ", len(scaled_features[0]))
    print("Feature space size: ", len(scaled_features))

    X_train, X_test, y_train, y_test = train_test_split(scaled_features, result, test_size=0.4)

    def do_grid_search(scaled_features, result):
        param_grid = {
            'max_features': [None, 'auto'],
            'max_depth': [1] + list(range(2, 26, 5)),
            'min_samples_leaf': [1] + list(range(3, 22, 5)),
            'min_samples_split': [1] + list(range(3, 24, 5)),
        }

        clf = RandomForestClassifier()
        gs_cv = grid_search.GridSearchCV(clf, param_grid, n_jobs=4).fit(scaled_features, result)
        print("First run, best parameters: ", gs_cv.best_params_)
        print('First run, best score: ', gs_cv.best_score_)

        first_run_params = gs_cv.best_params_

        # Use the pre-existing best case stuff for the n_estimators search
        clf = RandomForestClassifier(**first_run_params)
        param_grid = {
            'n_estimators': list(range(1, 100, 10) + list(range(150, 2000, 500)))
        }
        gs_cv = grid_search.GridSearchCV(clf, param_grid, n_jobs=4).fit(scaled_features, result)
        print('Final run, best parameters: ', gs_cv.best_params_)
        print('Final run, best score: ', gs_cv.best_score_)
        first_run_params.update(gs_cv.best_params_)
        return first_run_params

    best_params = do_grid_search(scaled_features, result)

    clf = RandomForestClassifier(**best_params)
    avg_deltas = np.array([])
    clf.fit(X_train, y_train)
    with open('clf_22feb2016_single_line.pickle', 'wb') as out_pickle:
        dump(clf, out_pickle, protocol=2)
    score = clf.score(X_test, y_test)
    print("Score: ", score)
