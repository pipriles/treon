#!/usr/bin/env python
# encoding: utf-8

import requests as rq
import csv
import re
import os

from multiprocessing.dummy import Pool

from bs4 import BeautifulSoup
from datetime import datetime as dt

BASE_URL  = 'https://twitter.com/i/profiles/show/{}/timeline/tweets?'
BASE_URL += 'include_available_features=1&'
BASE_URL += 'include_entities=1&'
BASE_URL += 'max_position={}&'
BASE_URL += 'reset_error_state=false'

# Hardcoded for now....
USERS = ['kindafunnyvids', 'amandapalmer', 'cgpgrey', 'Kurz_Gesagt', 
	'EasyAllies', 'FenoxoFenfen', 'TheComedyButton', 'swordandscale', 
	'JimSterling', 'RollPlay', 'PTXofficial', 'CANADALAND', 
	'tarababcock', 'marble_syrup']

MAX_THREADS = 10
FILE_PATH = 'csv/{}_tweets.csv'

def fetch_tweets(user, max_=1000):
	
	cont = 0
	max_position = ''
	data = {}

	# Open file
	path = FILE_PATH.format(user)
	file = open(path, 'w')
	wt = csv.writer(file)

	while max_position is not None and cont < max_:

		url = BASE_URL.format(user, max_position)
		print("Fetching {} ...".format(url))
		try:
			resp = rq.get(url)
			data = resp.json()
		except Exception as e:
			print(resp, resp.reason)
			print(e)
			break

		max_position = data['min_position']
		html = data['items_html']
		tweets = parse_tweets(html)

		if cont <= 0:
			wt.writerow(tweets[0].keys())

		# Store tweets
		for t in tweets:
			wt.writerow(t.values())

		cont += len(tweets)

		print('Fetched {} results'.format(cont))
		print('--------------------------')

	file.close()

def parse_tweets(html):

	soup = BeautifulSoup(html, 'html.parser')
	tweets = soup.select('.tweet')
	
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
	p = Pool(MAX_THREADS)
	p.map(fetch_tweets, USERS)
	p.close()
	p.join()


if __name__ == '__main__':
	main()