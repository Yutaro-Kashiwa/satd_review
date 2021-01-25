import os
import re
import shutil

from exe.distribution_util.merge import find_files
debug = "review/qt/170001-180000/170001-170200/"
debug = ""
frm = "/Users/yutarokashiwa/Desktop/rowdata/" + debug
to = "/Users/yutarokashiwa/rowdata/" + debug
detail_file = ".*/detail\.json"
query_file = ".*/query\.json"
diff_files = ".*/diff_files_.*\.json"
ab_file = ".*/\d_.*\.json"
files = [detail_file, query_file, diff_files, ab_file]
if __name__ == '__main__':
    rtn = []
    all_files = find_files(frm, "**/**.json")
    print(len(all_files))
    for a in all_files:
        print(a)
        for file in files:
            result = re.match(frm+file, fr'{a}')
            if result:
                copy_dist = a.replace(frm, to)
                os.makedirs(os.path.dirname(copy_dist), exist_ok=True)
                shutil.copyfile(a, copy_dist)
                break
