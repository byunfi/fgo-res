from . import service
from .updater import FRUpdater
from .extractor import ServantExtractor
from .utils import to_screen
import os
from shutil import copyfile


class FGORes(object):
    def __init__(self, path):
        self.updater = FRUpdater(path)

    def start(self):
        self.setup_database()
        updater = self.updater
        servants = list(service.iter_servants_info())
        # download resources.
        svtIds = map(lambda s: s[0], updater.servants())
        to_screen('Downloading comments from kazemai...')
        service.predownload_comments(svtIds)

        link_names = map(lambda s: s[2], servants)
        to_screen('Downloading servants from mooncell...')
        service.predownload_servants(link_names)

        for no, name, link_name, nicknames in servants:
            to_screen(f'{no} {name}')
            svtId = updater.svtId_for_no(no)
            if no in (0, 1):
                continue
            if svtId is None:
                continue
            self.update_servant(link_name, svtId)
        #TODO add ignored servants.
        updater.create_mstSvtIndex()
        for no, _, link_name, nicknames in servants:
            svtId = updater.svtId_for_no(no)
            updater.update_mstSvtIndex(svtId, link_name, nicknames)
        updater.commit()

    def setup_database(self):
        updater = self.updater
        # record jp master data
        to_screen('Decoding compressed masterData from kazemai...')
        records = service.masterdata()
        to_screen('Writing to database...')
        updater.load_json(records)
        updater.custom_table()
        updater.commit()

    def update_servant(self, link_name, svtId=None):
        servant_html = service.get_servant_html(link_name)
        se = ServantExtractor(servant_html)
        if svtId is None:
            no = se.collectionNo()
            svtId = self.updater.svtId_for_no(no)
        self.updater.perfrom_update(svtId, se)