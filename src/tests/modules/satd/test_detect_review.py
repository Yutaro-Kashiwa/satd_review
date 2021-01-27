import glob
import os
from unittest import TestCase

from exe import load_project
from exe._1_detect import run
from tests.modules.satd.stub import SatdDetectorStub
from tests.other.important_list import deleted, added


class TestSATDDetector(TestCase):



    def test_detect_case_qt774(self):
        project = "qt"
        no = 774
        p = load_project(project)
        df, error = run.run(p, no-1, no)
        assert df.loc[0, 'is_added_satd']==False #qtdoc is not target


    def verify(self, project, no, type = 'is_added_satd', expected=True):
        p = load_project(project)
        df, error = run.run(p, no - 1, no)
        assert df.loc[0, type] == expected


    def test_detect_case_qt145762(self):
        project = "qt"
        no = 145762
        self.verify(project, no)

    def test_detect_case_qt65801(self):
        project = "qt"
        no = 65801
        self.verify(project, no)

    def test_detect_case_qt151666(self):#Exception
        project = "qt"
        no = 151666
        self.verify(project, no)

    def test_detect_case_qt189399(self):#Exception
        project = "qt"
        no = 189399
        self.verify(project, no)

    def test_detect_case_qt173416(self):
        project = "qt"
        no = 173416
        self.verify(project, no)

    def test_detect_case_qt32700(self):
        project = "qt"
        no = 32700
        self.verify(project, no)

    def test_detect_case_qt165445(self):
        project = "qt"
        no = 165445
        self.verify(project, no)

    def test_detect_case_qt38451(self):#'NoneType' object is not callable
        project = "qt"
        no = 38451
        self.verify(project, no)

    def test_detect_case_qt16042(self):#'NoneType' object is not callable
        project = "qt"
        no = 16042
        self.verify(project, no)

    def test_detect_case_qt3616(self):#Exception
        project = "qt"
        no = 3616
        self.verify(project, no)

    def test_detect_case_qt25917(self):
        project = "qt"
        no = 25917
        self.verify(project, no)

    def test_detect_case_qt143722(self):
        project = "qt"
        no = 143722
        self.verify(project, no)

    def test_detect_case_qt73047(self):
        project = "qt"
        no = 73047
        self.verify(project, no, 'is_added_satd')
    def test_detect_case_qt74049(self):
        project = "qt"
        no = 74049
        self.verify(project, no, 'is_deleted_satd')

    def test_detect_case_qt22189(self):
        project = "qt"
        no = 22189
        self.verify(project, no, 'is_added_satd')

    def test_detect_case_qt2270(self):
        project = "qt"
        no = 2270
        self.verify(project, no, 'is_deleted_satd')

    def test_detect_case_qt115(self):
        project = "qt"
        no = 115
        self.verify(project, no, 'is_deleted_satd', expected=False)

    def test_detect_case_qt16230(self):
        project = "qt"
        no = 16230
        self.verify(project, no, 'is_deleted_satd', expected=False)

    def test_detect_case_qt14546(self):
        project = "qt"
        no = 14546
        self.verify(project, no, 'is_deleted_satd', expected=False)

    def test_detect_case_qt16531(self):#detector is too busy
        project = "qt"
        no = 16531
        self.verify(project, no, 'is_deleted_satd', expected=False)


    # def test_detect_case_qt63560(self)://対象外
    #     project = "qt"
    #     no = 63560
    #     self.verify(project, no, 'is_deleted_satd')

    def test_important_deleted_list(self):
        project = "qt"
        for no in deleted[project]:
            self.verify(project, no, 'is_deleted_satd')

    def test_important_added_list(self):
        project = "qt"
        for no in added[project]:
            self.verify(project, no, 'is_added_satd')

    def test_detect_case_os570078(self):#lack of a file
        project = "openstack"
        self.verify(project, 570078, 'is_added_satd')

    def test_detect_case_os661466(self):
        project = "openstack"
        self.verify(project, 661466, 'is_deleted_satd')

    def test_detect_case_os635671(self):
        project = "openstack"
        self.verify(project, 635671, 'is_deleted_satd')

    def test_detect_case_os7131(self):
        project = "openstack"
        self.verify(project, 7131, 'is_deleted_satd')

    def test_detect_case_qt3092(self):
        project = "qt"
        self.verify(project, 3092, 'is_added_satd')

    def test_detect_case_qt221553(self):
        project = "qt"
        self.verify(project, 221553, 'is_added_satd')
