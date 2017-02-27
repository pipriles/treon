#!/usr/bin/env python
# encoding: utf-8

import os
import sys

# Get into context
sys.path.insert(0, os.path.abspath('..'))

import log
from brain.twitter import tweets

logger = log.init_logger()

def main():
	name = input('Enter page name: ')
	tweets.scrape_tweets(name)

if __name__ == '__main__':
	main()