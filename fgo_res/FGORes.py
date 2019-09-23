import os
from shutil import copyfile
from functools import reduce

from . import service
from .extractor import RelatedQuestExtractor, ServantExtractor, MissionExtarctor
from .updater import FRUpdater
from .utils import NoContent, to_screen, to_screen2


class FGORes(object):
    def __init__(self, path):
        self.updater = FRUpdater(path)
        self._servants = None

    @property
    def servants(self):
        if self._servants is None:
            infos = service.iter_servants_info()
            servants = []
            for info in infos:
                svtId = self.updater.svtId_for_no(info[0])
                if svtId is None:
                    continue
                servants.append((svtId,) + info)
            self._servants = servants
        return self._servants

    def start(self):
        updater = self.updater
        to_screen('Loading masterData...', skip_eol=True)
        if not updater.is_masterData_loaded:
            self.load_masterData()
            updater.commit()
        to_screen(' loaded.')

        servants = self.servants
        svtIds = list(map(lambda s: s[0], servants))

        to_screen('Loading mstSvtComment...', skip_eol=True)
        if not updater.is_mstSvtComment_loaded:
            self.load_mstSvtComment(svtIds)
            updater.commit()
        to_screen(' loaded.')
        # csutom table fields.
        updater.custom_table()
        
        updater.begin()
        to_screen('Start loading servants.')
        for svtId, no, name, link_name, _ in servants[1:]:
            to_screen2(f'loading No.{no} {name}')
            self.update_servant(link_name, svtId)
            if updater.get_passiveIds:
                self.update_related_quest(link_name, svtId)
        to_screen('Apply patches.')
        self.apply_patches()
        updater.end()

        to_screen('Updating Index.')
        updater.create_mstSvtIndex()
        for svtId, _, _, link_name, nicknames in servants:
            updater.update_mstSvtIndex(svtId, link_name, nicknames)
        updater.commit()
        to_screen('Complete.')

    def load_masterData(self):
        datas = service.masterdata()
        self.updater.load_json(datas)

    def load_mstSvtComment(self, svtIds):
        comments = reduce(
                lambda x, y: x + service.get_comment_json(y), svtIds, [])
        self.updater.load_json({'mstSvtComment': comments})
    
    def predownload(self, link_names, svtIds):
        to_screen('Downloading servants from mooncell...')
        service.predownload_servants(link_names)
        to_screen('Downloading servant quests from mooncell...')
        service.predownload_related_quests(link_names)
        to_screen('Downloading comments from kazemai...')
        service.predownload_comments(svtIds)

    def update_servant(self, link_name, svtId=None):
        servant_html = service.get_servant_html(link_name)
        se = ServantExtractor(servant_html)
        if svtId is None:
            no = se.collectionNo()
            svtId = self.updater.svtId_for_no(no)
        self.updater.perfrom_update(svtId, se)

    def update_related_quest(self, link_name, svtId):
        quest_html = service.get_related_quest_html(link_name)
        try:
            qe = RelatedQuestExtractor(quest_html)
        except NoContent:
            pass
        else:
            self.updater.perfrom_update(svtId, qe)

    def update_missions(self):
        missions = [
            (1, 0, '特异点F_燃烧污染都市_冬木'),
            (1, 1, '第一特异点_邪龙百年战争_奥尔良'),
            (1, 2, '第二特异点_永续疯狂帝国_七丘之城'),
            (1, 3, '第三特异点_封锁终局四海_俄刻阿诺斯'),
            (1, 4, '第四特异点_死界魔雾都市_伦敦'),
            (1, 5, '第五特异点_北美神话大战_合众为一'),
            (1, 6, '第六特异点_神圣圆桌领域_卡美洛'),
            (1, 7, '第七特异点_绝对魔兽战线_巴比伦尼亚'),
            (1, 8, '终局特异点_冠位时间神殿_所罗门'),
            (2, 1, '亚种特异点Ⅰ_恶性隔绝魔境_新宿'),
            (2, 2, '亚种特异点Ⅱ_传承地底世界_雅戈泰'),
            (2, 3, '亚种特异点Ⅲ_尸山血河舞台_下总国'),
            (2, 4, '亚种特异点Ⅳ_禁忌降临庭园_塞勒姆'),
            # (3, 0, '序／2017年_12月26日'),
            (3, 1, 'Lostbelt_No.1_永久冻土帝国_阿纳斯塔西娅'),
            (3, 2, 'Lostbelt_No.2_无间冰焰世纪_诸神黄昏'),
            (3, 3, 'Lostbelt_No.3_人智统合真国_SIN'),
            (3, 4, 'Lostbelt_No.4_创世灭亡轮回_宇迦刹土')
        ]
        for part, chapter, name in missions:
            html_str = service.get_mission_html(name)
            me = MissionExtarctor(html_str)
            mains = me.extract_main_quests()
            self.updater.update_main_quests(part, chapter, mains)
            frees = me.extract_free_quests()
            self.updater.update_free_quests(part, chapter, frees)

    def apply_patches(self):
        updater = self.updater
        def extract_detail(lines):
            count = int(len(lines) / 2)
            r = range(count)
            detail = [lines[i * 2] for i in r]
            value = [lines[i * 2 + 1].split('\t') for i in r]
            return detail, value

        def id_name_reader(f):
            while 1:
                line = f.readline()
                if line:
                    id, name = line.split(' ')
                    yield int(id), name
                else: 
                    break

        with open('./fgo_res/extra/name.txt') as name_f:
            for svtId, name in id_name_reader(name_f):
                updater.update_name(svtId, name)

        with open('./fgo_res/extra/treasure_device.txt') as td_f:
            td_texts = td_f.read().split('\n\n')
            for td_text in td_texts:
                lines = td_text.split('\n')
                tdId = int(lines[0])
                td_name = lines[1]
                typeText = lines[2]
                updater.update_mstTreasureDevice(tdId, td_name, typeText)
                td_detail, td_value = extract_detail(lines[3:])
                updater.update_mstTreasureDeviceDetail(tdId, td_detail,
                                                       td_value)
        with open('./fgo_res/extra/quest.txt') as quest_f:
            while 1:
                line = quest_f.readline().rstrip('\n')
                if line:
                    values = line.split(' ')
                    updater.update_mstQuest(int(values[0]), values[2])
                else: 
                    break

    def write_mssions(self):
        main_quests = self.updater.main_quests()
        m = '\n'.join(map(lambda q: f'{q[0]} {q[1]} {q[2]}', main_quests))
        with open('./fgo_res/extra/main_quest.txt', 'w+') as mf:
            mf.write(m)

        free_quests = self.updater.free_quests()
        f = '\n'.join(map(lambda q: f'{q[0]} {q[1]} {q[2]}', free_quests))
        with open('./fgo_res/extra/free_quest.txt', 'w+') as ff:
            ff.write(f)