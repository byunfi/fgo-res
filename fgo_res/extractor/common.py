from lxml import etree


class MediaWikiExtractor(object):
    """根据`标题`对网页正文部分进行区域划分.
    Attributes:
        root: <div class="mw-parser-output">节点
    """
    def __init__(self, html, base_url):
        html = etree.HTML(html)
        self.root = html.find(
            './/*[@id="mw-content-text"]/div[@class="mw-parser-output"]')
    
    def find(self, in_head):
        """
        Attributes:
            in_head: head content.
        """
        node = self.root.find(f'./*/span[@id="{in_head}"]/..')
        if node is None:
            return None
        stop_tag = node.tag
        while 1:
            node = node.getnext()
            tag = node.tag
            if tag == stop_tag or (not isinstance(tag, str)) or (
                len(tag) > 1 and tag.startswith('h') and tag < stop_tag):
                break
            yield node


class FGOWikiExtractor(MediaWikiExtractor):

    WT_NOMOBILE_LOGO = 'wikitable nomobile logo'
    WT_LOGO = 'wikitable logo'
    WT_NOMOBILE = 'wikitable nomobile'
    WT = 'wikitable'
    NOMOBILE = 'nomobile'

    def __init__(self, html):
        super(FGOWikiExtractor, self).__init__(html, 'https://fgo.wiki/w')

    def find_tables(self, in_head, table_class, keep_struct=False):
        for node in self.find(in_head):
            cls = node.get('class')
            if not cls and table_class is not None:
                continue
            if node.tag == 'div' and cls.startswith('tabber'):
                res = node.xpath(
                    f'descendant::table[starts-with(@class,"{table_class}")]')
                if keep_struct:
                    yield [table for table in res]
                else:
                    for table in res:
                        yield table
            elif node.tag == 'table' and table_class == cls:
                yield node