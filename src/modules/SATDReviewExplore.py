# 異なるリビジョンの同一コメントを消す．
# やり方：resultリストに１つずつ要素を突っ込む．
# その際，resultリストの各要素見て，comment一致，ファイル名一致，SHA不一致の３条件を満たしていたら中断し，appendしない．
# 通常版と比べ，SHAを条件から取り除いている．加えて，同じものが見つかった時，last_SHAを更新している．
from concurrent.futures.thread import ThreadPoolExecutor
from json import JSONDecodeError

from modules.others.my_exceptions import KnowUnknownJsonError, QueryFileNotFoundError, DetailFileNotFoundError, \
    DiffFileNotFoundError, DiffLineFileNotFoundError
from modules.review.Review import Review
from modules.satd.SatdDetector import SatdDetector
from modules.source.satd_process_worker import process
from modules.source.utils import get_file_type


def samecheck(list, list2):  # list = そのリビジョンのコメント，list2 = その前までのリビジョンのコメント
    result = list2
    judge = True  # 同一のSATDを発見したらFalseにする．
    length = len(list)  # いらないかも
    # print("found comments = " + str(len(list)))
    for x in range(len(list)):  # そのリビジョンのコメントそれぞれについて
        for y in range(len(result)):  # その前までのリビジョンのコメントと比較する．
            # でかいデータならlen(list2)ではなくlen(result)にすべし．
            if list[x]["comment"] == result[y]["comment"] and list[x]["now_filename"] == result[y]["now_filename"]:
                # print "found same SATD"
                judge = False
                result[y]["last_SHA"] = list[x]["SHA"]  # ここ追加しました
                break
        if judge == True:
            result.append(list[x])
        else:
            judge = True
    # print("unique comments = " + str(len(result)))
    return result

class SATDReviewExplore():
    def __init__(self, gc):
        self.gc = gc

    def detect(self):
        error = {"program error": [], "know unknown problem": [], "anonymous file not found": [],
                 "query file not found": [], "detail file not found": [], "diff file not found": [], "diff line file not found": [],
                 }
        output = []
        tpe = ThreadPoolExecutor(max_workers=50)
        while self.gc.next():
                query = self.gc.get_run_info()
                tpe.submit(process, query, output, error)

        tpe.shutdown()
        return output, error




