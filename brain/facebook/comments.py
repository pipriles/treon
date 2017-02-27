#!/usr/bin/env python
# encoding: utf-8

import requests as rq
import csv
import time
import logging
import os

from .. import config
from .. import util

# Handle error when posts file doesnt exists
# Still think this module is ugly and slow

logger = logging.getLogger(__name__)

BASE_URL = 'https://graph.facebook.com/v2.6/'

HEADER = [\
    'status_id', 'parent_id', 'comment_id', 'comment_message', 
    'comment_author', 'comment_likes', 'comment_published']

ACCESS_TOKEN = config.APP_ID + "|" + config.APP_SECRET

def do_request(url, params={}, retries=10):

    # This function can be moved to the __init__.py

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

def fetch_comments(post_id, limit=100):

    node = "{}/comments".format(post_id)

    fields  = "id,message,like_count,created_time,"
    fields += "comments,from,attachment"

    params = {
        'fields': fields,
        'order': 'chronological',
        'limit': str(limit),
        'access_token': ACCESS_TOKEN
    }

    url = BASE_URL + node

    comments = do_request(url, params)

    return comments

def parse_comments(comment, post, parent=''):

    id_ = comment['id']
    message = comment.get('message', '')
    author = comment['from']['name']
    likes = comment.get('like_count', 0)

    # Wtf is this
    if 'attachment' in comment:
        message += ' ' if message else ''
        message += "[[{}]]".format(comment['attachment']['type'].upper())

    # Make it to one line
    message = util.clean_text(message)
    published = util.to_datetime(comment['created_time'])

    return (post, parent, id_, message, author, likes, published)

def read_posts(reader, writer):

    cont = 0
    for post in reader:
        id_ = post['status_id']
        r_comments(id_, id_, writer)
        cont += 1
        logger.debug('%s Posts comments scraped', cont)

# Fetch comments with recursion

def r_comments(parent, status, writer):

    count = 0
    done = False
    comments = fetch_comments(parent)

    while not done:
        
        # logger.debug(comments)

        for comment in comments.get('data', {}):
            row = parse_comments(comment, status, parent)
            writer.writerow(row)

            if 'comments' in comment:
                #logger.debug('Subcomment!')
                r_comments(comment['id'], status, writer)

            count += 1
            logger.info("%s Comments Processed", count)

        if 'next' in comments.get('paging', {}):
            comments = do_request(comments['paging']['next'])
        else:
            done = True

    # logger.debug('End!')

def scrape_comments(post):

    if not os.path.exists(config.COMMENTS_PATH):
        os.makedirs(config.COMMENTS_PATH)

    # This should not be file_id
    c_path  = config.COMMENTS_PATH
    c_path += '{}_comments.csv'.format(post)

    with open(c_path, 'w', encoding='utf-8') as fcomment:
        writer = csv.writer(fcomment)
        writer.writerow(HEADER)

        p_path  = config.POSTS_PATH
        p_path += '{}_posts.csv'.format(post)

        with open(p_path, 'r', encoding='utf-8') as fpost:
            reader = csv.DictReader(fpost)

            # Fetch comments per post
            read_posts(reader, writer)

    logger.debug('Finished to scrape!')

if __name__ == '__main__':
    # Nope, not today
    pass
