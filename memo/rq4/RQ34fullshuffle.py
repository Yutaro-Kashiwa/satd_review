# coding: UTF-8

import os
import commands
import sys
import re #正規表現用
import json
import codecs
import numpy
from time import sleep
import subprocess
import multiprocessing
import math
import urlparse
import csv
import random

csv.field_size_limit(sys.maxsize)

#python2
#使い方：「python review_extract.py openstack」 という具合．
#RQ3のアウトプットファイル４つにあるコメントを「まとめず」それぞれシャッフルする．
#引数1=プロジェクト名/リポジリ名

#TODO list
#1.４ファイルから読み込み
#2.ヘッダを排除してまとめる
#3.シャッフル
#4.csv出力
#  csv形式で出力すべきか．

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


def comment_get(url, hash):
    is_diff = False #i行目がdiff箇所に該当するか否かを入力する．
    list = []
    comments = ""
    temp_str = "" #一時保存用文字列
    multi_line = False
    after_solo = False #１行コメント(//系)の直後ならTrueにする．単行コメントが連続するなら文字列をつなぐ．
    javadoc = False #javadocの文法である疑いがあるならtrue.その場合@もあればyieldを行わない．
    now_line = 1
    start_line = 0
    intro_id = ""
    now_filename = url #チェックアウトに合わせて変えていくファイル名 .DS/proj_nameまでを消したもの
    #print "pass:" + url
    now_filename = now_filename.replace('./DS/' + proj_name + '/', '', 1)
    #print "now_filename:" + now_filename
    #ファイル開閉処理が入ってないやん．
    try:
        with open(url, "r+") as f:
            line = f.readline()
            while line: #ここhttps://除外をやっておく？
                if (re.search(re.escape(r"http://"), line) or re.search(re.escape(r"https://"), line)) and multi_line == False: #http exclude
                    if after_solo == True: #単行コメントの直後の場合の処理
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                    after_solo = False
                    now_line += 1 #continue前に次の行への処理は必須
                    line = f.readline()
                    continue
                elif re.search(re.escape(r"/*"), line) and multi_line == True: # /*
                    if after_solo == True: #単行コメントの直後の場合の処理
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                    after_solo = False
                    multi_line = True
                    comments = line[line.find("/*"):-1] + "\n"
                    if re.match(re.escape(r"/*"), comments):
                        javadoc = True
                    start_line = now_line
                elif re.search(re.escape(r"*/"), line) and multi_line == True : # */ bool=trueの条件も追加
                    comments += line[0:line.index("*/")]
                    multi_line = False
                    #list.append([comments, start_line, now_line])
                    #blameするならこのタイミングがいいか？
                    #intro_id = blame(url, start_line)
                    after_solo = False
                    if javadoc == False or re.search(re.escape(r"TODO"), comments) or re.search(re.escape(r"XXX"), comments) or re.search(re.escape(r"FIXME"), comments): #javadocでない，もしくはTODO,FIXME,XXXのいずれかの語を含むなら
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename, "last_SHA":hash} #dictはキーの順番保持しない．
                    javadoc == False
                elif re.search(re.escape(r"//"), line) and multi_line == False : #//
                    temp_str = line[line.find("//"):-1] #改行文字は除外しない index -> find
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    if after_solo == True:
                        comments += temp_str
                    else:
                        comments = temp_str
                        start_line = now_line
                        after_solo = True
                elif re.search(re.escape(r"/*"), line) and re.search(re.escape(r"*/"), line) and multi_line == False : # /* 〜〜〜 */
                    comments = line[line.find("/*"):line.index("*/")+1]
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":now_line, "end_line":now_line, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                elif multi_line :
                    comments += line
                    if not re.search(re.escape(r"*"), line):
                        javadoc = False #javadocは行ごとに*が入ってる．
                else:
                    if after_solo == True: #単行コメントの直後の場合の処理
                        yield {"proj_name":proj_name, "pass":url, "comment":comments, "start_line":start_line, "end_line":now_line - 1, "SHA":hash, "now_filename":now_filename, "last_SHA":hash}
                        after_solo = False
                    else:
                        after_solo = False
                now_line += 1
                line = f.readline()
    except IOError:
        print "IOError occured"
#list2 = [list[0] for x in liar]

#return list #返り値はコメント，開始行，終了行の３要素を持ったリストのリスト


