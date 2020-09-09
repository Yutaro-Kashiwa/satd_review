import subprocess
class GitController:
    def checkout(hash):
        count = 0
        while 1:
            try:
                s = subprocess.check_output("git checkout -f " + hash, shell=True, cwd='./DS/' + sub_name,
                                            stderr=subprocess.STDOUT)  # -fがないとたまに例外が出る．
                s.strip("\n")
                print
                "log = [" + s + "]"
            except subprocess.CalledProcessError as e:
                s = e.output
                s.strip("\n")
                print
                "errlog = [" + s + "]"
            if s.find("reference is not a") != -1:
                return 1
            return 0

    def file_search(h):  #
        before_hash = h + "^"
        # find ../DS/{project}って感じになりそう．
        # string = subprocess.call("pwd")
        # print string
        # コマンドが動作しない．何がおかしいんだろう？
        # script = r"find ./DS/stripe-java -name \"*.java\" -print" #エスケープなしでいける？
        # string = subprocess.call(script)
        # check_output = 返り値が標準出力になる．(他のコマンドだと０が返ってくるのでこれが必要）
        # if rev_count == 1 or rev_count == list_length: #初めと最後は全部見つける必要あり．
        if 1:
            string = subprocess.check_output(
                "git diff --name-only " + before_hash + " " + h + " --diff-filter=ACMR *." + lang, shell=True,
                cwd='./DS/' + sub_name)
        else:
            string = subprocess.check_output(
                "git diff --name-only " + before_hash + " " + h + " --diff-filter=ACMR *." + lang, shell=True,
                cwd='./DS/' + proj_name)
        # diff-filter..A=追加，C=コピー，M=変更，R=リネーム．のあったフォルダ．Dは削除．
        # でもD以外（小文字のdとするのが良さそう)
        # 先に１つ前のリビジョン，後に今のリビジョンとすること．逆だと追加，除去の判定が逆転して死ぬ．
        # print string  #for test
        return string