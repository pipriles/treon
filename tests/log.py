#!/usr/bin/env python
#encoding: utf-8

import logging

def init_logger(module='brain'):

	logger = logging.getLogger('brain')

	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)

	frmt = logging.Formatter('[%(module)10s] : %(message)s')
	handler.setFormatter(frmt)

	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

	return logger

def main():
	init_logger()

if __name__ == '__main__':
	main()