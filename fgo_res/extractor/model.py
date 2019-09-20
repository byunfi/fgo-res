class FWTreasureDevice:
    def __init__(self, name, typeText, detail, value, title=None):
        self.name = name
        self.typeText = typeText
        self.detail = detail
        self.value = value
        self.title = title


class FWSkill:
    def __init__(self, num, name, detail, value, title=None):
        self.num = num
        self.name = name
        self.detail = detail
        self.value = value
        self.title = title