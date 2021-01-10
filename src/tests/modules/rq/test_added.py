from unittest import TestCase

from exe import PROJECT
from modules.SATDReviewExplore import SATDReviewExplore
from modules.review.GerritController import GerritControllerViaLocal
from modules.rq.common import mark_satd
from tests.modules.rq.test_util import exe
from tests.modules.satd.stub import SatdDetectorStub
import pandas as pd


class TestAdded(TestCase):

    def test_detect_case_N001(self):
        target = 427
        df = exe(target, "openstack")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == True

    def test_detect_case_N002(self):
        target = 452
        df = exe(target, "openstack")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == False

    def test_detect_case_N003(self):# TODO: not tested yet due to error
        target = 112
        df = exe(target, "qt")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == False

    def test_detect_case_Y002(self):
        target = 190
        df = exe(target, "openstack")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == True

    def test_detect_case_Y003(self):
        target = 482
        df = exe(target, "openstack")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == True

    def test_detect_case_Y004(self):
        target = 628
        df = exe(target, "openstack")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == True

    def test_detect_case_Y005(self):
        target = 665
        df = exe(target, "openstack")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == True

    def test_detect_case_Y006(self):  # TODO: not tested yet due to time
        target = 1917
        df = exe(target, "openstack")
        assert df.at[0, "is_added_satd"] == True

    def test_detect_case_N004(self):
        target = 663
        df = exe(target, "qt")
        print(df.at[0, "is_added_satd"])
        assert df.at[0, "is_added_satd"] == False
    def test_detect_case_N005(self):
        target = 1
        df = exe(target, "qt")
