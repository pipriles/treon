#!/usr/bin/env python
# encoding: utf-8

# Max tweets: 3240

# For user
# - tweet.user.id
# - tweet.user.created_at
# - tweet.user.description
# - tweet.user.favourites_count
# - tweet.user.friends_count
# - tweet.user.followers_count
# - tweet.user.listed_count
# - tweet.user.location
# - tweet.user.url
# - tweet.user.screen_name
# - tweet.user.name
# - tweet.user.verified
# - tweet.user.geo_enabled
# - tweet.user.lang

# For tweets
# - tweet.id
# - tweet.text
# - tweet.retweet_count
# - tweet.favorite_count
# - tweet.lang
# - tweet.coordinates
# - tweet.created_at

import tweepy
import csv
import os
import logging
import time
import random

from ..config import *

MAX_RETRIES = 5

logger = logging.getLogger(__name__)

tweet_data = ('id', 'text', 'retweet_count',
	'favorite_count', 'created_at', 'lang', 'coordinates')

def filter_data(tweet):
	return tuple(getattr(tweet, attr) for attr in tweet_data)
	# Should i encode utf-8 the text?

def fetch_tweets(user, max_cont=None, oldest=None):
	#
	# First steps...
	
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	api = tweepy.API(auth)
	
	retries = MAX_RETRIES
	cont = 0

	while max_cont is None or cont < max_cont:

		logger.debug("{} : {}".format(user, oldest))

		try:
			chunk = api.user_timeline(
				screen_name=user, count=200, max_id=oldest)
		except Exception as e:

			if retries > 0:
				retries -= 1	

				step = random.randint(1, MAX_RETRIES-retries)
				logger.warning('Error!, Retrying {}s ...'.format(step))

				time.sleep(2 ** step)

				continue

			raise e

		if len(chunk) <= 0:
			break
		
		yield [filter_data(tweet) for tweet in chunk] 

		oldest = chunk[-1].id - 1
		cont += len(chunk)

		logger.info("Tweets scraped: {}".format(cont))

def scrape_tweets(user):
	
	if not os.path.exists(TWEETS_PATH):
		os.makedirs(TWEETS_PATH)

	path = TWEETS_PATH + '{}_tweets.csv' .format(user)

	with open(path, 'w', encoding='utf-8') as f:
		
		writer = csv.writer(f)
		writer.writerow(tweet_data)
		
		for tweets in fetch_tweets(user):
			writer.writerows(tweets)

	logger.info('Done.')

def main():
	scrape_tweets('KindaFunnyVids')	# Should i put multithread pool?

if __name__ == '__main__':
	main()
