# coding: UTF-8

import os
import commands
import sys
import re #正規表現用
import json
import codecs
import numpy #新しいAWSで動かす場合はinstall必須
from time import sleep
import subprocess
import multiprocessing
import math
import urlparse

#APIデータをダウンロードしない場合はこっちで実行する．
#全て辞書の辞書({{}})形式に変更．
#ラストパッチ以外は意味ないけどラストパッチはこうしといたほうがRQ5でスムーズにperlの方と連携できる
#APIダウンロードする版はここからcomment_get,comment_get2, diff_include_checkを持ってきて上書きすること．

#AWSで動かす時の注意
#javaインストールしないとdetectorが動かない

#python2
#shからの呼び出し方：「python ~~.py openstack nova 0」 という具合．
#タイミング：RQ0.pyで(sub).jsonを取った後
#1.dictから対応ファイルを開く．
#2.それぞれのナンバーに対してAPIでコメントをとる．
#3.APIで取った情報に対してBotの名前でないか＋本文が自動コメントでないかを判断．
#  大丈夫なら名前をリストに追加する
#4.全部取り終わった後，set()して人数が１以下ならセルフレビューとする

bot_list = ['Jenkins', 'Zuul', 'Qt Sanity Bot', 'Qt Continuous Integration System']

#他にもCIで終わるものもbotとして扱うようにしましょう

#============================================================================
# SATDgetより引用
#============================================================================

def file_search(): #このままでは使えない
    #find ../DS/{project}って感じになりそう．
    #string = subprocess.call("pwd")
    #print string
    #コマンドが動作しない．何がおかしいんだろう？
    #script = r"find ./DS/stripe-java -name \"*.java\" -print" #エスケープなしでいける？
    #string = subprocess.call(script)
    #check_output = 返り値が標準出力になる．(他のコマンドだと０が返ってくるのでこれが必要）
    if rev_count == 1 or rev_count == list_length: #初めと最後は全部見つける必要あり．
        string = subprocess.check_output("find ./DS/" + proj_name + " -name *." + lang + " -print",  shell=True)
    else:
        string = subprocess.check_output("git diff --name-only " + before_hash + " " + h +  " --diff-filter=ACMR *." + lang,  shell=True, cwd= './DS/' + proj_name )
    #diff-filter..A=追加，C=コピー，M=変更，R=リネーム．のあったフォルダ．Dは削除．
    #でもD以外（小文字のdとするのが良さそう)
    #先に１つ前のリビジョン，後に今のリビジョンとすること．逆だと追加，除去の判定が逆転して死ぬ．
    #print string  #for test
    return string


def diff_include_check(start, end, diff_data): #得たコメントの中に変更のあった行が含まれるかを判定する
    judge = False
    for check_line in range(start, end+1): #+1つけないと最終行見てくれない
        if diff_data[check_line] == True:
            judge = True
            break
    return judge

