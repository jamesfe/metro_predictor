# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals, print_function, division)

from datetime import datetime


def timestamp_to_minutes_from_midnight(unix_timestamp=0):
    unix_timestamp = int(unix_timestamp)
    datetime_object = datetime.utcfromtimestamp(unix_timestamp)
    return datetime_object.hour * 60 + datetime_object.minute
