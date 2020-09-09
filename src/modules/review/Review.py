from modules.others.configure import get_languages
from modules.others.my_exceptions import KnowUnknownJsonError
from modules.review.utils import remove_bots_message, extract_inline_comments_number


class Review:
    def __init__(self, query, review_id, revision_info, review_info):
        self.query = query
        if not "current_revision" in revision_info:
            raise KnowUnknownJsonError
        current_revision = revision_info["current_revision"]
        self.total_revisions = revision_info["revisions"][current_revision]["_number"]  # その変更のパッチ総数．
        self.review_id = review_id
        tmp = revision_info['project'].split("/")
        assert len(tmp) == 2
        self.project = tmp[0]
        self.sub_project = tmp[1]
        self.target_languages = get_languages(self.project, self.sub_project)
        self.change_id = revision_info["change_id"]
        self.status = revision_info["status"]
        self.commit_message = revision_info["subject"]
        # review_info
        # print("review_info ", review_info["messages"])
        self.comments = remove_bots_message(review_info["messages"], query.bots)
        self.total_inline_comments = extract_inline_comments_number(self.comments)
        self.total_comments = len(self.comments)  # self.total_outline_comments + self.total_inline_comments
        if "REVIEWER" in review_info["reviewers"]:
            self.total_reviewers = len(review_info["reviewers"]["REVIEWER"])
        else:
            self.total_reviewers = 0

    def get_info(self):
        out = dict()
        # リビジョン数
        out["revisions"] = self.total_revisions
        # コメント数
        out["comments"] = self.total_comments
        # インラインコメント数
        out["inline_comments"] = self.total_inline_comments
        # レビュー状態
        out["status"] = self.status
        # レビュー状態（false/true）
        out["is_accepted"] = (self.status == "MERGED")
        # url
        out["url"] = self.query.get_url()
        # コミットメッセージ
        out["commit_message"] = self.commit_message
        return out