#/*~~*/, /*, */, //, 複数行コメント中の５パターンに反応してコメントを得る
def comment_get(url, hash, script, diff_data, com_start, com_end, com_solo):
    #第１引数＝スクリプト内容，第２引数＝各行がdiff箇所であるかの情報，
    #第３引数＝コメント開始文字(/*とか)，第４引数＝コメント終了文字(*/とか),
    #第５引数＝単行コメント文字(//とか)
    st = com_start # /*とかのこと
    en = com_end   # */とかのこと
    sl = com_solo  # //とかのこと．ちなみにネーミングはsololineの略．
    print "script_len+1 = " + str(len(script)) + ", diff_data_len = " + str(len(diff_data))
    after_diff = False #i-1行が差分行だった時にTrue
    is_diff = False #i行目がdiff箇所に該当するか否かを入力する．
    comments = "" #複数行まとめた文字列
    temp_str = "" #一時保存用文字列
    result = [] #コメントを格納する
    multi_line = False #/*が含まれたら*/が来るまでTrueにしておく
    after_solo = False #１行コメント(//系)の直後ならTrueにする．単行コメントが連続するなら文字列をつなぐ．
    javadoc = False #javadocの文法である疑いがあるならtrue.その場合@もあればyieldを行わない．
    now_line = 1
    #core_line = 0 #そのコメントのうち，差分行に該当する行を示す．複数行あるなら一番最初の行を利用する． 未使用
    start_line = 0
    now_filename = url #チェックアウトに合わせて変えていくファイル名 .DS/proj_nameまでを消したもの
    #print "pass:" + url
    now_filename = now_filename.replace('./DS/' + proj_name + '/', '', 1)
    #print "now_filename:" + now_filename
    #ファイル開閉処理が入ってないやん．
    try:
        for line in script:
            #line = f.readline() #入力がリスト形式なのでここ変更すべき
            #while line: #ここhttps://除外をやっておく？
                after_diff = is_diff
                is_diff = diff_data[now_line] #todo:out of rangeになる
                #http://関連の対策はpythonでは不要
                if (re.search(re.escape(r"http://"), line) or re.search(re.escape(r"https://"), line)) and multi_line == False: #0. http://の//が引っかかるので対策
                    if after_solo == True: #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                    after_solo = False
                    now_line += 1 #continue前に次の行への処理は必須
                    #line = f.readline()
                    continue
                elif re.search(re.escape(st), line) and re.search(re.escape(en), line) and multi_line == False : #1. /* 〜〜〜 */
                    if after_solo == True: #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                    comments = line[line.find(st):line.index(en) + len(en)]
                    if diff_include_check(now_line, now_line, diff_data): #その行が差分行なら
                        result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":now_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename})
                    after_solo = False
                elif re.search(re.escape(st), line): #2. /*
                    if after_solo == True : #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                    after_solo = False
                    multi_line = True
                    comments = line[line.find(st):]
                    if re.match(re.escape(st), comments):
                        javadoc = True
                    start_line = now_line
                elif re.search(re.escape(en), line) and multi_line == True : #3. */ bool=trueの条件も追加
                    comments += line #[0:line.index(en)] 全部読んでいいよね
                    multi_line = False
                    after_solo = False
                    if javadoc == False or now_line - start_line <= 1 or re.search(re.escape(r"TODO"), comments) or re.search(re.escape(r"XXX"), comments) or re.search(re.escape(r"FIXME"), comments):
                        #javadocでない，2行以下，もしくはTODO,FIXME,XXXのいずれかの語を含むなら
                        if diff_include_check(start_line, now_line, diff_data): #start~endで差分行が含まれていれば
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename})
                    javadoc == False
                elif re.search(re.escape(sl), line) and multi_line == False: #4. //,かつ/*~*/の中でない
                    temp_str = line[line.find(sl):] #
                    if after_solo == True: #前の行も//なら文字列結合
                        comments += ' ' + temp_str
                    else:
                        comments = temp_str
                        start_line = now_line
                        after_solo = True
                elif multi_line == True: #5.複数行コメントの途中
                    comments += line
                    if not re.search(re.escape(r"*"), line):
                        javadoc = False #javadocは行ごとに*が入ってる．
                else: #その他
                    if after_solo == True: #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                        after_solo = False
                    else:
                        after_solo = False
                now_line += 1
                #line = f.readline()
    except IOError:
        print "IOError occured"
    return result
#list2 = [list[0] for x in liar]

#return list #返り値はコメント，開始行，終了行の３要素を持ったリストのリスト


