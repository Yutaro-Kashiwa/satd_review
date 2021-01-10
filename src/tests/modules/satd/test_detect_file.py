import glob
import os
from unittest import TestCase

from tests.modules.satd.stub import SatdDetectorStub


class TestSATDDetector(TestCase):
    def check(self, input_data, answer):
        output = self.get_results(input_data, "js")
        if answer:
            assert output[0]['include_SATD'] == answer
        else:
            assert output['a_comments'] == []
            assert output['b_comments'] == []

    def get_results(self, input_data, ext):
        detector = SatdDetectorStub()
        output = detector.detect_satd_in_file(input_data, ext)
        detector.close()
        return output

    def get_files(self, dr):
        files = glob.glob(dr)
        return files

    def test_detect_case_N001(self):
        files = self.get_files(f"{os.getcwd()}/inputs/qt/79973/?_*")
        for f in files:
            print(self.get_results(f, "js"))

    def test_detect_case_N002(self):
        start = 263001
        stop = 263200
        dr_name = f"/Users/yutarokashiwa/Desktop/rowdata/review/qt/260001-270000/{start}-{stop}/"
        for i in range(start, stop):
            files = self.get_files(f"{dr_name}/{i}/?_*")
            for f in files:
                print(self.get_results(f, "js"))

    def test_detect_case_N003(self):
        start = 72807
        stop = 72810
        dr_name = f"/Users/yutarokashiwa/Desktop/rowdata/review/qt/70001-80000/72801-73000"
        for i in range(start, stop):
            files = self.get_files(f"{dr_name}/{i}/?_*")
            for f in files:
                print(f)
                print(self.get_results(f, "js"))
