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




class SATDReviewExplore():
    def __init__(self, gc, workers=10):
        self.gc = gc
        self.workers = workers

    def detect(self):
        error = {"not target sub-project": [], "program error": [], "know unknown problem": [], "anonymous file not found": [],
                 "query file not found": [], "detail file not found": [], "diff file not found": [],
                 "SATD detector is too busy": [], "internal server error in review system": [], "no contents": [], "self-review": [], "Please Rerun":[]}
        output = []
        tpe = ThreadPoolExecutor(max_workers=self.workers)
        while self.gc.next():
            query = self.gc.get_run_info()
            tpe.submit(process, query, output, error)

        tpe.shutdown()
        return output, error