#pythonのように複数行コメントの開始文字と終了文字が同じ場合はこっちで対処する．
#def comment_get2(url, hash):
def comment_get2(url, hash, script, diff_data):
    print "script_len+1 = " + str(len(script)) + ", diff_data_len = " + str(len(diff_data))
    after_diff = False
    is_diff = False #i行目がdiff箇所に該当するか否かを入力する．
    diff_flag = False #変更のある行が含まれてたらTrue
    comments = "" #複数行まとめた文字列
    temp_str = "" #一時保存用文字列
    result = []
    multi_line = False #複数行コメント中の間True
    after_solo = False #１行コメント(//系)の直後ならTrueにする．単行コメントが連続するなら文字列をつなぐ．
    javadoc = False #javadocの文法である疑いがあるならtrue.その場合@もあればyieldを行わない．
    now_line = 1
    start_line = 0
    intro_id = ""
    now_filename = ""
    now_filename = url #チェックアウトに合わせて変えていくファイル名 .DS/proj_nameまでを消したもの
    #print "pass:" + url
    now_filename = now_filename.replace('./DS/' + proj_name + '/', '', 1)
    #print "now_filename:" + now_filename
    #ファイル開閉処理が入ってないやん．
    try:
        for line in script:
            #line = f.readline() #入力がリスト形式なのでここ変更すべき
            #while line: #ここhttps://除外をやっておく？
                after_diff = is_diff
                is_diff = diff_data[now_line] #todo:out of rangeになる
                if re.search(re.escape(r"'''"), line) and line.count("'''") >= 2 and multi_line == False : #1. /* 〜〜〜 */
                    if after_solo == True: #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                    comments = line[line.find("'''"):-1]
                    if diff_include_check(now_line, now_line, diff_data):
                        result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":now_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename})
                    after_solo = False
                elif re.search(re.escape(r"'''"), line) and line.count("'''") == 1 and multi_line == False: #2. /*
                    if after_solo == True: #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                    after_solo = False
                    multi_line = True
                    comments = line[line.find("'''"):]
                    if re.match(re.escape(r"'''"), comments):
                        javadoc = True
                    start_line = now_line
                elif re.search(re.escape(r"'''"), line) and multi_line == True : #3. */ bool=trueの条件も追加
                    comments += line[0:line.index("'''")+2]
                    multi_line = False
                    after_solo = False
                    if 1: #javadocの心配はないので
                        #javadocでない，もしくはTODO,FIXME,XXXのいずれかの語を含むなら
                        if diff_include_check(start_line, now_line, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename})
                    javadoc == False
                elif re.search(re.escape(r"#"), line) and multi_line == False and is_diff == True: #4. //
                    temp_str = line[line.find("#"):] #改行文字は除外しない index -> find
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    if after_solo == True and is_diff == True:
                        comments += ' ' + temp_str
                    else:
                        comments = temp_str
                        start_line = now_line
                        after_solo = True
                elif multi_line == True: #複数行コメント中
                    comments += line
                    if not re.search(re.escape(r"*"), line):
                        javadoc = False #javadocは行ごとに*が入ってる．
                else:
                    if after_solo == True: #単行コメントの直後の場合の処理
                        if diff_include_check(start_line, now_line - 1, diff_data):
                            result.append({"proj_name":sub_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename})
                        after_solo = False
                    else:
                        after_solo = False
                now_line += 1
                #line = f.readline()
    except IOError:
        print "IOError occured"
    return result
#list2 = [list[0] for x in liar]

#return list #返り値はコメント，開始行，終了行の３要素を持ったリストのリスト



def detect(commentList):
    SATDComments = 0
    result = []
    temp_list = [] #value個ずつ読むときに使う．
    string = "" #detectorへの入力文字列
    id = 0
    id2 = 0
    value = 300 #１度に同時にでDetectorに処理してもらうコメント数．適宜増減させよう．
    p = os.getcwd() #SATDgetのディレクトリが出てきます
    print p
    det = p + "/srca/satd_detector.jar" #detectorのフルパス

    print commentList
    comlistlen = len(commentList) # commentListの長さ
    print "Detecting SATD..."
    for comment in commentList:

        #ここへ＊の消去処理を加えるべきか？
        n_delete = comment["comment"] #\n_delete.つまり改行消した版の文字列をここへ突っ込む．
        n_delete = n_delete.replace('\r\n', ' ') #\rのreplaceも入れるべきか？
        n_delete = n_delete.replace('\n', ' ') #\rのreplaceも入れるべきか？
        n_delete = n_delete.replace('\\n', ' ')
        commentList[id]["comment"] = n_delete ###リザルト修正用に[comment]をつける

        #ここから大改造．
        temp_list.append(comment)
        #string += n_delete + "\n"
        string += n_delete.encode("utf-8") + "\n" #エラー対策

        if (id + 1) % value == 0 or comlistlen - id == 1: #100回読んだor commentListが最後なら実行
            satd_detector = subprocess.Popen("java -jar " + det + " test", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) # 最後の「,encoding='utf-8'」」はエラーが出たので省略．

            #string = string.encode("utf-8") #190620:一時停止中
            (stdout, stderr) = satd_detector.communicate(string) #ここが入力箇所．処理が遅い（約３秒）
            #print n_delete
            #Open a process with the SATD Detector tool to test the current comment text
            #print "STDOUT:" + stdout #必要に応じて使用する．
            strlist = [] #detectorの出力を行単位で入れる変数
            strlist = stdout.splitlines()
            list_len = len(temp_list) #要素が１００ない場合に使う．
            print "strlist:" + str(len(temp_list)) + " out_line:" + str(len(strlist)) + " id:" + str(id)
            #print "comment::" + n_delete
            #comment.commentTextをcomment["comment"]にすればいけるか？
            #そしてSATDならもう１つのリスト変数に移す動作を行う，と言った感じになるか．
            #print "..."
            for i in range(0,value): #0~99.ただし１００個入ってない場合の処理も必要．
                if i != 299 and i >= list_len:
                    print "list end at:" + str(i)
                    break
                #if stdout == '>SATD\n>': #
                elif "Not SATD" in strlist[i]:
                    pass
                elif "SATD" in strlist[i]:
                    result.append(temp_list[i])
                    SATDComments = SATDComments + 1
                else:
                    print "WHY????"
                id2 += 1
            temp_list = [] #１００個ごとに持ってきてた情報の消去．
            string = ""
            print "SATD found = " + str(SATDComments)
        else: #value回の節目以外はパス．
            pass
        id += 1 # commentごとのforループここまで

    return result

