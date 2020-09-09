import math
from json import JSONDecodeError

import backoff
import requests
from pygerrit2 import GerritRestAPI, HTTPBasicAuth, Anonymous

from exe import ENV
from modules.others.configure import read_json
from modules.others.my_exceptions import DetailFileNotFoundError, QueryFileNotFoundError, DiffFileNotFoundError, \
    DiffLineFileNotFoundError
from modules.others.url import url_encode
from modules.review.GerritDao import GerritDao


class GerritController:
    project = None
    current_review_id = 0
    max_review_id = 0
    min_review_id = 1

    def __init__(self, project, max_no=None):
        self.project = project
        if max_no is None:
            self.max_review_id = int(project['last_review_no'])
        else:
            self.max_review_id = max_no

    def next(self):
        self.current_review_id += 1
        if (self.current_review_id <= self.max_review_id):
            return True
        return False

    def get_run_info(self):
        return self._get_run_info()

    def set_target(self, no):
        self.current_review_id = no-1


class QueryBase:
    def __init__(self, project, current_review_id):
        self.url = project["url"]
        self.review_id = current_review_id
        self.name = project["name"]
        self.bots = project["bots"]

    def get_review_data(self):
        return self._get_detail()

    def get_revision_data(self):
        return self._get_query()

    def get_diff_files(self, revision_no):
        return self._get_diff_files(revision_no)

    def get_diffs(self, revision_no, filename):
        return self._get_diffs(revision_no, filename)

    def get_url(self):
        return f'https://{self.url}/#/c/{self.review_id}'


class GerritControllerViaWeb(GerritController):
    def __init__(self, project, max_no):
        super(GerritControllerViaWeb, self).__init__(project, max_no)
        self.rest = GerritRestAPI(url=f'https://{self.project["url"]}', auth=Anonymous())

    @backoff.on_exception(backoff.expo, requests.exceptions.ConnectionError, max_time=1000000)
    def _get(self):
        # TODO: データ取得(q=no)
        changes = self.rest.get(
            "changes/?q=is:open&q=is:close&q=all&o=DETAILED_ACCOUNTS&o=ALL_REVISIONS&o=ALL_COMMITS&o=ALL_FILES&o=MESSAGES",
            headers={'Content-Type': 'application/json'})
        return changes
        pass

    def _get_run_info(self):
        return QueryViaWeb(self.project, self.current_review_id)


class QueryViaWeb(QueryBase):
    def __init__(self, project, current_review_id):
        super(QueryViaWeb, self).__init__(project, current_review_id)

    def _get_detail(self):
        changes = self.db.get(self.review_id + "_detail")
        return changes
    # def _get_file(self):
    #     print("now_file = " + key)
    #     print("files:" + str(key_count) + "/" + str(len(file_dic) - 1))
    #     url_key = url_encode(key)
    #     script = 'curl "https://' + address + '/changes/' + str(number) + '/revisions/' + str(
    #         patch) + '/files/' + url_key + '/diff"'
    #     input = api_get(script)  # APIデータ取得
    #     if input.startswith("<!DOCTYPE HTML PUBLIC") == True:  # api_getが異常終了した時に使う
    #         skip_flag = True
    #         print("skipped")
    #         error_ids.append(number)
    #         temp_dict = {"error_ids": error_ids}
    #         with open(t_path, 'w') as e:
    #             json.dump(temp_dict, e)
    #     # ここから差分行の情報を取る必要がある．
    #     path2 = dir_calc(proj_name, number) + str(patch) + '_' + url_key + '.json'  # 仮．本番までには必ずどこかへしっかり保存せよ
    #     dic = write_read(input, path2)  # 変数dicにdiffデータの辞書を読み込み


class GerritControllerViaDB(GerritController):
    def __init__(self, project, max_no):
        super(GerritControllerViaDB, self).__init__(project, max_no)
        self.db = GerritDao(project)

    def _get_run_info(self):
        return QueryViaDB(self.project, self.current_review_id)


class QueryViaDB(QueryBase):
    def __init__(self, project, current_review_id):
        super(QueryViaDB, self).__init__(project, current_review_id)

    def _get_detail(self):
        changes = self.db.get(self.current_review_id + "_detail")
        return changes


import json


class GerritControllerViaLocal(GerritController):
    def __init__(self, project, max_no=None):
        super(GerritControllerViaLocal, self).__init__(project, max_no)
        self.data_dir = ENV['data_dir']

    def _get_run_info(self):
        return QueryViaLocal(self.project, self.current_review_id, self.data_dir)


class QueryViaLocal(QueryBase):
    detail_file = "detail.json"
    query_file = "query.json"
    diff_files = "diff_files_[NO].json"
    diff_lines = "[NO]_[FILE_NAME].json"

    def __init__(self, project, current_review_id, data_dir):
        super(QueryViaLocal, self).__init__(project, current_review_id)
        self.data_dir = data_dir
        self.path = self._dir_calc(self.name, self.review_id)

    def _get_query(self):  # raise FileNotFoundException
        # ファイル検索
        try:
            js = read_json(self.path + self.query_file)[0]
            return js
        except FileNotFoundError:
            raise QueryFileNotFoundError

    def _get_detail(self):
        # ファイル検索
        path = self._dir_calc(self.name, self.review_id)
        try:
            js = read_json(path + self.detail_file)
            return js
        except FileNotFoundError:
            raise DetailFileNotFoundError

    def _get_diff_files(self, patch_no):
        # ファイル検索
        dirname = self._dir_calc(self.name, self.review_id)
        file = self.diff_files.replace("[NO]", str(patch_no))
        try:
            js = read_json(dirname + file)
            return js
        except FileNotFoundError:
            raise DiffFileNotFoundError

    def _get_diffs(self, patch_no, filename):
        # ファイル検索
        dirname = self._dir_calc(self.name, self.review_id)
        file = self.diff_lines.replace("[NO]", str(patch_no)).replace("[FILE_NAME]", url_encode(filename))
        try:
            js = read_json(dirname + file)
            return js
        except FileNotFoundError:
            raise DiffLineFileNotFoundError

    def _dir_calc(self, proj, i):
        i = int(i)
        ceil1 = int(math.ceil(i / 10000.0))  # math.ceil() ..切り上げ
        ceil2 = int(math.ceil(i / 200.0))
        a = (ceil1 - 1) * 10000 + 1
        b = (ceil1) * 10000
        c = (ceil2 - 1) * 200 + 1
        d = (ceil2) * 200
        dirname = self.data_dir + "review/" + proj + '/' + str(a) + '-' + str(b) + '/' + str(c) + '-' + str(
            d) + '/' + str(i) + '/'
        return dirname