#python系のコメント規則を持つもの(#,'''でコメントをつけられるもの)についてはこっちで対処する．
#def comment_get2(url, hash):
def comment_get2(script, diff_data):
    print "script_len+1 = " + str(len(script)) + ", diff_data_len = " + str(len(diff_data))
    after_diff = False
    is_diff = False #i行目がdiff箇所に該当するか否かを入力する．
    list = []
    comments = "" #複数行まとめた文字列
    temp_str = "" #一時保存用文字列
    result = []
    multi_line = False
    after_solo = False #１行コメント(//系)の直後ならTrueにする．単行コメントが連続するなら文字列をつなぐ．
    javadoc = False #javadocの文法である疑いがあるならtrue.その場合@もあればyieldを行わない．
    now_line = 1
    start_line = 0
    intro_id = ""
    #now_filename = url #チェックアウトに合わせて変えていくファイル名 .DS/proj_nameまでを消したもの
    #print "pass:" + url
    #now_filename = now_filename.replace('./DS/' + proj_name + '/', '', 1)
    #print "now_filename:" + now_filename
    #ファイル開閉処理が入ってないやん．
    try:
        for line in script:
            #line = f.readline() #入力がリスト形式なのでここ変更すべき
            #while line: #ここhttps://除外をやっておく？
                after_diff = is_diff
                is_diff = diff_data[now_line] #todo:out of rangeになる
                #http://関連の対策はpythonでは不要
                if re.search(re.escape(r"'''"), line) and multi_line == False: # /*
                    if after_solo == True and after_diff == True: #単行コメントの直後の場合の処理
                        result.append(comments)
                    after_solo = False
                    multi_line = True
                    comments = line[line.find("'''"):-1] + "\n"
                    if re.match(re.escape(r"'''"), comments):
                        javadoc = True
                    start_line = now_line
                elif re.search(re.escape(r"'''"), line) and multi_line == True : # */ bool=trueの条件も追加
                    comments += line[0:line.index("'''")]
                    multi_line = False
                    #list.append([comments, start_line, now_line])
                    #blameするならこのタイミングがいいか？
                    #intro_id = blame(url, start_line)
                    after_solo = False
                    #if javadoc == False or re.search(re.escape(r"TODO"), comments) or re.search(re.escape(r"XXX"), comments) or re.search(re.escape(r"FIXME"), comments):
                    if 1: #javadocの心配はないので
                        #javadocでない，もしくはTODO,FIXME,XXXのいずれかの語を含むなら
                        result.append(comments)
                    javadoc == False
                elif re.search(re.escape(r"#"), line) and multi_line == False and is_diff == True: #//
                    temp_str = line[line.find("#"):-1] #改行文字は除外しない index -> find
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    if after_solo == True and is_diff == True:
                        comments += temp_str
                    else:
                        comments = temp_str
                        start_line = now_line
                        after_solo = True
                elif re.search(re.escape(r"'''"), line) and re.search(re.escape(r"'''"), line) and multi_line == False : # /* 〜〜〜 */
                    comments = line[line.find("'''"):line.index("'''")+1]
                    #list.append([comments, now_line, now_line]) #要素追加
                    #intro_id = blame(url, now_line)
                    result.append(comments)
                elif multi_line and is_diff == True:
                    comments += line
                    if not re.search(re.escape(r"*"), line):
                        javadoc = False #javadocは行ごとに*が入ってる．
                else:
                    if after_solo == True: #単行コメントの直後の場合の処理
                        result.append(comments)
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
        n_delete = comment #\n_delete.つまり改行消した版の文字列をここへ突っ込む．
        n_delete = n_delete.replace('\r\n', ' ') #\rのreplaceも入れるべきか？
        n_delete = n_delete.replace('\n', ' ') #\rのreplaceも入れるべきか？
        n_delete = n_delete.replace('\\n', ' ')
        commentList[id] = n_delete
        
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
    input = subprocess.check_output(script, shell=True, cwd='./')
    #inputから")]}'"を除外する．
    input = input.replace(")]}'\n", "", 1)
    return input

def write_read(input, path): #指定パスに書き込みを行い，さらに読み込んで辞書を返り値に取る
    with open(path, 'w') as f:
        f.write(input)
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    return dic

def url_encode(string): #urlエンコード．スラッシュを%2Fに変えます．
    string = string.replace("/", "%2F")
    return string

def url_decode(string): #urlデコード．%2Fをスラッシュに変えます．
    string = string.replace("%2F", "/")
    return string

def delete_header(path):
    with open(path, 'r') as f:
        r = csv.reader(f)
        reader = [row for row in r] #２次元リスト化
    return reader[1:]

###########################################################################
#保存形式は？
#レビューのプロジェクト情報.. リストでプロジェクト名を保存させるのはメモリオーバーが考えられるから賢明でないと思う．
#
#openstackのgerritname .. review.opendev.org
#qt .. codereview.qt-project.org



#必要ディレクトリの準備
now_end = 673199 #qt=263350


proj_name = "openstack"
sub_name = "nova"
lang = "py"


if len(sys.argv) >= 2: #プログラム名の後に引数があるなら(argvはプログラム名も数に含めている)
    argvs = sys.argv
    proj_name = argvs[1]
    #sub_name = argvs[2]
    #ignore = argvs[3] #引数に値が存在すれば，その分だけすでに終わってることにする
    #ignore = int(ignore)


