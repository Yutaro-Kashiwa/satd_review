import subprocess

import re

import pexpect

from exe import ENV
from modules.source.comments import extract_commentout


class SatdDetector:
    def __init__(self):
        self.jarfile = ENV['home_dir'] / "src/satd_detector.jar"
        self.MAX_BUFFER = 1024

    def init(self):
        self.analyzer = pexpect.spawn(f'java -Xms512m -Xmx8g -jar {self.jarfile} test', encoding='utf-8', timeout=30,
                                      maxread=1024 * 2, searchwindowsize=1024 * 4)
        self.analyzer.timeout = 1000
        self.analyzer.expect('>')

    def close(self):
        self.analyzer.close()

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

    def _append(self, lines, script, diff, either):
        for line in lines:  # TODO:　もっとシンプルに
            diff.append(either)
            script.append(line)

    def _satd_detect(self, script_lines):
        self.init()
        for line in script_lines:
            if line['comment'] == "/exit":
                continue
            comment = line['comment']

            lines = []
            if len(comment) >= self.MAX_BUFFER:
                split_comments = comment.split("<KAIGYO>")
                con = ""
                for s in split_comments:
                    s = s + ' '
                    if len(con + s) >= self.MAX_BUFFER:
                        lines.append(con)
                        con = ""
                    con = con + s
                lines.append(re.sub('[ 　]+', ' ', con + ' ' + s))
            else:
                lines.append(re.sub('[ 　]+', ' ', comment.replace("<KAIGYO>", " ")))
            line['include_SATD'] = False
            for ll in lines:
                is_satd = self._detect(ll)
                if is_satd:
                    line['include_SATD'] = True
                    break
        self.close()
        return script_lines

    def _detect(self, line):
        if len(line) > self.MAX_BUFFER:
            return False
        self.analyzer.sendline(line.replace(">", "<"))
        self.analyzer.expect('>')
        match = re.search(r'(Not SATD|SATD)', self.analyzer.before)
        try:
            result = match.group(1)
            if result == 'SATD':
                return True
            elif result == 'Not SATD':
                return False
            else:
                raise
        except AttributeError:
            print("line: " + line)
            raise

    # def _satd_detect(self, script_lines):
    #     self.init()
    #     for line in script_lines:
    #         if line == "/exit":
    #             continue
    #         comment = line['comment'].replace("  ", " ")
    #         lines = []
    #         if len(comment) >= 1024:
    #             split_comments = comment.split(".")
    #             con = ""
    #             for s in split_comments:
    #                 s = s + '.'
    #                 if len(con + s) >= 1024:
    #                     lines.extend(con)
    #                     con = ""
    #                 con = con + s
    #             lines.extend(con + s + '.')
    #         else:
    #             lines.extend(comment)
    #         line['include_SATD'] = False
    #         for ll in lines:
    #             is_satd = self._detect(ll)
    #             if is_satd:
    #                 line['include_SATD'] = True
    #                 break
