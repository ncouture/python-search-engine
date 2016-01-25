from __future__ import absolute_import

from celery import Celery

celery = Celery(include=[
    'spider.celery.tasks'
])

celery.config_from_object('spider.celeryconfig')

if __name__ == '__main__':
    celery.start()
            
