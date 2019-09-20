from .database.fgo import FRDatabase
from copy import deepcopy
from .utils import flatten


class FRUpdater(FRDatabase):
    _perform_key = 'extract_'

    def custom_table(self):
        for add_value_name in ('mstSkillDetail', 'mstTreasureDeviceDetail'):
            self.con.execute(f'ALTER TABLE {add_value_name} add value TEXT')

        renames = ('mstSvt', 'mstSkill', 'mstTreasureDevice', 'mstQuest', 
            'mstItem', 'mstCommandCode')
        for rename in renames:
            self.con.execute(f'ALTER TABLE {rename} RENAME name TO jpName')
            self.con.execute(f'ALTER TABLE {rename} add name TEXT')

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
        pass

    def update_related_quest(self, svtId, names):
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
            update_fn = getattr(self, f'update_{name}')
            update_fn(svtId, items)
