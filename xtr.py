#!/usr/bin/env python3

import os
import re
import lxml
import lxml.html
import couchdb
import requests #TODO: replace with httplib2
import ngrams

from ngrams import segment
from datetime import datetime
from urllib.parse import urlparse, urljoin
from lxml.html import document_fromstring
from lxml.html.clean import Cleaner

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC, KEYWORD, NGRAMWORDS
from couchdb.mapping import Document, TextField, DateTimeField, ListField, FloatField

schema = Schema(
    title=TEXT(stored=True),
    url=ID(stored=True, unique=True),
    desc=ID(stored=True),
    description=TEXT(stored=True),
    rank=NUMERIC(stored=True, numtype=float),
    raw=TEXT,
    content=TEXT,
    keywords=KEYWORD,
    internal_links=TEXT,
    external_links=TEXT,
    ngramwords=NGRAMWORDS
)

_ix = None


class XTRExcetion:
    pass

def _is_etree(tree):
    if not isinstance(tree, lxml.etree.ElementBase):
        raise XTRExcetion("you're passing something that's not an etree")

    
def get_etree(html):
    return lxml.html.document_fromstring(html)


def get_clean_html(etree, text_only=False):
    _is_etree(etree)
    # enable filters to remove Javascript and CSS from HTML document
    cleaner = Cleaner()
    cleaner.javascript = True
    cleaner.style = True
    cleaner.html = True
    cleaner.page_structure = False
    cleaner.meta = False
    cleaner.safe_attrs_only = False
    cleaner.links = False
    
    html = cleaner.clean_html(etree)
    if text_only:
        return html.text_content()

    return lxml.html.tostring(html)


def doctitle(etree):
    _is_etree(etree)
    return ' '.join([title for title
                     in etree.xpath('//title/text()')])


def meta_name_description(etree):
    _is_etree(etree)
    return ' '.join(etree.xpath("//meta[@name='description']/@content"))


def get_url_keywords(url):
    az_re = re.compile('[a-zA-Z]{1}')
    domain_text = ''.join(urlparse(url).netloc.split('.')[:-1])
    uri_str = ' '.join(urlparse(url).path.split('/'))
    uri_text=''.join(az_re.findall(uri_str))
    keywords = segment('{}{}'.format(domain_text,
                                     uri_text))
    return keywords


def get_links(etree, page_url):
    """    page_url: the url of the page parsed in the etree
    """
    _is_etree(etree)
    links = [urljoin(page_url, i)
             for i in etree.xpath('//a/@href')]

    localhost = urlparse(page_url).hostname
    internal = set()
    external = set()
    for link in links:
        if not urlparse(link).hostname == localhost:
            internal.add(link)
        else:
            external.add(link)

    return {'internal': list(internal),
            'external': list(external)}


def parse_that(url):
    resp = requests.get(url)
    url = url
    raw = resp.text
    tree = get_etree(raw)
    title = doctitle(tree)
    links = get_links(tree, url)
    keywords = get_url_keywords(url)
    meta_description = meta_name_description(tree)
    html = get_clean_html(tree)
    text_content = get_clean_html(tree, text_only=True)
    return {'rank': 0,
            'title': title,
            'url': url,
            'description': meta_description,
            'keywords': keywords,
            'raw': raw,
            'text': text_content,
            'internal_links': links['internal'],
            'external_links': links['external']}


def index_this(rank, title, url, description,
               keywords, raw, text, internal_links, external_links):
    since = get_last_change()
    writer = get_writer()
    last_change = since
    text_content = text
    meta_description = description

    # index
    writer.update_document(
        title=title,
        url=url,
        desc=meta_description,
        description=meta_description,
        rank=0,
        raw=raw,
        content=text_content,
        keywords=keywords,
        ngramwords=text_content,
        internal_links=internal_links,
        external_links=external_links
    )
        
    writer.commit()

    # update last_change indicator
    writer = get_writer()
    set_last_change(since)


def share_links():
    pass


def get_index():
    global _ix

    if _ix is not None:
        pass
    elif not os.path.exists("indexdir"):
        os.mkdir("indexdir")
        _ix = index.create_in("indexdir", schema)
    else:
        _ix = index.open_dir("indexdir")

    return _ix


def get_writer():
    return get_index().writer()


def get_searcher():
    return get_index().searcher()


def get_last_change():
    get_index() # create directory

    if os.path.exists("indexdir/since.txt"):
        try:
            return int(open("indexdir/since.txt").read())
        except ValueError:
            return 0
    else:
        return 0


def set_last_change(since):
    get_index() # create directory

    open("indexdir/since.txt", "w").write(str(since))
