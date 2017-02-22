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

from .. import config
from .. import util

MAX_RETRIES = 5
MAX_SLEEP = 3

logger = logging.getLogger(__name__)

tweet_data = ('id', 'text', 'retweet_count',
	'favorite_count', 'created_at', 'lang', 'coordinates')

def filter_data(tweet):
	
	# Should i encode to utf-8 the text?
	tweet.text = util.clean_text(tweet.text)
	
	return tuple(getattr(tweet, attr) for attr in tweet_data)

def twitter_api():
	auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
	auth.set_access_token(config.ACCESS_KEY, config.ACCESS_SECRET)
	return tweepy.API(auth)

def do_request(api, user, id_, count=200, retries=10):

	data = None

	while retries > 0:
		try:
			data = api.user_timeline(
				screen_name=user, count=count, max_id=id_)
			retries = 0
		except Exception as e:
			logger.warning('Error! (%s)', e)
			logger.warning('Retrying in %ss', MAX_SLEEP)
			retries -= 1
			time.sleep(MAX_SLEEP)

	return data

def fetch_tweets(user, max_cont=None, oldest=None):

	api = twitter_api()
	cont = 0

	while max_cont is None or cont < max_cont:

		logger.debug("{} : {}".format(user, oldest))
		chunk = do_request(api, user, oldest)

		if not chunk or len(chunk) <= 0:
			break
		
		yield [filter_data(tweet) for tweet in chunk] 

		oldest = chunk[-1].id - 1
		cont += len(chunk)

		logger.info("Tweets scraped: {}".format(cont))

def scrape_tweets(user):
	
	if not os.path.exists(config.TWEETS_PATH):
		os.makedirs(config.TWEETS_PATH)

	path = config.TWEETS_PATH + '{}_tweets.csv' .format(user)

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
