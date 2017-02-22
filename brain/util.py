#!/usr/bin/env python
# encoding: utf-8

import re

regex_ws = re.compile(r'\s+')
regex_be = re.compile(r'^\s+|\s+$')

def clean_text(t):
	text = regex_ws.sub(' ', t)
	text = regex_be.sub('', text)
	return text
