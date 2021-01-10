from chardet import detect

from modules.others.configure import read_json
from modules.review.GerritController import QueryBase
from modules.satd.SatdDetector import SatdDetector
from modules.source.utils import get_file_type


class SatdDetectorStub(SatdDetector):
    def detect_satd(self, string):
        s = [string]
        return self._satd_detect(s)

    def detect_satd_in_file(self, file_name, ext="py"):
        diffs = read_json(file_name)
        comments = self.detect(diffs, ext)
        return comments
