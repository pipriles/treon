#!/usr/bin/env python
# encoding: utf-8

import requests as rq
import datetime as dt
import csv
import time
import logging
import os

from .. import config

# I'll make this multithreading to accelerate the
# requests

BASE_URL = 'https://graph.facebook.com/v2.6/'

logger = logging.getLogger(__name__)

access_token = config.APP_ID + '|' + config.APP_SECRET

CSV_HEADER = ["status_id", "status_message", "link_name", 
    "status_type", "status_link", "status_published", 
    "num_reactions", "num_comments", "num_shares", "num_likes", 
    "num_loves", "num_wows", "num_hahas", "num_sads", "num_angrys"]

FROM_DT_FORMAT = '%Y-%m-%dT%H:%M:%S+0000'
TO_DT_FORMAT = '%Y-%m-%d %H:%M:%S'

def do_request(url, params={}, retries=10):

    data = None

    while retries > 0:
        try:
            resp = rq.get(url, params=params)
            data = resp.json()
            retries  = 0
        except Exception as e:
            retries -= 1
            time.sleep(3)   # Put max wait time

    return data

def fetch_posts(page, limit):

    node = '{}/posts'.format(page)

    # I have to move this to a superior scope
    fields  = 'message,link,created_time,type,name,id,shares,'
    fields += 'comments.limit(0).summary(true),'
    fields += 'reactions.limit(0).summary(true)'

    params = {
        'fields': fields,
        'limit': limit,
        'access_token': access_token    # APP ID | APP SECRET
    }

    url = BASE_URL + node

    data = do_request(url, params)

    # Load json from data
    return data

def fetch_reactions(post):

    node = '{}'.format(post)

    fields  = "reactions.type(LIKE).limit(0).summary(total_count).as(like)"
    fields += ",reactions.type(LOVE).limit(0).summary(total_count).as(love)"
    fields += ",reactions.type(WOW).limit(0).summary(total_count).as(wow)"
    fields += ",reactions.type(HAHA).limit(0).summary(total_count).as(haha)"
    fields += ",reactions.type(SAD).limit(0).summary(total_count).as(sad)"
    fields += ",reactions.type(ANGRY).limit(0).summary(total_count).as(angry)"

    params = {
        'fields': fields,
        'access_token': access_token
    }

    url = BASE_URL + node

    data = do_request(url, params)

    # Load json from data
    return data

def parse_post(post):

    def to_datetime(date):
        t = dt.datetime.strptime(date, FROM_DT_FORMAT)
        return t.strftime(TO_DT_FORMAT)

    def get_summary(attr, src):
        if attr in src:
            return src[attr]['summary']['total_count']
        else:
            return 0

    id_ = post['id'] 
    message = post.get('message', '')
    name = post.get('name', '')
    type_ = post.get('type', '')
    link = post.get('link', '')
    created_time = to_datetime(post['created_time'])

    reactions_count = get_summary('reactions', post)
    comments_count = get_summary('comments', post)

    if 'shares' in post:
        shares_count = post['shares']['count']
    else:
        shares_count = 0

    reactions = {}

    if created_time >= '2016-02-24 00:00:00':
        reactions = fetch_reactions(post['id'])
        likes = get_summary('likes', reactions)
    else:
        likes = reactions_count

    loves = get_summary('love', reactions)
    wows = get_summary('wow', reactions)
    hahas = get_summary('haha', reactions)
    sads = get_summary('sad', reactions)
    angrys = get_summary('angry', reactions)

    return (id_, message, name, type_, link, created_time, 
        reactions_count, comments_count, shares_count,
        likes, loves, wows, hahas, sads, angrys)

def write_stats(stats, writer):

    for st in stats:
        if 'reactions' in st:   # Not sure if this is useful
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

    logger.debug('\nDone!')
    logger.debug('{} Statuses processed'.format(count))
    # Remember to put time diff here

    file.close()


if __name__ == '__main__':
    page_demo = 'CuteDogsAndEpicMemes'
    scrape_posts(page_identifier)


