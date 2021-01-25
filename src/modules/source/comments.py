import re

lang_c = ["c", "h", "cc", "cpp", "cxx", "cp", "hpp", "hxx", "qml", "m", "mm", "java", "js", "frag", "vert",
          "g"]  # c言語タイプ
lang_script = ["py", "sh", "pro", "pl"]  # pythonタイプ
# 厳密にはsh,qmake(pro),plは複数行コメントアウトは存在しない
# shは一応<<任意の文字列〜任意の文字列で可能だが今は無視
lang_vb = ["vb", "vbs"]  # visualbasicタイプ(シングルクォート
lang_query = ["xq"]  # xqueryタイプ (:  :)


def get_is_multi_comment_out(lang):
    start = None
    end = None
    if lang in lang_c:  # 言語に応じて異なるメソッドでdiffであるコメントを抽出
        start = is_start_multi_comments_compiler
        end = is_end_multi_comments_compiler
    elif lang in lang_script:
        start = is_start_multi_comments_script
        end = is_end_multi_comments_script
    elif lang in lang_vb:  # visualbasic系には複数行コメントはないのでテキトーな無理文字列でごまかす
        start = is_start_multi_comments_vb
        end = is_end_multi_comments_vb
    elif lang in lang_query:  # xqueryタイプ
        start = is_start_multi_comments_query
        end = is_end_multi_comments_query
    return start, end


def get_is_single_comment_out(lang):
    start = None
    if lang in lang_c:  # 言語に応じて異なるメソッドでdiffであるコメントを抽出
        start = is_single_comment_compiler
    elif lang in lang_script:
        start = is_single_comment_script
    elif lang in lang_vb:  # visualbasic系には複数行コメントはないのでテキトーな無理文字列でごまかす
        start = is_single_comment_vb
    elif lang in lang_query:  # xqueryタイプ
        start = is_single_comment_query
    return start

def remove_exception(lang):
    exception = except_common
    if lang in lang_c:  # 言語に応じて異なるメソッドでdiffであるコメントを抽出
        exception = get_c_exeption
    return exception

def get_c_exeption(line):
    line = line.replace("://", "")  # To handle http/https/ftp
    line = line.replace("//*", "//")  # To handle http/https/ftp
    return except_common(line)

def except_common(line):
    return re.sub('".+?"', '""', line)

def check_javadoc(line, flag_in_javadoc):
    should_continue = False
    if is_start_javadoc(line):
        flag_in_javadoc = True
    if flag_in_javadoc:  # 一行の場合もあるので注意
        if is_end_javadoc(line):
            flag_in_javadoc = False
            should_continue = True
    return flag_in_javadoc, should_continue



# コメントアウトだけ取り出す
def append_info(info, line_no, comment):
    if len(info) > 0:
        info['end_line'] = line_no
        info['comment'] = info['comment'] + '<KAIGYO>' + comment
    else:
        info['start_line'] = line_no
        info['end_line'] = line_no
        info['comment'] = comment
    return info


def extract_commentout(lines, is_diffs, file_type):
    is_single_comment_out = get_is_single_comment_out(file_type)
    if is_single_comment_out is None:
        return []
    is_start_multi_comment_out, is_end_multi_comment_out = get_is_multi_comment_out(file_type)
    remove = remove_exception(file_type)
    commentout_info = []
    flag_in_multi_comment_out = False
    flag_in_javadoc = False
    merged_comment = ""
    info = {}
    flg_diff = False
    for line_no, line in enumerate(lines, 0):
        if line.endswith("=="):  # skip base64
            continue
        line = remove(line)
        # Check JAVA DOC
        if file_type == 'java':
            flag_in_javadoc, should_continue = check_javadoc(line, flag_in_javadoc)
            if should_continue:
                continue
        if not flag_in_multi_comment_out:# if the previous lines did not start comment out
            # pythonの場合，#を使いながら複数行コメントをする
            flag_in_single_comment_out, comment = is_single_comment_out(line)
            if flag_in_single_comment_out:
                info = append_info(info, line_no, comment)
                if is_diffs[line_no]:
                    flg_diff = True
                continue
            elif len(info) > 0:
                if flg_diff:
                    commentout_info.append(info)
                    flg_diff = False
                info = {}
            else:
                pass

            flag_in_multi_comment_out, comment = is_start_multi_comment_out(line)
            if flag_in_multi_comment_out:  # if this line starts comment out
                info['start_line'] = line_no
                merged_comment = line
                if is_diffs[line_no]:
                    flg_diff = True

                double_flg, double_comment = is_end_multi_comment_out(comment)
                if double_flg:#one line multiple comment out pattern
                    info['end_line'] = line_no
                    info['comment'] = double_comment
                    if flg_diff:
                        commentout_info.append(info)
                        flg_diff = False
                    info = {}
                    flag_in_multi_comment_out = False
                continue
            else:
                pass
        else:# if the previous lines have alreadly started comment out
            is_closed, comment = is_end_multi_comment_out(line)
            if is_closed:# if this line ends comment out
                merged_comment += '<KAIGYO>' + comment
                info['end_line'] = line_no
                info['comment'] = merged_comment
                if is_diffs[line_no]:#this line has changes?
                    flg_diff = True
                if flg_diff:# does this line or the previous line has changes?
                    commentout_info.append(info)
                    flg_diff = False
                info = {}
                flag_in_multi_comment_out = False
                merged_comment = ""
                continue
            else:# comment out does not finish
                merged_comment += '<KAIGYO>' + line
                if is_diffs[line_no]:#this line has changes?
                    flg_diff = True
                continue


    if len(info) > 0:  # if one line change in "a" or "b"
        if flg_diff:
            commentout_info.append(info)
    # assert not flag_in_multi_comment_out
    # assert not flag_in_javadoc
    return commentout_info

##########################################
def _extract_comment_after(symbol, line):
    pattern = rf".*?({symbol}.*)"  # ?で最左一致にしている
    comment = re.match(pattern, line)
    if comment:
        return True, comment.group(1)
    else:
        return False, None


def is_single_comment_compiler(line):
    return _extract_comment_after("//", line)


def is_single_comment_script(line):
    return _extract_comment_after("#", line)


def is_single_comment_query(line):
    return False, None  # xquery does not have single comment out


def is_single_comment_vb(line):
    return _extract_comment_after("\\'", line)


###########################################


def is_start_multi_comments_compiler(line):
    return _extract_comment_after("/\\*", line)


def is_start_multi_comments_script(line):
    return _extract_comment_after("\\'\\'\\'", line)


def is_start_multi_comments_query(line):
    return _extract_comment_after("\\(:", line)


def is_start_multi_comments_vb(line):
    return False, None


#############################################
def _extract_comment_before(symbol, line):
    pattern = rf"(.*{symbol}).*"
    comment = re.match(pattern, line)
    if comment:
        return True, comment.group(1)
    else:
        return False, None


def is_end_multi_comments_compiler(line):
    return _extract_comment_before("\\*\\/", line)


def is_end_multi_comments_script(line):
    return _extract_comment_before("\\'\\'\\'", line)


def is_end_multi_comments_query(line):
    return _extract_comment_before(":\\)", line)


def is_end_multi_comments_vb(line):
    return False, None


#####################################################
def is_start_javadoc(line):
    return _extract_comment_after("/\\*\\*", line)


def is_end_javadoc(line):
    return _extract_comment_before("\\*\\*/", line)
