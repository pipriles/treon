#!/usr/bin/env python
# encoding: utf-8

# I have to investigate how to debug parallel code
# with multiple windows
#
# Change csv folder dest
# Save the state of the script
# Put facebook comments
# Solve tweepy problem

import os
import re
import logging
import time

from queue import Queue
from threading import Thread

# Stuff
from brain import treon
from brain.twitter import tweets
from brain.facebook import posts

MAX_THREADS = 1 # Change this for more threads
MAX_Q_SIZE = 10

#logging.basicConfig(
#	level=logging.DEBUG, 
#	format='%(relativeCreated)6d %(threadName)s %(message)s')

logger = logging.getLogger('brain')

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

frmt = logging.Formatter('[%(threadName)10s][%(module)10s] : %(message)s')
handler.setFormatter(frmt)

logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

q = Queue(MAX_Q_SIZE)

# I don't like this solution
f_queue = Queue()
t_queue = Queue()

class Treon(Thread):

	def __init__(self, data):
		super(Treon, self).__init__()
		self.data = data

	def run(self):
		self.end = False
		ap = treon.ArtistScraper()
		ap.open()

		try:
			while not self.end and self.data:
				user = self.data.pop(0)
				
				logger.info(
					'(%4s) Fetching %s ...', len(self.data), user)
				
				stat = ap.start(user)
				resolve_tasks(stat)

				# Wait to resolve another task

		except Exception as e:
			raise

		finally:
			logger.info('Closed treon task.')
			ap.close()

	def close(self): 
		self.end = True

class FacebookTask(Thread):

	def __init__(self):
		super(FacebookTask, self).__init__()

	# I really need to change this facebook code
	def run(self):
		self.end = False

		while not self.end:
			user = f_queue.get()

			try:
				logger.info('Scraping {} posts'.format(user))
				posts.scrape_posts(user)
			except Exception as e:
				logger.warning(e)
				pass

			# make the same here for the comments
			# q.task_done()

	def close(self):
		logger.info('Closed facebook task.')
		self.end = True

class TwitterTask(Thread):

	def __init__(self):
		super(TwitterTask, self).__init__()

	def run(self):
		self.end = False

		while not self.end:
			user = t_queue.get()

			try:
				logger.info('Scraping {} tweets'.format(user))
				tweets.scrape_tweets(user)
			except Exception as e:
				logger.warning(e)
				pass

	def close(self):
		logger.info('Closed twitter task.')
		self.end = True

def facebook_work(url):
	if url is not None:
		user = re.sub(r'.*facebook\.com\/(?:pages\/)?([^\/]+)\/?.*', r'\1', url)
		f_queue.put(user)

def twitter_work(url):
	if url is not None:
		user = re.sub(r'.*twitter\.com\/(.+)', r'\1', url)
		t_queue.put(user)

def resolve_tasks(artist):

	url = artist.get('facebook_url', None)
	facebook_work(url)

	url = artist.get('twitter_url', None)
	twitter_work(url)

def main():

	threads = []
	data = treon.fetch_creators()

	def finish_threads():
		for t in threads:
			t.close()
			t.join()

	for i in range(MAX_THREADS):
		t = Treon(data)
		threads.append(t)

	threads.append(FacebookTask())
	threads.append(TwitterTask())
	
	for t in threads:
		t.start()
	
	try:
		while True:
			time.sleep(5)
	except BaseException as e:
		logger.debug('Exit! %s', e)
	finally:
		finish_threads()

if __name__ == '__main__':
	main()
