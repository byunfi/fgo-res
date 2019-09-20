import os
import shutil
import traceback

from .utils import to_screen


class Cache(object):
    def __init__(self, rootdir=None):
        if rootdir is None:
            rootdir = os.path.join('~', '.cache', 'fgores')
        self.rootdir = os.path.expandvars(os.path.expanduser(rootdir))

    def _get_cache_fn(self, section, key):
        return os.path.join(self.rootdir, section, key)

    def isCached(self, section, key):
        fn = self._get_cache_fn(section, key)
        return os.path.exists(fn)

    def store(self, section, key, data, mode='wb+'):
        fn = self._get_cache_fn(section, key)
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        try:
            with open(fn, mode) as wf:
                wf.write(data)
        except Exception:
            tb = traceback.format_exc()
            to_screen(f'Writing cache to {fn} failed: {tb}')

    def load(self, section, key, mode='rb', default=None):
        fn = self._get_cache_fn(section, key)
        try:
            with open(fn, mode) as f:
                return f.read()
        except IOError:
            pass  # No cache available
        return default

    def remove(self, section=''):
        cachedir = self._get_cache_fn(section, '')
        if os.path.exists(cachedir):
            shutil.rmtree(cachedir)
            to_screen('Removing cache dir {cachedir}.', skip_eol=True)


default_cache = Cache()