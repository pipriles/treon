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

from .. import config

BASE_URL = 'https://twitter.com/i/search/timeline'

USER_AGENT  = "Mozilla/5.0 (X11; Linux x86_64) "
USER_AGENT += "AppleWebKit/537.36 (KHTML, like Gecko) "
USER_AGENT += "Chrome/56.0.2924.87 "
USER_AGENT += "Safari/537.36"

HEADERS = { 'user-agent': USER_AGENT }

TWITTER_HEADER = ['id', 'user', 'text', 'date', 'reply', 'retweet', 'favorite']

FILE_PATH = config.TWEETS_PATH + '{}_tweets.csv'

def do_request(user, max_position, retries=10):

	print("Fetching {} ...".format(user))

	payload = {
		'q': 'from:{}'.format(user),
		'max_position': max_position
	}

	data = None
	while retries > 0:
		try:
			resp = rq.get(BASE_URL, params=payload, headers=HEADERS)
			data = resp.json()
			retries = 0
		except Exception as e:
			retries -= 1
			print(resp, resp.reason)
			print(e)
			time.sleep(3)

	return data

def fetch_tweets(user, max_=1000):
	
	cont =  0
	last = -1

	max_position = ''
	data = {}

	def write_tweets(tweets):
		for t in tweets:
			wt.writerow(t.values())

	if not os.path.exists(config.TWEETS_PATH):
		os.makedirs(config.TWEETS_PATH)

	# Open file
	path = FILE_PATH.format(user)
	file = open(path, 'w', encoding='utf-8')
	wt = csv.writer(file)

	wt.writerow(TWITTER_HEADER)

	while cont > last: # and cont < max_:

		data = do_request(user, max_position)

		if data is None:# or not data['has_more_items']:
			break

		try:
			max_position = data['max_position']
		except KeyError:
			max_position = data['min_position']

		html = data['items_html']
		tweets = parse_tweets(html)

		# Store tweets
		write_tweets(tweets)

		last = cont
		cont += len(tweets)

		print('Fetched {} results'.format(cont))
		print('--------------------------')

	file.close()

def parse_tweets(html):

	soup = BeautifulSoup(html, 'html.parser')
	tweets = soup.select('.original-tweet')
	
	return [scrape_tweet(t) for t in tweets]

def scrape_tweet(tweet):
	
	def cont_attr(attr):
		item_class = 'ProfileTweet-action--{}'.format(attr)
		info = tweet.find('span', class_=item_class)
		return info.span['data-tweet-stat-count']

	def to_datetime(stamp):
		return dt.utcfromtimestamp(int(stamp))

	user_e = tweet.find('span', class_='username')
	tweet_e = tweet.find('div', class_='js-tweet-text-container')
	date_e = tweet.find('span', class_='_timestamp')

	return {
		'id': tweet['data-tweet-id'],
		'user': user_e.b.text,
		'text': re.sub(r'\n', '', tweet_e.text), 
		'date': to_datetime(date_e['data-time']),
		'reply': cont_attr('reply'),
		'retweet': cont_attr('retweet'),
		'favorite': cont_attr('favorite')
	}

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