from unittest import TestCase

from modules.source.comments import is_single_comment_script
from tests.modules.satd.stub import SatdDetectorStub


class TestSATDDetector(TestCase):
    def check(self, input_data, answer):
        detector = SatdDetectorStub()
        output = detector.detect_satd(input_data)
        print(output)
        assert output[0]['include_SATD'] == answer

    def test_detect_case_N001(self):
        input_data = {"comment": "# TODO: hoge"}
        answer = True
        self.check(input_data, answer)

    def test_detect_case_N002(self):
        input_data = {"comment": "# yhooo"}
        answer = False
        self.check(input_data, answer)
    # the case includes '>' that isn't allowed by detector
    def test_detect_case_N002(self):
        input_data = {"comment": "<=>?@^_`{|}~\")"}
        answer = False
        self.check(input_data, answer)


    def test_double_sharps_N001(self):
        input_data = "source code # LP Bug #755916. This information is still coming back"
        is_satd, comment = is_single_comment_script(input_data)
        assert comment == "# LP Bug #755916. This information is still coming back"