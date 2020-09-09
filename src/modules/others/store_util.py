from meds.utils import json


def store(self, js, path):
    # path = 'diff_' + str(patch_no) + '_' + file_name + '.json'
    with open(path, 'w') as g:
        json.dump(js, g, sort_keys=True)