#異なるリビジョンの同一コメントを消す．
#やり方：resultリストに１つずつ要素を突っ込む．
#その際，resultリストの各要素見て，comment一致，ファイル名一致，SHA不一致の３条件を満たしていたら中断し，appendしない．
#通常版と比べ，SHAを条件から取り除いている．加えて，同じものが見つかった時，last_SHAを更新している．
def samecheck(list, list2): #list = そのリビジョンのコメント，list2 = その前までのリビジョンのコメント
    result = list2
    judge = True #同一のSATDを発見したらFalseにする．
    length = len(list) #いらないかも
    print "found comments = " + str(len(list))
    for x in range(len(list)): #そのリビジョンのコメントそれぞれについて
        #print x
        for y in range(len(result)): #その前までのリビジョンのコメントと比較する．
            #でかいデータならlen(list2)ではなくlen(result)にすべし．
            if list[x]["comment"] == result[y]["comment"] and list[x]["now_filename"] == result[y]["now_filename"]:
                #print "found same SATD"
                judge = False
                result[y]["last_SHA"] = list[x]["SHA"] #ここ追加しました
                break
        if judge == True:
            result.append(list[x])
        else:
            judge = True
    print "unique comments = " + str(len(result))
    return result


#============================================================================
# original
#============================================================================




def dir_calc(proj, id): #パッチIDに応じて保存先を計算する．最後はスラッシュ付き．
    id = int(id)
    ceil1 = int(math.ceil(id/10000.0)) #math.ceil() ..切り上げ
    ceil2 = int(math.ceil(id/200.0))
    a = (ceil1 - 1) * 10000 +1
    b = (ceil1) * 10000
    c = (ceil2 - 1) * 200 +1
    d = (ceil2) * 200
    #print id
    #print ceil1
    #print ceil2
    #print a
    #print b
    #print c
    #print d
    string = './result/' + proj_name + '/' + str(a) + '-' + str(b) + '/' + str(c) + '-' + str(d) + '/' + str(id) + '/'
    return string

def api_get(script): #引数を実行し，初めの)]}'を抜いた文字列を返します．
    false_count = 0
    while 1:
        if false_count >= 100:
            break
        try:
            input = subprocess.check_output(script, shell=True, cwd='./')
        except subprocess.CalledProcessError:
            print "retry"
            false_count += 1
            continue
        #inputから")]}'"を除外する．
        input = input.replace(")]}'\n", "", 1)
        if input.startswith("<!DOCTYPE HTML PUBLIC") == False:
            break
        print "retry"
        false_count += 1
    return input

def write_read(input, path): #指定パスに書き込みを行い，さらに読み込んで辞書を返り値に取る
    #with open(path, 'w') as f:
    #    f.write(input)
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    return dic

def url_encode(string): #urlエンコード．スラッシュを%2Fに変えます．
    string = string.replace("/", "%2F")
    string = string.replace("#", "%23")
    string = string.replace(" ", "%20")
    return string

def url_decode(string): #urlデコード．%2Fをスラッシュに変えます．
    string = string.replace("%2F", "/")
    string = string.replace("%23", "#")
    string = string.replace("%20", " ")
    return string

#保存形式は？
#レビューのプロジェクト情報.. リストでプロジェクト名を保存させるのはメモリオーバーが考えられるから賢明でないと思う．
#
#openstackのgerritname .. review.opendev.org
#qt .. codereview.qt-project.org


#必要ディレクトリの準備
now_end = 673199 #qt=263350


proj_name = "openstack" #ただの初期値
sub_name = "nova"
lang = "py"