#number = ignore #number..現在見ているレビューidのこと．


if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
    now_end = 673199
if proj_name == "qt":
    address = "codereview.qt-project.org"
    now_end = 263350


#number = int(number) #文字列ー＞数値

#SATD_haveの情報を呼び出す
#with open('./dict/result_RQ0_' + proj_name + '.json', 'r') as g:
#    json_dic = json.load(g)

#ignoreについての処理は未対応．

list_count = 0 #進捗表示用変数
#error_ids = [] #checkoutに失敗したIDを格納する．
#path1 = './csv/result_RQ34_'+ sub_name +'.csv' #レビュ中で追加/削除されたSATDの数
path2 = './data/RQ3com_'+ proj_name +'.csv' #削除されたコメントの内容
path3 = './data/RQ4com_'+ proj_name +'.csv' #追加されたコメントの内容
path4 = './data/delunreview_com_'+ proj_name +'.csv' #追加されたコメントの内容
path5 = './data/addunreview_com_'+ proj_name +'.csv' #追加されたコメントの内容




list1 = delete_header(path2)
list2 = delete_header(path3)
list3 = delete_header(path4)
list4 = delete_header(path5)


total_list = list1
total_list2 = list2
total_list3 = list3
total_list4 = list4

head = "NUMBER,FILE_NAME,PATCH,LINE,LINK,COMMENT\n" #2-4全部同じ
random.seed(2)
random.shuffle(total_list)
random.seed(2)
random.shuffle(total_list2)
random.seed(2)
random.shuffle(total_list3)
random.seed(2)
random.shuffle(total_list4)
out_path1 = './RQanswers/comment_shuffle_RQ3_'+ proj_name +'.csv'
out_path2 = './RQanswers/comment_shuffle_RQ4_'+ proj_name +'.csv'
out_path3 = './RQanswers/comment_shuffle_del_'+ proj_name +'.csv'
out_path4 = './RQanswers/comment_shuffle_add_'+ proj_name +'.csv'
with open(out_path1, 'w') as f:
    f.write(head)
with open(out_path2, 'w') as f:
    f.write(head)
with open(out_path3, 'w') as f:
    f.write(head)
with open(out_path4, 'w') as f:
    f.write(head)


#まず最初にセルフリスト(self_review_(sub).json)の統合をしておこう (self_merger.pyに分離しても良い)
#
openstack_list = [['nova', 'glance', 'swift'], ['cinder', 'neutron'], [], [], []]
qt_list = [['qtquickcontrols', 'qtenginio', 'qtrepotools', 'qtx11extras', 'qtmacextras',
            'qtsvg', 'qtbase'],
            ['qtmultimedia', 'qtandroidextras', 'qttranslations', 'qtdoc', 'qtwinextras', 'qtquick1', 'qtlocation', 'qtbase'],
            ['qtactiveqt', 'qtwebsockets', 'qttools', 'qtxmlpatterns', 'qtqa', 'qtsensors',
             'qtimageformats', 'qtwebchannel', 'qtserialport', 'qtconnectivity',
             'qtgraphicaleffects', 'qtwebkit-examples', 'qtwebkit', 'qtscript',
             'qtdeclarative', 'qtbase'],
            ['qtbase'], ['qtbase']]
input_dir = ['data', 'data_msr1', 'data_msr2', 'data_msr3', 'data_msr4'] #入力に連動させよ
if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
    active_list = openstack_list
if proj_name == "qt":
    address = "codereview.qt-project.org"
    now_end = 263350
    active_list = qt_list

self_list = []
for i, sub_list in enumerate(active_list, 0): #enumerate = 0から同時にカウントを得る
    for sub_name in sub_list:
        #url = url_head + str(number) + "/"
        #output = str(i) + "," + str(number) + "," + url + "," + "\n"
        with open('./' + input_dir[i] + '/self_review_'+ sub_name +'.json', 'r') as f:
            sub_dic = json.load(f)
        self_list.extend(sub_dic["self_review"]) #データ結合

self_dict = {"self_review":self_list}
with open('./data/self_review_' + proj_name +'.json', 'w') as f:
    json.dump(self_dict, f)

print "self_review_merged"
####プロジェクト単位でのセルフリスト作成はここまで.

