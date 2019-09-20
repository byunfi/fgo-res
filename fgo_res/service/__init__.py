from ..requests_cache import requests


from .kazemai import *
from .mooncell import *


def predownload_servants(link_names):
    urls = list(map(lambda n: get_servant_url(n), link_names))
    requests.setcaches(urls, SERVANT_SECTION)


def predownload_comments(svtIds):
    urls = list(map(lambda i: get_comment_url(i), svtIds))
    requests.setcaches(urls, COMMENT_SECTION)






