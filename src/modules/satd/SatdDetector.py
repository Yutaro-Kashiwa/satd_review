
import subprocess


import re

import pexpect

from exe import ENV
from modules.source.comments import extract_commentout


class SatdDetector:
    def __init__(self):
        jarfile = ENV['home_dir'] / "src/satd_detector.jar"
        self.analyzer = pexpect.spawn(f'java -jar {jarfile} test', encoding='utf-8')
        self.analyzer.expect('>')

    def detect(self, diffs, file_type):
        a_SATD_comments, b_SATD_comments = self._process_by_file(diffs, file_type)
        comments = {"a_comments": a_SATD_comments, "b_comments": b_SATD_comments}
        return comments


    def _process_by_file(self, diffs, file_type):
        a_script_lines, a_line_is_diff, b_script_lines, b_line_is_diff = self._append_lines(diffs)
        a_comments = extract_commentout(a_script_lines, a_line_is_diff, file_type)
        b_comments = extract_commentout(b_script_lines, b_line_is_diff, file_type)
        a_SATD_comments = self._satd_detect(a_comments)
        b_SATD_comments = self._satd_detect(b_comments)
        return a_SATD_comments, b_SATD_comments

    def _append_lines(self, diffs):
        a_script = []
        b_script = []
        a_diff = []  # 配列[i] = i行目にコメントが存在するか
        b_diff = []  # 0行目は必ずFalseで
        for contents in diffs["content"]:
            for ab in contents.keys():  # 前のと後のやつの差分行の登録
                lines = contents[ab]
                if ab == "ab":
                    self._append(lines, a_script, a_diff, False)
                    self._append(lines, b_script, b_diff, False)
                else:
                    if ab == "a":
                        self._append(lines, a_script, a_diff, True)
                    elif ab == "b":
                        self._append(lines, b_script, b_diff, True)
                    elif ab == "common":
                        continue
                    elif ab == "skip":
                        continue
                    else:
                        print('Error', ab)
                        raise
        return a_script, a_diff, b_script, b_diff

    def _append(self, lines, script, diff, param):
        for line in lines:  # TODO:　もっとシンプルに
            diff.append(param)
            script.append(line)

    def _satd_detect(self, script_lines):
        for line in script_lines:
            self.analyzer.sendline(line['comment'].replace(">", "<"))
            self.analyzer.expect('>')
            match = re.search(r'(Not SATD|SATD)', self.analyzer.before)
            try:
                result = match.group(1)
                if result == 'SATD':
                    print("***************DETECTED************************")
                    line['include_SATD'] = True
                elif result == 'Not SATD':
                    line['include_SATD'] = False
                else:
                    raise
            except AttributeError:
                print(line)
                raise
        return script_lines


