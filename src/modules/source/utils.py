import os



def get_file_type(filename):
    filename_ext = os.path.splitext(filename)
    assert len(filename_ext) == 2
    file_type = filename_ext[1].replace(".", "")
    return file_type




def diff_include_check(start, end, diff_data):  # 得たコメントの中に変更のあった行が含まれるかを判定する
    judge = False
    for check_line in range(start, end + 1):  # +1つけないと最終行見てくれない
        if diff_data[check_line]:
            judge = True
            break
    return judge
