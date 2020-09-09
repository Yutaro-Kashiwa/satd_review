from modules.satd.SatdDetector import SatdDetector


class SatdDetectorStub(SatdDetector):
    def detect_satd(self, string):
        s = [string]
        return self._satd_detect(s)
