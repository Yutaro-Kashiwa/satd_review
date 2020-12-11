import json
from json import JSONDecodeError

from exe import CONFIG_DIR


def get_languages(project, sub_project):
    path = CONFIG_DIR/'langs'/project/(sub_project+'.txt')
    with open(path) as f:
        l = f.readlines()[0]
        li = list(l.split(' ')[2:])
        return li


def read_json(file):
    print("open->", file)
    f = open(file, 'r')
    json_load = json.load(f)
    f.close()
    return json_load