if len(sys.argv) >= 4: #プログラム名の後に引数があるなら(argvはプログラム名も数に含めている)
    argvs = sys.argv
    proj_name = argvs[1]
    sub_name = argvs[2]
    temp_start = 0
    end = 999999
    ignore = argvs[3] #引数に値が存在すれば，その分だけすでに終わってることにする
    if len(sys.argv) >= 5:
        end = argvs[4]
        ignore = int(ignore) #始点のレビューNO
        end = int(end) #終点のレビューNO
        temp_start = ignore
        temp_start = int(temp_start)
else:
    raise Error

#number = ignore #number..現在見ているレビューidのこと．


if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
    now_end = 673199 #qt=263350
if proj_name == "qt":
    address = "codereview.qt-project.org"
    now_end = 263350


#number = int(number) #文字列ー＞数値

with open('./dict/' + sub_name + '.json', 'r') as g: #
    json_dic = json.load(g)

list_count = 0 #進捗表示用変数
error_ids = [] #checkoutに失敗したIDを格納する．

'''
if ignore >= 1: #途中から始める時の処理
    path = './dict/temp_RQ0_'+ sub_name +'_' + str(ignore) + '-' + str(end) + '.json'
    if os.path.isfile(path):
        with open(path, 'r') as h:
            temp_dict = json.load(h)
        error_ids = temp_dict["error_ids"]
    else:
        error_ids = []
'''




#0.まずAPIでどんなコマンドを打てばいいのか考えましょう
#1.dictから対応ファイルを開く．
#2.それぞれのナンバーに対してAPIでコメントをとる．
#3.APIで取った情報に対してBotの名前でないか＋本文が自動コメントでないかを判断．
#  大丈夫なら名前をリストに追加する
#4.全部取り終わった後，set()して人数が１以下ならセルフレビューとする

error_signal = False #何度アクセスしてもエラーしか出ないやつの対策
self_list = []
#number...レビューナンバー
for number in json_dic[proj_name + "/" + sub_name]:
    list_count += 1
    if int(number) < int(temp_start): #途中から始めたいとき用
        continue
    if int(number) > int(end): #
        break
    skip_flag = False
    patch_skip = False
    lang_flag = False #言語が対象かどうかチェックするフラグ
    error_signal = False
    print "\n"
    print "now number = " + str(number)
    print "now:" + str(list_count) +"/"+ str(len(json_dic[proj_name + "/" + sub_name]))
    #ここからメッセージログを取る操作．
    patch = 1
    script = 'curl "https://'+ address +'/changes/' + str(number) + '/detail"' #messagesはopenstack側のAPIには存在しないから使い物にならないというトラップがある
    #print script

    path = dir_calc(proj_name, number) + 'detail.json' #保存先のpath
    input = api_get(script)
    with open(path, 'w') as f:
        f.write(input)
    
    try:
        with open(path, 'r') as h:
            #ここからjson->辞書形式で当該ファイルを読み込み
            dic = json.load(h)
    except ValueError:
        print "Error!! data has deleted."
        continue
    #if isinstance(dic, dict): #たまにリストで囲まれてないことがあるので補正
    #    dic = [dic]
    name_list = []
    for elem in dic["messages"]:
        try:
            name = elem["author"]["name"]
        except KeyError: #gerrit自身が送る，マージ失敗などのログの場合はauthorがないので例外が必要．
             continue
        #ここでBotの名前でないか判別
        is_bot = False
        for bot_name in bot_list:
            if name == bot_name:
                is_bot = True
                break
        if is_bot == True or name.endswith("CI") or name.endswith("ci") or name.endswith("Bot"):
            #該当時は何もしない
            continue
        
        message = elem["message"]
        if message.startswith("added to "):
            continue
        #ここで無意味なメッセージを判別(added to REVIEWERから始まるものは自動扱い)
        #date = elem["date"] #これは多分今いらないよね？RQ2くらいで使うやつ．
        name_list.append(name)
        
        
    name_list = list(set(name_list))
    
    #ここまで作った
    if len(name_list) <= 1:
        self_list.append(number)
        

#全部とったらself_listをdataディレクトリへ保存する
json_list = {"self_review":self_list}
path = './data/self_review_' + sub_name + '.json'

with open(path, 'w') as g:
    json.dump(json_list, g, sort_keys=True)


print "finish!"



#パッチの数の取り方．．currentで取ってjsonに変換した後に値を取得しカウントダウン式に取る？

#レビューコメントの取り方
#while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
    #script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/comments"'
