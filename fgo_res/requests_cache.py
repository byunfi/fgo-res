from multiprocessing.pool import ThreadPool

import requests

from .cache import default_cache as cache

USER_AGENTS = {
    'Safari':
    'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
}


def sanitize_filename(s):
    return s.translate(str.maketrans('/?', "_'", ':'))


def getcache(url, section='') -> requests.Response:
    filename = sanitize_filename(url)
    content = cache.load(section, filename)
    if content is None:
        res = requests.get(url, headers=USER_AGENTS)
        if res.ok:
            cache.store(section, filename, res.content)
    else:
        res = requests.Response()
        res._content = content
        res.status_code = 299  # read from cache
        res.encoding = 'utf-8'
    return res


def setcache(url, section='') -> bool:
    filename = sanitize_filename(url)
    if cache.isCached(section, filename):
        return True
    res = requests.get(url, headers=USER_AGENTS)
    if res.ok:
        cache.store(section, filename, res.content)
        return True
    return False


def setcaches(urls, section=''):
    def _setcache(url):
        setcache(url, section)
        
    pool = ThreadPool(8)
    res = pool.imap_unordered(_setcache, urls)
    for _ in res:
        pass
    pool.close()
    pool.join()


requests.getcache = getcache
requests.setcache = setcache
requests.setcaches = setcaches
