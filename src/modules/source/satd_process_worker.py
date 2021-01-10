from json.decoder import JSONDecodeError

import pexpect

from modules.others.my_exceptions import KnowUnknownJsonError, QueryFileNotFoundError, DetailFileNotFoundError, \
    DiffLineFileNotFoundError, DiffFileNotFoundError, NotTargetSubProjectException, NoContentsException
from modules.review.GerritController import QueryBase
from modules.review.Review import Review
from modules.satd.SatdDetector import SatdDetector
from modules.source.utils import get_file_type

def process(query: QueryBase, output, error):
    try:
        print(f"#{query.review_id} started")
        revision_data = query.get_revision_data()
        review = Review(query, query.review_id, revision_data)
        results = _process_by_review(query, review)

        info = {"id": query.review_id, "results": results}
        info.update(review.get_info())
        output.append(info)
    except NotTargetSubProjectException:
        print(f"NotTargetSubProjectException@{query.review_id}")
        error["not target sub-project"].append(query.review_id)
    except NoContentsException:
        print(f"NoContentsException@{query.review_id}")
        error["no contents"].append(query.review_id)
    except KnowUnknownJsonError:
        print(f"KnowUnknownJsonError@{query.review_id}")
        error["know unknown problem"].append(query.review_id)
    except QueryFileNotFoundError:
        # print(f"QueryFileNotFound (no problem)@{query.review_id}")
        error["query file not found"].append(query.review_id)
    except DetailFileNotFoundError:
        print(f"DetailFileNotFoundError@{query.review_id}")
        error["detail file not found"].append(query.review_id)
    except DiffFileNotFoundError:
        print(f"DiffFileNotFoundError@{query.review_id}")
        error["diff file not found"].append(query.review_id)
    except DiffLineFileNotFoundError:
        print(f"DiffLineFileNotFoundError@{query.review_id}")
        error["diff line file not found"].append(query.review_id)
    except FileNotFoundError:
        print(f"FileNotFoundError@{query.review_id}")
        error["anonymous file not found"].append(query.review_id)
    except pexpect.exceptions.EOF:
        print(f"EOF@{query.review_id}")
        error["SATD detector is too busy"].append(query.review_id)#reduce workers
    except pexpect.exceptions.TIMEOUT:
        print(f"TIMEOUT@{query.review_id}")
        error["SATD detector is too busy"].append(query.review_id)#reduce workers
    except Exception as e:
        print(f"Exception@{query.review_id}:{e}")
        error["program error"].append(query.review_id)
    print(f"#{query.review_id} finish")

def _process_by_review(query, review):
    revision = 1
    out = []
    while revision <= review.total_revisions:  # 各パッチについてコメントとレビューの情報を取る
        contents = _process_by_revision(query, review, revision)
        out.append({"revision": revision, "changed_files": contents})
        revision += 1
    return out


def _process_by_revision(query, review, patch_no):  # return line:True
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
        detector = SatdDetector()
        comments = detector.detect(diffs, file_type)
        comments["filename"] = file_name
        out.append(comments)
    return out