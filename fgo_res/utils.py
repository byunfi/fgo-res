import sys

def to_screen(message, skip_eol=False):
    terminator = ('\n', '')[skip_eol]
    message += terminator
    sys.stdout.write(message)
    sys.stdout.flush()


def read_csv(s, *fields, separator='\\n'):
    fields_string, *content = s.split(separator)
    fieldnames = fields_string.split(',')
    indexs = [fieldnames.index(n) for n in fields]
    for row in content:
        values = row.split(',')
        yield (values[i] for i in indexs)


def flatten(l):
    return [item for sublist in l for item in sublist]