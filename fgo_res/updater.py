from .database.fgo import FRDatabase
from copy import deepcopy
from .utils import flatten, to_screen
import math


class FRUpdater(FRDatabase):
    _perform_key = 'extract_'

    def is_mstSvtComment_loaded(self):
        return self.table_exists('mstSvtComment')

    def is_masterData_loaded(self):
        return self.table_exists('mstSkillDetail')

    def custom_table(self):
        for add_value_name in ('mstSkillDetail', 'mstTreasureDeviceDetail'):
            if self.field_exists('value', add_value_name):
                continue
            self.con.execute(f'ALTER TABLE {add_value_name} add value TEXT')

        renames = ('mstSvt', 'mstSkill', 'mstTreasureDevice', 'mstQuest', 
            'mstItem', 'mstCommandCode', 'mstSpot')
        for rename in renames:
            if self.field_exists('jpName', rename):
                continue
            self.con.execute(f'ALTER TABLE {rename} RENAME name TO jpName')
            self.con.execute(f'ALTER TABLE {rename} add name TEXT')

        if not self.field_exists('jpComment', 'mstSvtComment'):
            self.con.execute(f'ALTER TABLE mstSvtComment RENAME comment TO jpComment')
        if not self.field_exists('comment', 'mstSvtComment'):
            self.con.execute(f'ALTER TABLE mstSvtComment add comment TEXT')
        self.create_mstSvtVoice()

    def create_mstSvtIndex(self):
        self.con.execute('''CREATE TABLE IF NOT EXISTS mstSvtIndex (
            id integer PRIMARY KEY,
            collectionNo integer,
            name text,
            jpName text,
            classId integer,
            cardIds text,
            individuality text,
            genderType integer,
            attri integer,
            rarity integer,
            hpMax integer,
            atkMax integer,
            power integer,
            defense integer,
            agility integer,
            magic integer,
            luck integer,
            treasureDevice integer,
            policy integer,
            personality integer,
            deity integer,
            linkName text,
            nickNames text
            )''')
        svts = self.con.execute(
            'SELECT id,collectionNo,name,jpName,classId,cardIds,individuality,'
            'genderType,attri FROM mstSvt WHERE collectionNo>0 and (type=1 or type=2)').fetchall()
        ph = ','.join(['?'] * 23)
        for svt in svts:
            limit = self.con.execute(
                'SELECT rarity,hpMax,atkMax,power,defense,agility,magic,luck,'
                'treasureDevice,policy,personality,deity FROM mstSvtLimit'
            ).fetchone()
            self.con.execute(
                f'INSERT OR REPLACE INTO mstSvtIndex VALUES ({ph})',
                svt + limit + ('', ''))

    def create_mstSvtVoice(self):
        self.con.execute("""CREATE TABLE IF NOT EXISTS mstSvtVoice (
            svtId interger,
            category text,
            stage text,
            lines text,
            audioURL text
        )""")

    def update_mstSvtIndex(self, svtId, link_name, nicknames):
        self.update(
            'mstSvtIndex', svtId, linkName=link_name, nickNames=nicknames)

    def update_name(self, svtId, name):
        self.update_mstSvt(svtId, name)

    def update_treasure_devices(self, svtId, tds):
        # prepare
        tds = sorted(tds, key=lambda td: td.title)
        has_strengthStatus = False
        td0 = tds[0]
        if len(tds) > 2 and td0.title == '真名解放、强化后':
            has_strengthStatus = True
            td1 = deepcopy(td0)
            td1.name = '？？？'
            td1.title = '强化后'
            tds.insert(1, td1)

        matcher = self.find_treasureDeviceId_v2(svtId)
        for td in tds:
            # match `strengthStatus` and `flag`
            title = td.title
            strengthStatus = 1 if has_strengthStatus else 0
            flag = 0

            if title == '强化前':
                strengthStatus = 1
            elif title == '强化后':
                strengthStatus = 2
            elif title == '真名解放前':
                flag = 0
            elif title == '真名解放后':
                flag = 2
            elif title == '真名解放、强化后':
                flag = 2
                strengthStatus = 2

            tdId = matcher(strengthStatus, flag)
            self.update_mstTreasureDevice(tdId, td.name, td.typeText)
            self.update_mstTreasureDeviceDetail(tdId, td.detail, td.value)

    def update_skills(self, svtId, skills):
        matcher = self.find_skillId_v2(svtId)
        for skill in skills:
            title = skill.title
            strengthStatus = 0
            if title == '强化前':
                strengthStatus = 1
            elif title == '强化后':
                strengthStatus = 2
            skillId = matcher(skill.num, strengthStatus)
            self.update_mstSkill(skillId, skill.name)
            self.update_mstSkillDetail(skillId, skill.detail, skill.value)

    def update_passives(self, svtId, skills):
        passiveIds = self.get_passiveIds(svtId)
        for skillId, skill in zip(passiveIds, skills):
            self.update_mstSkill(skillId, skill.name)
            self.update_mstSkillDetail(skillId, skill.detail, skill.value)

    def _update_material(self, itemIds, namegroups):
        itemIds = flatten(itemIds)
        names = flatten(namegroups)
        assert len(names) == len(itemIds)
        self.con.executemany('UPDATE mstItem SET name=? WHERE id=?',
                             zip(names, itemIds))

    def update_ascension_materials(self, svtId, namegroups):
        itemIds = self.get_ascension_itemIds(svtId)
        self._update_material(itemIds, namegroups)

    def update_skill_materials(self, svtId, namegroups):
        itemIds = self.get_skill_itemIds(svtId)
        self._update_material(itemIds, namegroups)

    def update_bondstories(self, svtId, stories):
        for index, story in enumerate(stories):
            self.update_mstSvtComment(svtId, index+1, story[1])

    def update_voices(self, svtId, voices):
        if self.con.execute('SELECT svtId FROM mstSvtVoice WHERE svtId=? LIMIT 1', (svtId, )).fetchone():
            return
        for voice in voices:
            self.update_mstSvtVoice(svtId, voice.category, voice.stage, voice.lines, voice.audioURL)

    def update_related_quests(self, svtId, names):
        questIds = self.get_related_questIds(svtId)
        assert len(names) == len(questIds)
        self.con.executemany('UPDATE mstQuest SET name=? WHERE id=?',
                             zip(names, questIds))

    def perfrom_update(self, svtId, extractor):
        update_names = [
            name[len(self._perform_key):]
            for name in type(extractor).__dict__.keys()
            if name.startswith(self._perform_key)
        ]
        for name in update_names:
            extract_fn = getattr(extractor, f'extract_{name}')
            items = extract_fn()
            if items:
                update_fn = getattr(self, f'update_{name}')
                update_fn(svtId, items)

    # Mssions

    def _get_part_range(self):
        min_part_id, max_part_id = self.con.execute(
            'SELECT Min(id), Max(id) FROM mstQuest WHERE id <10000000').fetchone()

        def get_part(n):
            return math.floor(n / 1000000)
        return get_part(min_part_id), get_part(max_part_id)

    def _get_chapter_range(self, part):
        min_chapter_id, max_chapter_id = self.con.execute(
            f'select  Min(id), Max(id) from mstQuest where id between ? and ?', (part*1000000-1, part*1000000+1000)).fetchone()
        def get_chapter(n):
            return math.floor((n - part*1000000) / 100)
        return get_chapter(min_chapter_id), get_chapter(max_chapter_id)


    def update_main_quests(self, part, chapter, quests):
        start = part*1000000+100*chapter-1
        end = part*1000000+100*(chapter+1)
        game_sub_chapters = self.con.execute(
            'select id, chapterSubId, jpName from mstQuest where id'
            ' between ? and ?',(start, end)).fetchall()
        for questId, chapterSubId, jpName in game_sub_chapters:
            for index, quest in enumerate(quests):
                if quest.chapterSubId == chapterSubId:
                    self.update_mstQuest(questId, quest.name)
                    to_screen(
                        f'{chapterSubId} {quest.name} {jpName}')
                    del quests[index]
                    break
                else:
                    if quest.chapterSubId > chapterSubId:
                        to_screen(f'Skipped Part{part} Chapter{chapter}.{chapterSubId}')
                        break
                    else:
                        to_screen(f'Failed to handle Part{part} Chapter{chapter}.{chapterSubId}')
                        break

    def update_free_quests(self, part, chapter, quests):
        def get_start_id(part, chapter):
            if part == 1:
                part = 0
            elif part == 3:
                chapter += 1
            return 93000000 + part*10000 + 100*chapter
        
        start = get_start_id(part, chapter)
        end = get_start_id(part, chapter+1)
        game_sub_chapters = self.con.execute(
            'select id, chapterSubId, jpName from mstQuest where id between'
            ' ? and ?',(start, end)).fetchall()
        assert len(game_sub_chapters) == len(quests)
        for game_quest, quest in zip(game_sub_chapters, quests):
            questId, chapterSubId, jpName = game_quest
            self.update_mstQuest(questId, quest.name)
            spotId = self.soptId_for_Quest(questId)
            assert(spotId is not None)
            self.update_mstSpot(spotId, quest.spotName)
            to_screen(f'{chapterSubId} {quest.name} {jpName}')