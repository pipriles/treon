#!/usr/bin/env python
# encoding: utf-8

import requests as rq
import csv
import re
import os

from selenium import webdriver
from bs4 import BeautifulSoup

from multiprocessing.dummy import Pool

from bs4 import BeautifulSoup
from datetime import datetime as dt

BASE_URL = 'https://twitter.com/search?q=from:{}'

JSON_URL  = "https://twitter.com/i/search/timeline?"
JSON_URL += "vertical=default&"
JSON_URL += "q=from:{}&"
JSON_URL += "src=typd&"
JSON_URL += "include_available_features=1&"
JSON_URL += "include_entities=1&"
JSON_URL += "lang=en&"
JSON_URL += "max_position={}&"
JSON_URL += "reset_error_state=false"

# Hardcoded for now....
USERS = ['kindafunnyvids', 'amandapalmer', 'cgpgrey', 'Kurz_Gesagt', 
	'EasyAllies', 'FenoxoFenfen', 'TheComedyButton', 'swordandscale', 
	'JimSterling', 'RollPlay', 'PTXofficial', 'CANADALAND', 
	'tarababcock', 'marble_syrup']

MAX_THREADS = 10
FILE_PATH = 'csv/{}_tweets.csv'

def open_browser_with(user):

	url = BASE_URL.format(user)

	# Open browser to just get the html
	browser = webdriver.Chrome()
	browser.get(url)
	html = browser.page_source	
	browser.close()

	return html

def first_request(user):

	html = open_browser_with(user)

	# Parse to extract the min position
	tweets = parse_tweets(html)

	soup = BeautifulSoup(html, 'html.parser')
	timeline = soup.select('div#timeline .stream-container')[0]

	return (tweets, timeline['data-min-position'])

def do_request(user, max_position):

	url = JSON_URL.format(user, max_position)
	print("Fetching {} ...".format(url))

	resp = rq.get(url)
	data = resp.json()

	return data

def fetch_tweets(user, max_=1000):
	
	cont = 0
	max_position = ''
	data = {}

	def write_tweets(tweets):
		for t in tweets:
			wt.writerow(t.values())

	tweets, max_position = first_request(user)

	# Open file
	path = FILE_PATH.format(user)
	file = open(path, 'w', encoding='utf-8')
	wt = csv.writer(file)

	wt.writerow(tweets[0].keys())
	write_tweets(tweets)

	cont += len(tweets)

	while max_position is not None and cont < max_:

		try:
			data = do_request(user, max_position)
		except Exception as e:
			print(resp, resp.reason)
			print(e)
			break

		max_position = data['min_position']
		html = data['items_html']
		tweets = parse_tweets(html)

		# Store tweets
		write_tweets(tweets)

		cont += len(tweets)

		print('Fetched {} results'.format(cont))
		print('--------------------------')

	file.close()

def parse_tweets(html):

	soup = BeautifulSoup(html, 'html.parser')
	tweets = soup.select('.original-tweet')
	
	return [scrape_tweet(t) for t in tweets]

def scrape_tweet(tweet):
	
	data = {}

	def cont_attr(attr):
		item_class = 'ProfileTweet-action--{}'.format(attr)
		info = tweet.find('span', class_=item_class)
		return info.span['data-tweet-stat-count']

	def to_datetime(stamp):
		return dt.utcfromtimestamp(int(stamp))

	user_e = tweet.find('span', class_='username')
	tweet_e = tweet.find('div', class_='js-tweet-text-container')
	date_e = tweet.find('span', class_='_timestamp')

	data['user'] = user_e.b.text
	data['text'] = re.sub(r'\n', '', tweet_e.text)
	data['date'] = to_datetime(date_e['data-time'])
	data['reply'] = cont_attr('reply')
	data['retweet'] = cont_attr('retweet')
	data['favorite'] = cont_attr('favorite')

	return data

def main():

	try:
		os.mkdir('csv')
	except FileExistsError:
		pass

	# Parallel scrape users
	fetch_tweets('kindafunnyvids')


if __name__ == '__main__':
	main()