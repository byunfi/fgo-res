from .common import FGOWikiExtractor

class RelatedQuestExtractor(FGOWikiExtractor):
    def extract_related_quests(self):
        def get_title(in_head):
            tables = self.find_tables(in_head, self.WT_LOGO)
            if not tables:
                return []
            return [table.xpath('string(tbody/tr[1]/th[2]/big)') for table in tables]
        return get_title('幕间物语') + get_title('强化任务')
        