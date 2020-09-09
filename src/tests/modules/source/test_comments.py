from unittest import TestCase

from modules.source.comments import is_single_comment_vb, is_single_comment_compiler, is_single_comment_script, \
    is_single_comment_query, is_start_multi_comments_compiler, is_start_multi_comments_vb, \
    is_start_multi_comments_script, is_start_multi_comments_query, is_end_multi_comments_compiler, \
    is_end_multi_comments_vb, is_end_multi_comments_script, is_end_multi_comments_query


class TestExtractSingleComment(TestCase):
    def test_compilers(self):
        flg, comment = is_single_comment_compiler("hogehoge //TODO aaaa") 
        self.assertEqual(flg, True)
        self.assertEqual(comment, '//TODO aaaa')
        
    def test_vb(self):
        flg, comment = is_single_comment_vb("hogehoge 'TODO aaaa") 
        self.assertEqual(flg, True)
        self.assertEqual(comment, "'TODO aaaa")

    def test_script(self):
        flg, comment = is_single_comment_script("hogehoge #TODO aaaa")
        self.assertEqual(flg, True)
        self.assertEqual(comment, '#TODO aaaa')

    def test_query(self):
        flg, comment = is_single_comment_query("hogehoge 'TODO aaaa") 
        self.assertEqual(flg, False)
        self.assertEqual(comment, None)


class TestExtractMultiCommentStart(TestCase):
    def test_compilers(self):
        flg, comment = is_start_multi_comments_compiler("hogehoge /*TODO aaaa")
        self.assertEqual(flg, True)
        self.assertEqual(comment, '/*TODO aaaa')

    def test_vb(self):
        flg, comment = is_start_multi_comments_vb("hogehoge /*TODO aaaa")
        self.assertEqual(flg, False)
        self.assertEqual(comment, None)

    def test_script(self):
        flg, comment = is_start_multi_comments_script("hogehoge '''TODO aaaa")#
        self.assertEqual(flg, True)
        self.assertEqual(comment, "'''TODO aaaa")

    def test_query(self):
        flg, comment = is_start_multi_comments_query("hogehoge (:TODO aaaa")
        self.assertEqual(flg, True)
        self.assertEqual(comment, "(:TODO aaaa")


class TestExtractMultiCommentEnd(TestCase):
    def test_compilers(self):
        flg, comment = is_end_multi_comments_compiler("hogehoge TODO aaaa*/ aaa")
        self.assertEqual(flg, True)
        self.assertEqual(comment, 'hogehoge TODO aaaa*/')

    def test_vb(self):
        flg, comment = is_end_multi_comments_vb("hogehoge /*TODO aaaa")
        self.assertEqual(flg, False)
        self.assertEqual(comment, None)

    def test_script(self):
        flg, comment = is_end_multi_comments_script("hogehoge TODO aaaa''' aaa")
        self.assertEqual(flg, True)
        self.assertEqual(comment, "hogehoge TODO aaaa'''")

    def test_query(self):
        flg, comment = is_end_multi_comments_query("hogehoge TODO aaaa:) aaa")
        self.assertEqual(flg, True)
        self.assertEqual(comment, "hogehoge TODO aaaa:)")