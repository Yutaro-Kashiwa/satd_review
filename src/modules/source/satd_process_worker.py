from json.decoder import JSONDecodeError

from modules.others.my_exceptions import KnowUnknownJsonError, QueryFileNotFoundError, DetailFileNotFoundError, \
    DiffLineFileNotFoundError, DiffFileNotFoundError
from modules.review.Review import Review
from modules.satd.SatdDetector import SatdDetector
from modules.source.utils import get_file_type

def process(query, output, error):
    try:
        revision_data = query.get_revision_data()
        review_data = query.get_review_data()
        review = Review(query, query.review_id, revision_data, review_data)
        results = _process_by_review(query, review)

        info = {"id": query.review_id, "results": results}
        info.update(review.get_info())
        output.append(info)
    except KnowUnknownJsonError:
        error["know unknown problem"].append(query.review_id)
    except QueryFileNotFoundError:
        error["query file not found"].append(query.review_id)
    except DetailFileNotFoundError:
        error["detail file not found"].append(query.review_id)
    except DiffFileNotFoundError:
        error["diff file not found"].append(query.review_id)
    except DiffLineFileNotFoundError:
        error["diff line file not found"].append(query.review_id)
    except FileNotFoundError:
        error["anonymous file not found"].append(query.review_id)
    except Exception:
        error["program error"].append(query.review_id)

def _process_by_review(query, review):
    revision = 1
    out = []
    detector = SatdDetector()
    while revision <= review.total_revisions:  # 各パッチについてコメントとレビューの情報を取る
        contents = _process_by_revision(query, detector, review, revision)
        out.append({"revision": revision, "changed_files": contents})
        revision += 1
    return out


def _process_by_revision(query, detector, review, patch_no):  # return line:True
    out = []
    try:  # FIXME jsonファイルがない場合(Not Found)．これはあるべき状態ではないが，データ取ってくるところができるまで一時的に
        files = query.get_diff_files(patch_no)
    except JSONDecodeError:
        return out
    for file_name in files.keys():  # 発見した各ファイルへの処理
        if file_name == "/COMMIT_MSG":
            continue
        file_type = get_file_type(file_name)
        if file_type not in review.target_languages:  # サブプロジェクトに応じて変えるべき．forで．
            continue
        diffs = query.get_diffs(patch_no, file_name)
        comments = detector.detect(diffs, file_type)
        comments["filename"] = file_name
        out.append(comments)
    return out