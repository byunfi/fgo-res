from .common import Database


class FRDatabase(Database):
    def svtId_for_no(self, collectionNo):
        res = self.con.execute(
            'SELECT id FROM mstSvt WHERE collectionNo=? and'
            ' (type=1 or type=2)', (collectionNo,)).fetchone()
        return res[0] if res else None

    def soptId_for_Quest(self, questId):
        res = self.con.execute(
            'select spotId from mstQuest where id=?', 
            (questId,)).fetchone()
        return res[0] if res else None
        
    def servants(self):
        res = self.con.execute(
            'SELECT id, collectionNo, name FROM mstSvt WHERE collectionNo>0'
            ' and (type=1 or type=2) ORDER BY collectionNo').fetchall()
        return res
    
    def main_quests(self):
        res = self.con.execute(
            'select id, jpName, name from mstQuest where type=1'
            ' AND id<93000000').fetchall()
        return res
    
    def free_quests(self):
        res = self.con.execute(
            'select id, jpName, name from mstQuest'
            ' where type=2 and id<94000000').fetchall()
        return res
    
    def get_passiveIds(self, svtId):
        res = self.con.execute(
            'SELECT classPassive as "classPassive [intList]" FROM mstSvt'
            ' WHERE id=?', (svtId,)).fetchone()
        return res[0] if res else []

    def get_ascension_itemIds(self, svtId):
        res = self.con.execute(
            'SELECT itemIds as "itemIds [intList]" FROM mstCombineLimit'
            ' WHERE id=? ORDER BY svtLimit limit 4', (svtId,)).fetchall()
        return [l[0] for l in res]

    def get_skill_itemIds(self, svtId):
        res = self.con.execute(
            'SELECT itemIds as "itemIds [intList]" FROM mstCombineSkill'
            ' WHERE id=? ORDER BY skillLv limit 9', (svtId,)).fetchall()
        return [l[0] for l in res]
    
    def get_related_questIds(self, svtId):
        res = self.con.execute(
            'select relateQuestIds as "relateQuestIds [intList]"'
            ' from mstSvt where id=?', (svtId,)).fetchone()
        return res[0] if res else []

    def find_treasureDeviceId(self, svtId, strengthStatus, flag):
        sql = ('SELECT treasureDeviceId FROM mstSvtTreasureDevice'
               ' WHERE svtId=? AND strengthStatus=? and flag=? AND num=1')
        res = self.con.execute(sql, (svtId, strengthStatus, flag)).fetchone()
        return res[0] if res else None

    def find_treasureDeviceId_v2(self, svtId):
        sql = ('SELECT treasureDeviceId, strengthStatus, flag'
               ' FROM mstSvtTreasureDevice WHERE svtId=? AND num=1')
        res = self.con.execute(sql, (svtId,)).fetchall()
        def find(strengthStatus, flag):
            for td in res:
                if td[1] == strengthStatus and td[2] == flag:
                    return td[0]
        return find
    
    def find_skillId(self, svtId, num, strengthStatus, flag):
        sql = ('SELECT skillId FROM mstSvtSkill'
               ' WHERE svtId=? AND strengthStatus=? and flag=?')
        res = self.con.execute(sql, (svtId, strengthStatus, flag)).fetchone()
        return res[0] if res else None
    
    def find_skillId_v2(self, svtId):
        sql = ('SELECT skillId, num, strengthStatus, flag'
               ' FROM mstSvtSkill WHERE svtId=?')
        res = self.con.execute(sql, (svtId,)).fetchall()
        def find(num, strengthStatus, flag=0):
            for td in res:
                if td[1] == num and td[2] == strengthStatus and td[3] == flag:
                    return td[0]
        return find
    
    def update_mstSvt(self, svtId, name):
        self.update('mstSvt', svtId, name=name)

    def update_mstTreasureDevice(self, tdId, name, typeText):
        self.update('mstTreasureDevice', tdId, name=name, typeText=typeText)
    
    def update_mstTreasureDeviceDetail(self, tdId, detail, value):
        self.update('mstTreasureDeviceDetail', tdId, detail=detail, value=value)

    def update_mstSkill(self, skillId, name):
        self.update('mstSkill', skillId, name=name)
    
    def update_mstSkillDetail(self, skillId, detail, value):
        self.update('mstSkillDetail', skillId, detail=detail, value=value)

    def update_mstItem(self, itemId, name):
        self.update('mstItem', itemId, name=name)

    def update_mstQuest(self, questId, name):
        self.update('mstQuest', questId, name=name)

    def update_mstSpot(self, spotId, name):
        self.update('mstSpot', spotId, name=name)

    def update_mstSvtComment(self, svtId, id, comment):
        self.con.execute('UPDATE mstSvtComment SET comment=? WHERE'
        ' svtId=? and id=?', (comment, svtId, id))

    def update_mstSvtVoice(self, svtId, category, stage, lines, audioURL):
        self.con.execute('INSERT INTO mstSvtVoice VALUES (?,?,?,?,?)', (svtId, category, stage, lines, audioURL))