#!/usr/bin/env python
# encoding: utf-8

import re
import datetime as dt

FROM_DT_FORMAT = '%Y-%m-%dT%H:%M:%S+0000'
TO_DT_FORMAT = '%Y-%m-%d %H:%M:%S'

regex_ws = re.compile(r'\s+')
regex_be = re.compile(r'^\s+|\s+$')

def clean_text(t):
	text = regex_ws.sub(' ', t)
	text = regex_be.sub('', text)
	return text

def to_datetime(date, format=FROM_DT_FORMAT):
    t = dt.datetime.strptime(date, FROM_DT_FORMAT)
    return t.strftime(TO_DT_FORMAT)
