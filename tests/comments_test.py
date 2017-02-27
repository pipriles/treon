#!/usr/bin/env python
# encoding: utf-8

import os
import sys

# Get into context
sys.path.insert(0, os.path.abspath('..'))

import log
from brain.facebook import comments
from brain.facebook import posts
from brain import config

logger = log.init_logger()

def main():

	name = input('Enter page name: ')
	path = config.POSTS_PATH + '%s_posts.csv' % name
	
	if not os.path.exists(path):
		posts.scrape_posts(name)

	comments.scrape_comments(name)
	
if __name__ == '__main__':
	main()