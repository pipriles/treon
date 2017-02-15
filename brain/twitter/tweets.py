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

from ..config import *

logger = logging.getLogger(__name__)

tweet_data = ('id', 'text', 'retweet_count',
	'favorite_count', 'created_at', 'lang', 'coordinates')

def filter_data(tweet):
	return tuple(getattr(tweet, attr) for attr in tweet_data)
	# Should i encode utf-8 the text?

def fetch_tweets(user, max_cont=None):
	#
	# First steps...
	
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	api = tweepy.API(auth)
	
	oldest = None
	cont = 0

	while max_cont is None or cont < max_cont:

		chunk = api.user_timeline(
			screen_name=user, count=200, max_id=oldest)

		if len(chunk) <= 0:
			break
		
		yield [filter_data(tweet) for tweet in chunk] 

		oldest = chunk[-1].id - 1
		cont += len(chunk)

		logger.info("Tweets scraped: {}".format(cont))

def scrape_tweets(user):
	
	create_csv_folder()
	path = FOLDER_PATH + '{}_tweets.csv' .format(user)

	with open(path, 'w') as f:
		
		writer = csv.writer(f)
		writer.writerow(tweet_data)
		
		for tweets in fetch_tweets(user):
			writer.writerows(tweets)

	logger.info('Done.')

def create_csv_folder():
	try:
		os.mkdir(FOLDER_PATH)
	except FileExistsError:
		pass

def main():
	scrape_tweets('KindaFunnyVids')	# Should i put multithread pool?

if __name__ == '__main__':
	main()
