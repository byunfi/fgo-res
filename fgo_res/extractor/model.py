class FWTreasureDevice(object):
    def __init__(self, name, typeText, detail, value, title=None):
        self.name = name
        self.typeText = typeText
        self.detail = detail
        self.value = value
        self.title = title


class FWSkill(object):
    def __init__(self, num, name, detail, value, title=None):
        self.num = num
        self.name = name
        self.detail = detail
        self.value = value
        self.title = title


class FWVoice(object):
    def __init__(self, category, stage, lines, audioURL):
        self.category = category
        self.stage = stage
        self.lines = lines
        self.audioURL = audioURL


class FWQuest(object):
    def __init__(self, chapterSubId, name, spotName=None):
        self.chapterSubId = chapterSubId
        self.name = name
        self.spotName = spotName
