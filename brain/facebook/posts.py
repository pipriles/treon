#!/usr/bin/env python
# encoding: utf-8

import requests as rq
import datetime as dt
import csv
import time
import logging
import os

from .. import config
from .. import util

# I have to put the filter to the text of the posts

logger = logging.getLogger(__name__)

BASE_URL = 'https://graph.facebook.com/v2.6/'

ACCESS_TOKEN = config.APP_ID + '|' + config.APP_SECRET

CSV_HEADER = ["status_id", "status_message", "link_name", 
    "status_type", "status_link", "status_published", 
    "num_reactions", "num_comments", "num_shares", "num_likes", 
    "num_loves", "num_wows", "num_hahas", "num_sads", "num_angrys"]

REACTIONS = ['LIKE', 'LOVE', 'WOW', 'HAHA', 'SAD', 'ANGRY']

FROM_DT_FORMAT = '%Y-%m-%dT%H:%M:%S+0000'
TO_DT_FORMAT = '%Y-%m-%d %H:%M:%S'

MAX_SLEEP = 3

def to_hashtable(posts):
    return { p['id']:p for p in posts }

def to_datetime(date):
        t = dt.datetime.strptime(date, FROM_DT_FORMAT)
        return t.strftime(TO_DT_FORMAT)

def do_request(url, params={}, retries=10):

    data = None

    while retries > 0:
        try:
            resp = rq.get(url, params=params)
            data = resp.json()
            retries  = 0
        except Exception as e:
            logger.warning('Error! %s', e)
            logger.warning('Retrying in %ss', MAX_SLEEP)
            retries -= 1
            time.sleep(MAX_SLEEP)   # Put max wait time

    return data

def put_reaction(react, ptab, rtab):

	default = { 'reactions': { 'summary': { 'total_count': 0 } } }

	# Maybe i'll change this solution in the future
	for key in ptab:
		ptab[key][react] = rtab.get(key, default)['reactions']

def fetch_reactions(posts, url, params):

    reacts = 'reactions.limit(0).summary(true).type({})'
    ptab = to_hashtable(posts['data'])

    for react in REACTIONS:
        params['fields'] = reacts.format(react)

        # Fetch for each reaction and combine
        resp = do_request(url, params)
        rtab = to_hashtable(resp['data'])

        put_reaction(react.lower(), ptab, rtab)

def fetch_posts(page, limit=100):

    logger.debug('Fetching posts from %s', page)
    node = '{}/posts'.format(page)

    # I have to move this to a superior scope
    fields  = 'message,link,created_time,type,name,id,shares,'
    fields += 'comments.limit(0).summary(true)'

    params = {
        'fields': fields,
        'limit': limit,
        'access_token': ACCESS_TOKEN
        # APP ID | APP SECRET
    }

    url = BASE_URL + node
    
    # First request
    posts = do_request(url, params)
    fetch_reactions(posts, url, params)

    return posts

def parse_post(post):

    def get_summary(attr, src):
        if attr in src:
            return src[attr]['summary']['total_count']
        else:
            return 0

    id_ = post['id'] 
    
    # Get post text
    message = post.get('message', '')
    message = util.clean_text(message)

    name = post.get('name', '')
    type_ = post.get('type', '')
    link = post.get('link', '')
    created_time = to_datetime(post['created_time'])

    comments_count = get_summary('comments', post)
    
    if 'shares' in post:
        shares_count = post['shares']['count']
    else:
        shares_count = 0

    reacts = tuple(get_summary(r, post) for r in REACTIONS)
    reacts_count = sum(reacts)

    return (id_, message, name, type_, link, created_time, 
        reacts_count, comments_count) + reacts

def write_stats(stats, writer):
    
    for st in stats:
        data = parse_post(st)
        writer.writerow(data)

def scrape_posts(page):

    if not os.path.exists(config.POSTS_PATH):
        os.makedirs(config.POSTS_PATH)

    path = config.POSTS_PATH + '{}_posts.csv'.format(page)

    file = open(path, 'w', newline='', encoding='utf-8')
    wt = csv.writer(file)

    wt.writerow(CSV_HEADER)

    done = False
    count = 0

    stats = fetch_posts(page, 100)  # Put max limit to 100

    while not done and stats is not None:
        write_stats(stats['data'], wt)
        count += len(stats['data'])
        logger.info('Statuses processed: {}'.format(count))

        if 'paging' in stats:
            url = stats['paging']['next']
            stats = do_request(url)
        else:
            done = True

    logger.debug('Done!')
    # Remember to put time diff here

    file.close()

if __name__ == '__main__':
    page_demo = 'CuteDogsAndEpicMemes'
    logging.basicConfig(level=logging.DEBUG)
    scrape_posts(page_identifier)


