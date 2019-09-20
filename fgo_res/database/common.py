import sqlite3
from .utils import str2strs, str2ints, list2str, get_sqlite_type, get_primary_keys, json_to_create_table_sql


class Database(object):
    def __init__(self, path):
        self.con = sqlite3.connect(path, detect_types=sqlite3.PARSE_COLNAMES)
        self.con.execute('PRAGMA synchronous = OFF')
        self._register_adapters()

    def __getattr__(self, name):
        return getattr(self.con, name)

    def __del__(self):
        self.con.close()

    def _register_adapters(self):
        # list to string
        sqlite3.register_adapter(list, list2str)
        sqlite3.register_converter("strList", str2strs)
        sqlite3.register_converter("intList", str2strs)
        # dictionary to string
        sqlite3.register_adapter(dict, lambda d: str(d))

    def insert(self, table, **kw):
        fields, values = zip(*kw.items())
        fields_str = ','.join(fields)
        values_str = ','.join(['?'] * len(fields))
        sql = f"INSERT INTO {table} ({fields_str}) values ({values_str})"
        self.con.execute(sql, values)

    def update(self, table, id, **kw):
        keys, values = zip(*kw.items())
        fields = ', '.join(map(lambda k: f'{k}=?', keys))
        sql = f'UPDATE {table} SET {fields} WHERE id=?'
        self.con.execute(sql, values + (id, ))

    def load_json(self, records: dict):
        for tname, records in records.items():
            if not (isinstance(records, list) and len(records)):
                continue
            # create table
            pkey = get_primary_keys(records)
            if pkey: pkey = pkey[0]
            create_sql = json_to_create_table_sql(tname, records[0], pkey)
            self.con.execute(create_sql)
            # fill data
            for record in records:
                self.insert(tname, **record)
        self.con.commit()