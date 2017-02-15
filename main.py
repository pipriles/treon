#!/usr/bin/env python
# encoding: utf-8

# I have to investigate how to debug parallel code
# with multiple windows
#
# Change csv folder dest
# Save the state of the script
# Put facebook comments
# Solve tweepy problem

import re
import logging

from queue import Queue
from threading import Thread

# Stuff
from brain import treon
from brain.twitter import tweets
from brain.facebook import posts

MAX_THREADS = 6
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
f_queue = Queue(1)
t_queue = Queue(1)

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
				stat = ap.start(user)
				resolve_tasks(stat)

		except Exception as e:
			raise e

		finally:
			ap.close()

	def close(self): 
		self.end = True

class FacebookTask(Thread):

	def __init__(self):
		super(FacebookTask, self).__init__()
		self.token = posts.access_token

	# I really need to change this facebook code
	def run(self):
		while True:
			user = f_queue.get()

			logger.info('Scraping {} posts'.format(user))
			posts.scrapeFacebookPageFeedStatus(user, self.token)
			# q.task_done()
			# Name very long

class TwitterTask(Thread):

	def __init__(self):
		super(TwitterTask, self).__init__()
		self.user = None

	def run(self):
		while True:
			user = t_queue.get()

			logger.info('Scraping {} tweets'.format(user))
			tweets.scrape_tweets(user)

def facebook_work(url):
	if url is not None:
		user = re.sub(r'.*facebook\.com\/(.+)', r'\1', url)
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
		fb_thread.join()
		tw_thread.join()
		for t in threads:
			t.join()
		
	for i in range(MAX_THREADS):
		t = Treon(data)
		t.start()
		threads.append(t)

	fb_thread = FacebookTask()
	tw_thread = TwitterTask()

	fb_thread.start()
	tw_thread.start()
	
	finish_threads() # Block till end

	# try:
	# 	while True:
	# 		resolve_tasks()
	# except BaseException as e:
	# 	finish_threads(threads)
	# 	raise e

	# block until all tasks are done
	# q.join()

if __name__ == '__main__':
	main()
