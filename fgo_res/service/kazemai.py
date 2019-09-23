import json
import os
import re
from base64 import b64decode

from lzstring import LZString

from ..requests_cache import requests

__COMMON_DIR = 'http://kazemai.github.io/fgo-vz/common'
COMMENT_SECTION = 'comment'


def masterdata() -> dict:
    url = os.path.join(__COMMON_DIR, 'js', 'master.js')
    text = requests.getcache(url).text
    matched = re.search(
        r"convert_formated_hex_to_string\('(.*)'\)\);", text).group(1)

    def convert_formated_hex_to_string(hex_str):
        length = len(hex_str)
        res = (chr(int(hex_str[i:i+2], 16) | (int(hex_str[i+2:i+4], 16) << 8))
            for i in range(0, length-1, 4))
        return ''.join(res)

    compressed = convert_formated_hex_to_string(matched)
    del matched, text
    res = LZString().decompress(compressed)
    return json.loads(res)


def get_comment_url(svtId):
    return os.path.join(__COMMON_DIR, 'svtcomment', 'jp', str(svtId))


def get_comment_json(svtId):
    url = get_comment_url(svtId)
    resp = requests.getcache(url, COMMENT_SECTION)
    if resp.status_code == 404:
        return None
    decoded = str(b64decode(resp.content), 'utf-8')
    j = json.loads(decoded)
    return j
