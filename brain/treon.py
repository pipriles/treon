#!/usr/bin/env python
# encoding: utf-8

import requests as rq
import csv
import re
import pickle
import os
import logging

from bs4 import BeautifulSoup

from multiprocessing.dummy import Pool
from threading import Thread
from queue import Queue

from . import config

SITE_URL = 'https://graphtreon.com'
FILE_PATH = config.CREATORS_FILE

MAX_THREADS = 6

logger = logging.getLogger(__name__)

regex = {
	'trim': re.compile(r'\s'),
	'clrc': re.compile(r'\W'),
	'fdat': re.compile(r'series: \[(\{[^\{\}]+\})\]'),
	'name': re.compile(r'name: \'([^\']+)\''),
	'data': re.compile(r'data: \[(\[.+\])\]'),
	'stat': re.compile(r'^\s+|\s+$')
}

# This return a list of creators
def fetch_creators():
	# Nice message
	logger.debug("Fetching creators...")

	# If csv file exists don't do the request!
	data = check_creators()
	if not data:
		request = rq.get(SITE_URL + '/api/creators')
		data = request.json()['data']
		store_creators(data)

	return [extract_name(x) for x in data]

def check_creators(path=FILE_PATH):

	creators = []
	try:
		f = open(path, 'r') 
		reader = csv.DictReader(f)
		creators = [x for x in reader]
		f.close()
	except IOError:
		pass

	return creators

# Store the creators as a csv file
# I'll add a decorator to make it more pretty
# @store(FILE_PATH)
def store_creators(data, path=FILE_PATH):
	# This will never happen
	if not data: return

	with open(path, 'w') as f:	
		poe = csv.writer(f)
		poe.writerow(data[0].keys()) # Column names

		for item in data:
			poe.writerow(item.values())

def fetch_creator(creator):
	request = rq.get("{}/creator/{}".format(SITE_URL, creator))
	return request.text

def parse_scripts(soup):
	scripts = soup.find_all('script')

	# We can call find data from here
	for s in scripts:
		yield ' '.join(regex['trim'].sub(' ', s.text).split())

def find_data(script):
	stats = {}
	for span in regex['fdat'].finditer(script):
		content = span.group(1)
		parse_content(stats, content)

	return stats

def parse_content(stats, content):
	name = regex['name'].search(content).group(1)
	data = regex['data'].search(content).group(1)
	clean_data = regex['clrc'].sub(' ', data)
	final_value = clean_data.split()[-1]	# The last record

	key = {
		'Facebook Likes': 		'facebook_count',
		'Twitter Followers': 	'twitter_count',
		'Youtube Subscribers': 	'youtube_count'
	}.get(name, None)

	stats[key] = final_value

def parse_account(info, name, val, url):

	key = {
		'Patrons': 				'patrons',
		'Earnings per thing':	'earningsPerThing',
		'Earnings per Video':	'earningsPerVideo',
		'Earnings per month':	'earningsPerMonth',
		'Avg Patron per thing': 'avgPatronPerThing',
		'Avg Patron per Video': 'avgPatronPerVideo',
		'Avg Patron per month': 'avgPatronPerMonth',
		'Likes':				'facebook',
		'Followers':			'twitter',
		'Subscribers':			'youtube'
	}.get(name, None)

	if key in ('patrons', 'facebook', 'twitter', 'youtube'):
		info['%s_count' % key] = re.sub(r'[^\d\.KM]', r'', val, flags=re.I)
		info['%s_url'  % key] = url
	elif key is not None:
		info[key] = re.sub(r'[^\d\.]', r'', val)

def find_accounts(soup):
	
	info = {}
	header = soup.select('.headerstats-header')
	stat = soup.select('.headerstats-stat')
	
	for h, s in zip(header, stat):
		ext_url = h.a.get('href') if h.a else None
		title = regex['stat'].sub('', h.get_text())
		value = regex['stat'].sub('', s.get_text())
		
		parse_account(info, title, value, ext_url) # Super tuple

	return info

def update_stats(stats, conts):
	for key in stats:
		try:
			# If consts doesn't have the key pass
			stats[key] = conts[key]
		except KeyError:
			pass

def extract_name(artist):
	return artist['link'].split('_&_')[0]

def _scrape_artist(name):

	html = fetch_creator(name)
	soup = BeautifulSoup(html, 'html.parser')

	# Search for accounts
	stats = find_accounts(soup)

	# Scrape data from the script
	for script in parse_scripts(soup):
		conts = find_data(script)
		update_stats(stats, conts)

	return stats

class ArtistScraper():

	def __init__(self):

		self.file = None
		self._header = config.CREATORS_HEADER
		self._path	 = config.SCRAPED_FILE

		if os.path.exists(self._path):
			self._mode = 'a'
		else:
			self._mode = 'w'

	def open(self):
		self.file = open(self._path, self._mode)
		self.w = csv.writer(self.file)
		self.w.writerow(self._header)

	def close(self):
		self.file.close()

	def start(self, user):
		data = _scrape_artist(user)
		stat = [data.get(x, '') for x in self._header]
		self.w.writerow(stat)

		return data

def start_scrape_pool(data):

	# Scrape each creator step
	# I will do this in parallel

	header = config.CREATORS_HEADER
	path = config.SCRAPED_FILE

	mode = 'a' if os.path.exists(path) else 'w'
	f = open(path, mode)
	w = csv.writer(f)

	def scrape_helper(artist):

		stats = _scrape_artist(artist)

		w.writerow([stats.get(x, '') for x in header])	
		rem.remove(artist)
		
		logger.info("({:5}) Fetched {}...".format(len(rem), artist))
		return True

	# Write header in csv file
	w.writerow(header)

	# Restore state
	users = restore_state(users)
	rem = list(users)
	end = False

	p = Pool(MAX_THREADS) 
	it = p.imap(scrape_helper, users)

	try:
		while not end:
			if not next(it, False):
				end = True
	except BaseException as e:
		save_state(rem)
		raise e
	finally:
		logger.debug('Closing pool')
		p.terminate()
		p.join()
		f.close()

	# Secuencial aproach:
	# for artist in data:
	# 	_scrape_artist(artist)

def restore_state(default):
	try:
		f = open('dat.pickle', 'rb')
		dat = pickle.load(f)
		f.close()
		logger.debug('Restored state!')
	except (IOError, EOFError):
		dat = default

	return dat

def save_state(data):
	logger.debug('Saving state...')
	with open('dat.pickle', 'wb') as f:
		pickle.dump(data, f)

def main():
	try:
		data = fetch_creators()		# Fetch creators step
		start_scrape_pool(data)		# Scrape each creator step
	except KeyboardInterrupt:
		logger.debug('\nBye...')
		pass

if __name__ == '__main__':
	main()
