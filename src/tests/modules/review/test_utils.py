from unittest import TestCase

from modules.review.utils import detect_inline_comments


class TestExtractMultiCommentEnd(TestCase):


    def test_detect_case_N001(self):
        input = "Patch Set 1: (2 inline comments)\n\n"
        flg, num = detect_inline_comments(input)
        assert flg
        assert num == 2

    def test_detect_case_N002(self):
        input = "Patch Set 4: (1 inline comment)\n\n"
        flg, num = detect_inline_comments(input)
        assert flg
        assert num == 1

    def test_detect_case_N003(self):
        input = "Patch Set 1: I would prefer that you didn\u0027t merge this\n\n(2 inline comments)\n\nI realize it\u0027s WIP, just trying to keep track of your progress."
        flg, num = detect_inline_comments(input)
        assert flg
        assert num == 2

    def test_not_detect_case(self):
        input = "Patch Set 2:\n\nStarting check jobs.\nhttp://status.openstack.org/zuul/"
        flg, num = detect_inline_comments(input)
        assert flg
        assert num == 0