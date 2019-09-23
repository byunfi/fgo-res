import re

from .common import FGOWikiExtractor
from .model import FWTreasureDevice, FWSkill, FWVoice


class ServantExtractor(FGOWikiExtractor):
    def _extract_detail(self, trs):
        names = []
        values = []
        for tr in trs:
            if tr[0].tag == 'th':
                name = tr.xpath('string(th)').rstrip('\n')
                names.append(name)
            else:
                value = [v.rstrip('\n') for v in tr.xpath('td//text()')]
                values.append(value)
        assert len(names) == len(values)
        return names, values

    def extract_name(self):
        table = next(self.find_tables('基础数值', self.WT_NOMOBILE))
        name = table.xpath('string(tbody/tr[1]/th[1])').rstrip('\n')
        return name

    def collectionNo(self):
        table = next(self.find_tables('基础数值', self.WT_NOMOBILE))
        res = table.xpath('string(tbody/tr[1]/th[2])').rstrip('\n')
        return int(res[3:])

    def extract_treasure_devices(self):
        tables = self.find_tables('宝具', self.WT_NOMOBILE_LOGO)
        tds = []
        for table in tables:
            trs = table.xpath('tbody/tr')
            title = table.getparent().get('title')
            if title and (title.endswith('限定') or title.startswith('灵基再临')):
                continue
            name = trs[0].xpath('string(td/big)')
            typeText = trs[0].xpath('string(th/p[last()])')
            detail = self._extract_detail(trs[2 - len(trs) % 2:])

            td = FWTreasureDevice(name, typeText, *detail, title)
            tds.append(td)
        return tds

    def extract_skills(self):
        tables = self.find_tables('持有技能', self.WT_NOMOBILE_LOGO, True)
        skills = []
        for index, items in enumerate(tables):
            if not isinstance(items, list):
                items = [items]
            for table in items:
                trs = table.xpath('tbody/tr')
                name = trs[0].xpath('string(th[2])').rstrip('\n')
                detail = self._extract_detail(trs[2:])
                title = table.getparent().get('title')

                skill = FWSkill(index + 1, name, *detail, title)
                skills.append(skill)
        return skills

    def extract_passives(self):
        res = self.find_tables('职阶技能', self.WT_NOMOBILE_LOGO, True)

        passives = []
        for table in res:
            if isinstance(table, list):
                table = table[0]
            trs = table.xpath('tbody/tr')
            for tr in trs:
                if tr[0].tag == 'th':  # name
                    name = tr.xpath('string(th[2])').rstrip('\n ')
                    level = tr.xpath('string(td)')
                    if level.startswith('固有等级：'):
                        level = level[5:].strip('\n ')
                    name = f'{name} {level}'
                else:  # description
                    detail = re.split('&|＆',
                                      tr.xpath('string(td)').rstrip('\n'))
                    descrs = []
                    values = []
                    for one in detail:
                        result = re.search(r'\((\d+(\.\d+)?(%)?)\)', one)
                        if result:
                            descrs.append(one[:result.span()[0]])
                            values.append(result.group(1))
                        else:
                            descrs.append(one)
                            values.append('∅')
                    passive = FWSkill(-1, name, descrs, values)
                    passives.append(passive)
        return passives

    def _extract_materials(self, table):
        # remove last row for total material
        trs = table.xpath('tbody/tr')[:-1]
        titles = ((td.xpath('descendant::a/@title') for td in tr.xpath('td'))
                  for tr in trs)
        item_names = []
        # sort
        for row in zip(*titles):
            item_names += row
        return item_names

    def extract_skill_materials(self):
        for table in self.find_tables('技能强化', self.WT_NOMOBILE):
            return self._extract_materials(table)

    def extract_ascension_materials(self):
        for table in self.find_tables('灵基再临（从者进化）', self.WT_NOMOBILE):
            return self._extract_materials(table)

    def extract_bondstories(self):
        stroies = []
        for table in self.find_tables('资料', self.WT):
            trs = table.xpath('tbody/tr')
            assert (len(trs) == 2)
            cond = trs[0].xpath('string(th)').rstrip('\n')
            story = trs[1].xpath('string(td/div/div/p)').rstrip('\n')
            stroies.append((cond, story))
        return stroies
    
    def extract_voices(self):
        items = []
        for table in self.find_tables('语音', self.WT_MW_NOMOBILE):
            trs = table.xpath('tbody/tr')
            category = trs[0].xpath('string(th/b)')
            items += [FWVoice(category, tr.xpath('string(th/b)'), 
            tr.xpath('string(td[1]/p)'), tr.xpath('string(td[2]/span/a[last()]/@href)')) for tr in trs[1:]]
        return items


    def _extract_battle_images(self):
        tables = list(self.find_tables('战斗形象', self.WT))
        count = len(tables)
        if count == 2:
            _ = tables[0]
        # TODO:
