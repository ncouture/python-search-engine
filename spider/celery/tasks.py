#!/usr/bin/env python3
#

from xtr import index_this, parse_that, share_links
from spider.celery.daemon import celery


@celery.task
def crawl(url):
    parsed = parse_that(url)
    chain = feed_links.s(parsed) | index.s(parsed)
    chain()


@celery.task
def index(datadict):
    """    datadict: as returned by parse_that
    """
    d = datadict
    index_this(rank=d['rank'],
               title=d['title'], 
               url=d['url'],
               description=d['description'],
               keywords=d['keywords'],
               raw=d['raw'],
               text=d['text'],
               internal_links='|'.join(d['internal_links']),
               external_links='|'.join(d['external_links']))


@celery.task
def feed_links(datadict):
    """    datadict: as returned by parse_that
    """
    for link in datadict['external_links']:
        crawl.delay(link)
    for lnk in datadict['internal_links']:
        crawl.delay(link)


@celery.task
def add(x, y):
    return x + y
