
import fnmatch

# parse the proc interface for unix domain sockets
def parse_proc():
    results = {}

    with open('/proc/net/unix') as file:
        header = next(file).split(' ')
        names = []
        for name in header[1:]:
            name = name.strip()
            if name:
                names.append(name)

        for line in file:
            key = line.split(': ')[0]
            values = line.split(': ')[1].split(' ')

            result = {}

            i = 0
            for value in values:
                value = value.strip()
                if value:
                    result[names[i]] = value
                    i += 1

            results[key] = result

    return results

# find named UNIX domain sockets according to a user-specified wildcard
def find_named_sockets(pattern=None):
    candidates = []

    for entry in parse_proc().values():
        if 'Path' in entry and entry['Path'].startswith('/'):
            path = entry['Path'][1:]
            if pattern is None or fnmatch.fnmatchcase(path, pattern):
                candidates.append(path)

    return candidates

# find abstract UNIX domain sockets according to a user-specified wildcard
def find_abstract_sockets(pattern=None):
    candidates = []

    for entry in parse_proc().values():
        if 'Path' in entry and entry['Path'].startswith('@'):
            path = entry['Path'][1:]
            if pattern is None or fnmatch.fnmatchcase(path, pattern):
                candidates.append(path)

    return candidates
