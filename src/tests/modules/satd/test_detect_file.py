import glob
import os
from unittest import TestCase

from exe import load_project
from exe._1_detect import run
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


    def test_detect_case_N004(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/140001-150000/145601-145800/145762/5_src%2Fnetwork%2Faccess%2Fqhttp2protocolhandler.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N005(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/60001-70000/65801-66000/65801/6_src%2Fquick%2Fitems%2Fqquickitem.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N006(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/150001-160000/151601-151800/151666/3_src%2Fqdoc%2Fqmlcodeparser.h.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N007(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/150001-160000/151601-151800/151666/3_src%2Fqdoc%2Fmain.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N008(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/1-10000/2201-2400/2270/1_examples%2Fdeclarative%2Fparticles%2Fcustom%2Fshader.qml.json"
        print(self.get_results(file_name, "qml"))

    def test_detect_case_N009(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/1-10000/1-200/155/1_tests%2Fauto%2Fscenegraph%2Ftst_scenegraph.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N010(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/10001-20000/16201-16400/16230/1_tests%2Fauto%2Fwidgets%2Fitemviews%2Fqtreewidgetitemiterator%2Ftst_qtreewidgetitemiterator.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N011(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/30001-40000/30401-30600/30524/10_src%2Fquick%2Fdoc%2Fsnippets%2Fqml%2Fusecases%2Flayouts.qml.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N012(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/openstack/570001-580000/570001-570200/570078/16_nova%2Ftests%2Ffunctional%2Ftest_servers.py.json"
        print(self.get_results(file_name, "py"))

    def test_detect_case_N013(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/openstack/630001-640000/635601-635800/635671/4_neutron%2Fdb%2Fapi.py.json"
        print(self.get_results(file_name, "py"))

    def test_detect_case_N014(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/1-10000/3001-3200/3092/7_tests%2Fauto%2Fv8%2Fv8test.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N015(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/1-10000/3001-3200/3092/11_tools%2Fconfigure%2Fconfigureapp.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N016(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/10001-20000/13801-14000/13933/1_src%2Fcorelib%2Fitemmodels%2Fqidentityproxymodel.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N017(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/150001-160000/151601-151800/151678/8_src%2F3rdparty%2Fangle%2Fsrc%2Fcompiler%2Ftranslator%2FExtensionBehavior.h.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N018(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/200001-210000/200401-200600/200530/10_src%2F3rdparty%2Fmapboxgl%2Fboost%2F1.62.0%2Finclude%2Fboost%2Fconfig%2Fstdlib%2Froguewave.hpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N019(self):
        file_name = "/Users/yutarokashiwa/Desktop/rowdata/review/qt/220001-230000/221601-221800/221672/2_examples%2Fwidgets%2Fwidgets%2Felidedlabel%2Ftestwidget.cpp.json"
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N020(self):
        file_name = ""
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N021(self):
        file_name = ""
        print(self.get_results(file_name, "cpp"))

    def test_detect_case_N022(self):
        file_name = ""
        print(self.get_results(file_name, "cpp"))