import os
import re

from ..requests_cache import requests
from ..utils import read_csv

__DOMAIN = 'https://fgo.wiki/w'
SERVANT_SECTION = 'servant'


def get_servant_url(link_name):
    return os.path.join(__DOMAIN, link_name)


def get_related_quest_url(link_name):
    return os.path.join(__DOMAIN, link_name, '从者任务')


def get_related_quest_html(link_name):
    url = get_related_quest_url(link_name)
    html_str = requests.getcache(url, SERVANT_SECTION).text
    return html_str


def get_mission_url(name):
    return os.path.join(__DOMAIN, name, '关卡配置')


def get_mission_html(name):
    url = get_mission_url(name)
    html_str = requests.getcache(url, SERVANT_SECTION).text
    return html_str


def get_servant_html(link_name):
    url = get_servant_url(link_name)
    html_str = requests.getcache(url, SERVANT_SECTION).text
    return html_str


def _extract_csv_str(html_str):
    res = re.search(r'var raw_str = "(.*)";', html_str)
    if not res:
        return None
    csv_str = res.group(1)
    return csv_str


def iter_servants_info():
    """Yeild collectionNo, name, link name, nicknames."""
    url = os.path.join(__DOMAIN, '英灵图鉴')
    text = requests.get(url).text
    csv_str = _extract_csv_str(text)
    for no, name, link_name, name_other in read_csv(csv_str, 'id', 'name_cn',
                                                    'name_link', 'name_other'):
        yield int(no), name, link_name, name_other.split('&')