#1.
for data in total_list:
    #先にcsv->辞書形式にコンバートすべき．
    if len(data) < 6: #一部コメントが""を抜けてることによる弊害．後で直す
        continue
    #print data
    number = data[2]
    file = data[3]
    patch = data[4]
    line = data[5]
    comment = data[6]
    #comment = com["comment"]
    try:
        comment = comment.encode("utf-8")
    except UnicodeDecodeError:
        pass
    if int(data[2]) in self_dict["self_review"]: #セルフレビューの除外
        continue
    #line = com["start_line"]
    comment = re.sub('\"', '\"\"', comment)
    f_name = url_decode(file)
    #resultディレクトリと.jsonを引く
    minus_string = dir_calc(proj_name, number)+'RQ34_'
    f_name = f_name.replace(minus_string, '', 1)
    f_name = f_name.replace('.json', '', 1)
    link_url = "https://" + address + "/c/" + str(number) + "/" + str(patch) + "/" + str(f_name) + "@a" + str(line)
    output = str(number) + "," + f_name + "," + str(patch) + "," + str(line) + "," + link_url + ',"' + comment + '"\n'

    with open(out_path1, 'a') as f:
        f.write(output)
#もしかしたらunicode文字への変換処理が必要かもしれない．

#2.めんどくさいので同じコード４個コピペ．あとで直せ．
for data in total_list2:
    #先にcsv->辞書形式にコンバートすべき．
    if len(data) < 6: #一部コメントが""を抜けてることによる弊害．後で直す
        continue
    number = data[2]
    file = data[3]
    patch = data[4]
    line = data[7]
    comment = data[9]
    #comment = com["comment"]
    try:
        comment = comment.encode("utf-8")
    except UnicodeDecodeError:
        pass
    if int(data[2]) in self_dict["self_review"]: #セルフレビューの除外
        continue
    #line = com["start_line"]
    comment = re.sub('\"', '\"\"', comment)
    f_name = url_decode(file)
    #resultディレクトリと.jsonを引く
    minus_string = dir_calc(proj_name, number)+'RQ34_'
    f_name = f_name.replace(minus_string, '', 1)
    f_name = f_name.replace('.json', '', 1)
    link_url = "https://" + address + "/c/" + str(number) + "/" + str(patch) + "/" + str(f_name) + "@" + str(line)
    output = str(number) + "," + f_name + "," + str(patch) + "," + str(line) + "," + link_url + ',"' + comment + '"\n'

    with open(out_path2, 'a') as f:
        f.write(output)

#3.
for data in total_list3:
    #先にcsv->辞書形式にコンバートすべき．
    if len(data) < 6: #一部コメントが""を抜けてることによる弊害．後で直す
        continue
    number = data[2]
    file = data[3]
    patch = data[4]
    line = data[5]
    comment = data[6]
    #comment = com["comment"]
    try:
        comment = comment.encode("utf-8")
    except UnicodeDecodeError:
        pass
    if int(data[2]) in self_dict["self_review"]: #セルフレビューの除外
        continue
    #line = com["start_line"]
    comment = re.sub('\"', '\"\"', comment)
    f_name = url_decode(file)
    #resultディレクトリと.jsonを引く
    minus_string = dir_calc(proj_name, number) + 'RQ34_'
    f_name = f_name.replace(minus_string, '', 1)
    f_name = f_name.replace('.json', '', 1)
    link_url = "https://" + address + "/c/" + str(number) + "/" + str(patch) + "/" + str(f_name) + "@a" + str(line)
    output = str(number) + "," + f_name + "," + str(patch) + "," + str(line) + "," + link_url + ',"' + comment + '"\n'

    with open(out_path3, 'a') as f:
        f.write(output)


for data in total_list4:
    #先にcsv->辞書形式にコンバートすべき．
    if len(data) < 6: #一部コメントが""を抜けてることによる弊害．後で直す
        continue
    number = data[2]
    file = data[3]
    patch = data[4]
    line = data[7]
    comment = data[9]
    #comment = com["comment"]
    try:
        comment = comment.encode("utf-8")
    except UnicodeDecodeError:
        pass
    if int(data[2]) in self_dict["self_review"]: #セルフレビューの除外
        continue
    #line = com["start_line"]
    comment = re.sub('\"', '\"\"', comment)
    f_name = url_decode(file)
    #resultディレクトリと.jsonを引く
    minus_string = dir_calc(proj_name, number)+'RQ34_'
    f_name = f_name.replace(minus_string, '', 1)
    f_name = f_name.replace('.json', '', 1)
    link_url = "https://" + address + "/c/" + str(number) + "/" + str(patch) + "/" + str(f_name) + "@" + str(line)
    output = str(number) + "," + f_name + "," + str(patch) + "," + str(line) + "," + link_url + ',"' + comment + '"\n'


    with open(out_path4, 'a') as f:
        f.write(output)
    

#ここからさらに


#path = './dict/result_RQ34_' + sub_name + '.json'

#with open(path, 'w') as e:
#    json.dump(result, e)


#パッチの数の取り方．．currentで取ってjsonに変換した後に値を取得しカウントダウン式に取る？

#レビューコメントの取り方
#while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
#script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/comments"'
