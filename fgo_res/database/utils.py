def list2str(l):
    if isinstance(l, list):
        res = ','.join(map(list2str, l))
        return f"[{res}]"
    else:
        return str(l)


def str2strs(s):
    s = s.decode('utf8')[1:-1]
    if s.startswith('['):
        result = s[1:-1].split('],[')
        return [x.split(',') for x in result]
    else:
        return s.split(',')

def str2ints(s):
    s = s.decode('utf8')[1:-1]
    if s.startswith('['):
        result = s[1:-1].split('],[')
        return [int(s) for s in x.split(',') for x in result]
    else:
        return [int(s) for s in s.split(',')]


def get_primary_keys(records):
    """find probable primary (INTEGER) keys from records.

    Args:
        records: a sequence of dictionary which contains records.

    Returns:
        Keys that do not repeat values, else None.
    """
    res = dict()
    for key, value in records[0].items():
        if isinstance(value, int):
            res[key] = set()

    drop = []
    for record in records:
        for key, value in res.items():
            before_len = len(value)
            value.add(record[key])
            if len(value) == before_len:
                drop.append(key)
        for key in drop:
            del res[key]
        if not res:
            return list(res.keys())
        drop.clear()
    return list(res.keys())


def get_sqlite_type(obj):
    """Get an appropriate `sqlite` type for this `obj`."""
    obj_type = type(obj)
    if obj_type in (str, list, dict):
        return 'TEXT'
    elif obj_type == bool:
        return 'BOOLEAN'
    elif obj_type == int:
        return 'INTEGER'
    elif obj_type == float:
        return 'REAL'
    elif obj is None:
        raise TypeError('Can not infer type from a `None` value')
    else:
        raise TypeError('Unsupported type')


def json_to_create_table_sql(tablename, record: dict, primary_key=None):
    """Get a table creation statement from a record."""
    fields = []
    for key, value in record.items():
        stype = get_sqlite_type(value)
        words = [key, stype]
        if primary_key == key:
            words.append('PRIMARY KEY')
        field = ' '.join(words)
        fields.append(field)
    res = ','.join(fields)
    sql = f'CREATE TABLE IF NOT EXISTS {tablename} ({res})'
    return sql
