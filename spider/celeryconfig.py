BROKER_URL = "amqp://guest:guest@localhost:5672//"

#CELERY_RESULT_BACKEND = "couchdb://"

CELERYD_CONCURRENCY = 7

#CELERY_TASK_SERIALIZER='json'

CELERY_QUEUES = {
    "retrieve": {
        "exchange": "default",
        "exchange_type": "direct",
        "routing_key": "retrieve"
    },
    "process": {
        "exchange": "default",
        "exchange_type": "direct",
        "routing_key": "process"
    },
    "celery": {
        "exchange": "default",
        "exchange_type": "direct",
        "routing_key": "celery"
    }
}

CELERY_ROUTES = {
    "tasks.crawl": {
        "queue": "retrieve",
    },
    "tasks.index": {
        "queue": "process",
    }
}
