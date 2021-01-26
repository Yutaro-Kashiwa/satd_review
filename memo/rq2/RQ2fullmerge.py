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
#import statistics
import numpy as np
from scipy import linalg as LA #信頼区間が出せないのでいらないかも
import statsmodels.api as sm
import pandas
import matplotlib.pyplot as plt
import seaborn as sns #グラフ描画に使う
from sklearn.ensemble import RandomForestClassifier #以下はランダムフォレスト用
from sklearn.ensemble import ExtraTreesClassifier
from sklearn import datasets
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

#url:https://review.opendev.org/#/c/ or https://codereview.qt-project.org/c/

#python2
#RQ2に対する結果内容をプロジェクト単位でまとめる．全てのサブプロジェクトのcsvがすでに作られていることが条件．
#使い方：「python RQ2fullmerge.py openstack」 という具合．
#タイミング：RQ2checker使用後
#データ形式：PROJ,SUB_NAME,TYPE,SIZE,MERGED,notMERGED,notRATE,PATCH_SUM,PATCH_AVE,PATCH_MED\
#手順：
#1.ファイルを読み込む．file:data_msrX/RQ2_(main)_(sub).json
#2.１行目は読むだけ
#3.２行目はSATD_have．MERGED,notMERGED,PATCH_SUMを見て加算．
#4.３行目はnot_have．同じ要素を見て加算．
#4.全部たす．
#TODO:全マージファイル作ろう

#２次元リスト
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


def rq2checker(path, mode): #modeはRQ2については１，RQ2-2については２を記述する
    with open(path, 'r') as f:
        r = csv.reader(f)
        reader = [row for row in r] #２次元リスト化

    merged_count = 0 #MERGEDになってるレビューの数
    patch_sum = 0 #パッチ数を全部たす
    p_array = [] #中央値用の配列
    #reader.pop(0) #はじめの行を除外する

    for row in reader[1:]: #[2]=status, #[3]=patch_num
        patch_sum += int(row[3])
        p_array.append(int(row[3]))
        if row[2] == "MERGED":
            merged_count += 1
            
    length = len(reader)-1
    if length == 0:
        patch_ave = 0
        patch_med = 0
        not_rate = 0
    else:
        patch_ave = float(patch_sum) / float(length)
        patch_med = float(numpy.median(p_array))
        not_rate = float(length - merged_count) / float(length) * 100
        
    print " size  MERGED  notMERGED  not_rate  patch_sum  patch_ave  patch_med"
    print "%5d  %6d  %9d    %3.2f%%  %9d       %3.2f       %3.2f" % (length, merged_count, length - merged_count, not_rate, patch_sum, patch_ave, patch_med)
    
    if mode == 1:
        mode_str = "SATD_have"
    elif mode == 2:
        mode_str = "not_have"
    write_list = [proj_name, sub_name, mode_str, length, merged_count,length - merged_count,  str(not_rate)+"%", patch_sum, patch_ave, patch_med]
    write_list = map(str, write_list) #まとめて文字列にする
    with open(out_path, 'a') as f:
        out_str = ",".join(write_list)
        f.write(out_str + "\n")

def delete_header(path):
    with open(path, 'r') as f:
        r = csv.reader(f)
        reader = [row for row in r] #２次元リスト化
    return reader[1:]



#参考v1
#https://webcache.googleusercontent.com/search?q=cache:CuyTA3RA_9QJ:https://qiita.com/ynakayama/items/dae1f5bf5688b7ce8e77+&cd=2&hl=ja&ct=clnk&gl=jp&client=safari
#参考v2(こっちのが良さそう）
#https://to-kei.net/python/data-analysis/linearregression/
#1.ファイル開いてcsv形式にする
#2.説明変数１=[4](diffsize), 説明変数２=[7](satd or not),
#  目的変数=[6](merged or not) or [3](patch_num)
#3.解析実行
def jukaiki(mode): #mode...1なら目的変数はnot_merged?になる．2ならpatch_numになる．
    data = pandas.read_csv(out_path_ex)
    x12 = data.iloc[:,[8,7]].copy() #説明変数１...log(diffsize) , 説明変数２...satd or not
    #x12 = data.iloc[:,7]
#    for i in range(len(x12.iloc[:,0])):
#        val = x12.iloc[i,0]
#        if val > 0:
#            x12.iloc[i,0] = math.log(val)
#        else:
#            x12.iloc[i,0] = math.log(1)
    #print x12.iloc[:,0]
    X = sm.add_constant(x12)
    if mode == 1:
        y = data.iloc[:,6] #目的変数...not_merged?
        model = sm.Logit(y, X) #目的変数がダミー変数ならロジスティック回帰分析にする必要がある
        #model = sm.GLM(y, X, family=sm.families.Binomial()) #これも実質同じだけどお好みで．
    elif mode == 2:
        y = data.iloc[:,3] #目的変数...patch_num
        model = sm.OLS(y, X) #最小二乗法
    else:
        raise error #絶対に弾かないといけないエリア
    results = model.fit()
    print results.summary()  #これどうやって保存するのー！！！！
    #print type(results.summary())
    with open('./RQanswers/RQ2jukaiki' + str(mode) + '_' + proj_name + '.txt', 'w') as f:
        #string = results.summary().as_csv()
        #f.write(string)
        f.write(str(results.summary())) #statsmodels.iolib.summary.Summaryっていう変な型してるので無理やりstrに



#適宜分析したい情報に応じていじるやつ
def sokan(mode): #mode...1なら目的変数はnot_merged?になる．2ならpatch_numになる．
    data = pandas.read_csv(out_path_ex)
    x12 = data.iloc[:,8] #説明変数１...log(diffsize) , 説明変数２...satd or not
    #print x12.iloc[:,0]
    X = sm.add_constant(x12)
    if mode == 1:
        y = data.iloc[:,7] #目的変数...satd?
        model = sm.Logit(y, X) #目的変数がダミー変数ならロジスティック回帰分析にする必要がある
        #model = sm.GLM(y, X, family=sm.families.Binomial()) #これも実質同じだけどお好みで．
    elif mode == 2: #使用不可
        y = data.iloc[:,3] #目的変数...patch_num
        model = sm.OLS(y, X) #最小二乗法
    else:
        raise error #絶対に弾かないといけないエリア
    results = model.fit()
    print results.summary()  #これどうやって保存するのー！！！！
    #data = pandas.read_csv(out_path_ex)単純な相関ならこれでよし
    #x12 = data.iloc[:,[8,7]].copy() #説明変数１...log(diffsize)
    #print x12.corr(method='spearman')

#参考：https://webcache.googleusercontent.com/search?q=cache:IYUkC_4PtwgJ:https://qiita.com/TomokIshii/items/290adc16e2ca5032ca07+&cd=2&hl=ja&ct=clnk&gl=jp&client=safari
#ポッチャマ：https://docs.pyq.jp/python/machine_learning/tips/train_test_split.html
#これも：https://webcache.googleusercontent.com/search?q=cache:k-lPWq-xj0AJ:https://qiita.com/darkqueenreal/items/0c0b1884acaab5675159+&cd=3&hl=ja&ct=clnk&gl=jp&client=safari
#pandas->list：https://note.nkmk.me/python-pandas-list/
def randomforest():
    data = pandas.read_csv(out_path_ex)
    x = data.iloc[:,[8,7]] #説明変数１...log(diffsize) , 説明変数２...satd or not
    #print x
    x = x.values.tolist()
    y = data.iloc[:,6] #ターゲット：[6]=not_merged?, [3]=修正回数
    y = y.values.tolist()
    #random_state...シード用
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=0)
    #もしかしたらExtraTreesClassifierのがいいかも(精度よりも特徴量の重要度評価を目的とするときに使うらしい）
    clf_rf = RandomForestClassifier()
    #clf_rf = ExtraTreesClassifier()
    clf_rf.fit(X_train, y_train)
    y_pred = clf_rf.predict(X_test)

    accu = accuracy_score(y_test, y_pred)
    print('accuracy = {:>.4f}'.format(accu))

    # Feature Importance
    fti = clf_rf.feature_importances_

    print('Feature Importances:')
    for i, feat in enumerate(fti):
        print('[' + str(i) + ']:' + str(fti[i]))

#保存形式は？
#レビューのプロジェクト情報.. リストでプロジェクト名を保存させるのはメモリオーバーが考えられるから賢明でないと思う．
#
#openstackのgerritname .. review.opendev.org
#qt .. codereview.qt-project.org
'''
if sys.argv >= 2: #プログラム名の後に引数としてプロジェクト名があるなら
    argvs = sys.argv
    proj_name = argvs[1]
#proj_nameは団体名も含めてとる．例：openstack/もちゃんと入れる．
'''

####################################################################################
####################################################################################
####################################################################################

#必要ディレクトリの準備
now_end = 673199 #qt=263350


proj_name = "openstack"
sub_name = "nova"
lang = "py"

if len(sys.argv) >= 2: #プログラム名の後に引数があるなら(argvはプログラム名も数に含めている)
    argvs = sys.argv
    proj_name = argvs[1]
    #ignore = argvs[3] #引数に値が存在すれば，その分だけすでに終わってることにする
    #ignore = int(ignore)
else:
    pass
    #ignore = 0

#number = ignore #number..現在見ているレビューidのこと．


if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
if proj_name == "qt":
    address = "codereview.qt-project.org"



#number = int(number) #文字列ー＞数値



#TODO list
#1.RQ0の結果を読み込む
#2.query.jsonのstatusで採録状態を，revisions->sha->_numberパッチ数がどちらも取れるはず．
#  なおsha不明でパッチ数を見れないものや，skipでコード本文が読めないことが原因で
#  SATDを含んでいるかどうかわからないものはについては元からerror_idsに分類されているはず．
#  skipの場合はdiffはgitwebに存在するがAPIで直接は取れない上にパッチ単位じゃないので考えるだけ無駄．諦める．
#3.SATD_haveとnot_haveで結果を分ける
#csv...
#TYPE＝SATD_have or not_have
#NUMBER=change_idのこと
#STATUS=採録されたか否か
#PATCH_NUM=採録される，もしくは却下されるまでに提出されたパッチ総数

#number...レビューナンバー

############

if len(sys.argv) >= 2: #プログラム名の後に引数があるなら(argvはプログラム名も数に含めている)
    argvs = sys.argv
    proj_name = argvs[1]
    #sub_name = argvs[2]
    #ignore = argvs[3] #引数に値が存在すれば，その分だけすでに終わってることにする
    #ignore = int(ignore)
else:
    raise Error
    #ignore = 0

if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
    active_list = openstack_list
if proj_name == "qt":
    address = "codereview.qt-project.org"
    now_end = 263350
    active_list = qt_list


#result = {"SATD_have":[], "error_ids":[], "not_have":[]}

#データ形式：PROJ,SUB_NAME,TYPE,SIZE,MERGED,notMERGED,notRATE,PATCH_SUM,PATCH_AVE,PATCH_MED\
#手順：
#1.ファイルを読み込む．file:data_msrX/RQ2_(main)_(sub).json
#2.１行目は読むだけ
#3.２行目はSATD_have．SIZE,MERGED,notMERGED,PATCH_SUMを見て加算．
#4.３行目はnot_have．同じ要素を見て加算．
#4.全部たす．

#[0]はSATD_haveのデータ，[1]はnot_haveのデータ
size_full = [0, 0]
merged_full = [0, 0]
not_merged_full = [0, 0]
patch_sum_full = [0, 0]
not_rate = [0.0, 0.0]
patch_ave = [0.0, 0.0]
for i, sub_list in enumerate(active_list, 0): #enumerate = 0から同時にカウントを得る
    for sub_name in sub_list: #この中が実処理
        #url = url_head + str(number) + "/"
        #output = str(i) + "," + str(number) + "," + url + "," + "\n"
        with open('./' + input_dir[i] + '/RQ2_'+ proj_name + '_' + sub_name +'.csv', 'r') as f:
            r = csv.reader(f)
            reader = [row for row in r] #２次元リスト化
        #SATD_haveのデータ取得．２行目使用．
        size_full[0] += int(reader[1][3])
        merged_full[0] += int(reader[1][4])
        not_merged_full[0] += int(reader[1][5])
        patch_sum_full[0] += int(reader[1][7])
        #not_haveのデータ取得．３行目使用．
        size_full[1] += int(reader[2][3])
        merged_full[1] += int(reader[2][4])
        not_merged_full[1] += int(reader[2][5])
        patch_sum_full[1] += int(reader[2][7])
    
    
#全部加算し終えたらnot_rate, patch_aveの計算を行う．
for i in range(0,2): #0..1
    patch_ave[i] = float(patch_sum_full[i]) / float(size_full[i])
    #patch_med = float(numpy.median(p_array))
    not_rate[i] = float(not_merged_full[i]) / float(size_full[i]) * 100

out_path = './data/RQ2_' + proj_name + '.csv'
output1 = "PROJ,SUB_NAME,TYPE,SIZE,MERGED,notMERGED,notRATE,PATCH_SUM,PATCH_AVE,PATCH_MED\n"
write_list1 = [proj_name, "ALL", "SATD_have", size_full[0], merged_full[0], not_merged_full[0],  str(not_rate[0])+"%", patch_sum_full[0], patch_ave[0], "---"]
write_list2 = [proj_name, "ALL", "not_have", size_full[1], merged_full[1], not_merged_full[1],  str(not_rate[1])+"%", patch_sum_full[1], patch_ave[1], "---"]
write_list1 = map(str, write_list1) #まとめて文字列にする
write_list2 = map(str, write_list2) #まとめて文字列にする
output2 = ",".join(write_list1)
output3 = ",".join(write_list2)


with open(out_path, 'w') as f:
    f.write(output1)
    f.write(output2 + "\n")
    f.write(output3)
    

########さらにデータを1つにまとめる
satd_have = 0
merged = 0
out_path = './RQanswers/RQ2_fullmerge_' + proj_name + '.csv'
out_path_ex = './RQanswers/RQ2all_fullmerge_' + proj_name + '.csv' #SATD持ってないやつも無差別に
first_output = "TYPE,NUMBER,STATUS,PATCH_NUM,diffSIZE,TIME(sec),not_merged?,satd?,log(diffSIZ)\n"
with open(out_path, 'w+') as f:
    f.write(first_output)
with open(out_path_ex, 'w+') as f:
    f.write(first_output)
for i, sub_list in enumerate(active_list, 0): #enumerate = 0から同時にカウントを得る
    for sub_name in sub_list: #この中が実処理
        with open('./' + input_dir[i] + '/result_RQ2_' + sub_name +'.csv', 'r') as g:
            next(g)
            with open(out_path, 'a') as f:
                for line in g:
                    #splitでMERGEDか否かで0と1を末尾に突っ込もう
                    line = line.strip()
                    splited_line = line.split(',')
                    diffsize = int(splited_line[4])
                    if diffsize > 0:
                        logged_diffsize = math.log(diffsize)
                    else:
                        logged_diffsize = math.log(1) #size1とみなす
                    if splited_line[2] == 'MERGED':
                        merged = 0 #不採録率を見たいので0と1を反転してます
                    else:
                        merged = 1
                    f.write(line + ',' + str(merged) + ',1,' + str(logged_diffsize)+ '\n')
                    with open(out_path_ex, 'a') as e:
                        e.write(line + ',' + str(merged) + ',1,' + str(logged_diffsize)+ '\n')


out_path = './RQanswers/RQ2-2_fullmerge_' + proj_name + '.csv'
first_output = "TYPE,NUMBER,STATUS,PATCH_NUM,diffSIZE,TIME(sec),not_merged?,satd?,log(diffSIZ)\n"
with open(out_path, 'w+') as f:
    f.write(first_output)
for i, sub_list in enumerate(active_list, 0): #enumerate = 0から同時にカウントを得る
    for sub_name in sub_list: #この中が実処理
        with open('./' + input_dir[i] + '/result_RQ2-2_' + sub_name +'.csv', 'r') as g:
            next(g)
            with open(out_path, 'a') as f:
                for line in g:
                    #splitでMERGEDか否かで0と1を末尾に突っ込もう
                    line = line.strip()
                    splited_line = line.split(',')
                    diffsize = int(splited_line[4])
                    if diffsize > 0:
                        logged_diffsize = math.log(diffsize)
                    else:
                        logged_diffsize = math.log(1) #size1とみなす
                    
                    if splited_line[2] == 'MERGED':
                        merged = 0 #こっちも
                    else:
                        merged = 1
                    f.write(line + ',' + str(merged) + ',0,' + str(logged_diffsize)+ '\n')
                    with open(out_path_ex, 'a') as e:
                        e.write(line + ',' + str(merged) + ',0,' + str(logged_diffsize)+ '\n')
#########
#さらにもう一歩！ここからセルフレビューと時間マイナスのを消した差分を作成する
sabun = './RQanswers/RQ2_notselfandminus_' + proj_name + '.csv'
out_path = './RQanswers/RQ2_fullmerge_' + proj_name + '.csv'
with open(sabun, 'w+') as f:
    f.write(first_output)
    with open(out_path, 'r') as g:
        next(g)
        for line in g:
            #splitでMERGEDか否かで0と1を末尾に突っ込もう
            splited_line = line.split(',')
            if splited_line[5] == "": #self review remove
                continue
            elif float(splited_line[5]) < 0: #unknwon time remove
                continue
            else:
                f.write(line)
        

sabun = './RQanswers/RQ2-2_notselfandminus_' + proj_name + '.csv'
out_path = './RQanswers/RQ2-2_fullmerge_' + proj_name + '.csv'
with open(sabun, 'w+') as f:
    f.write(first_output)
    with open(out_path, 'r') as g:
        next(g)
        for line in g:
            #splitでMERGEDか否かで0と1を末尾に突っ込もう
            splited_line = line.split(',')
            if splited_line[5] == "": #self review remove
                continue
            elif float(splited_line[5]) < 0: #unknwon time remove
                continue
            else:
                f.write(line)
        

##########
#もう一つ追加！ランダムソート
#1.MERGEDのものは除外
#2.並べ替え
#3.保存
'''
sabun3 = './RQanswers/RQ2all_onlyAbondon_' + proj_name + '.csv'
with open(sabun3, 'w+') as f:
    f.write(first_output)
    with open(out_path_ex, 'r') as g:
        next(g)
        for line in g:
            #splitでMERGEDか否かで0と1を末尾に突っ込もう
            splited_line = line.split(',')
            if splited_line[2] == "MERGED": #self review remove
                continue
            else:
                f.write(line)
                
#ここまで不採録のみ取得する動作
#ここからシャッフル
list = delete_header(sabun2)
random.seed(3)
random.shuffle(list)
with open(sabun3, 'w+') as f:
    f.write(first_output)
    writer = csv.writer(f)
    writer.writerows(list)

'''

#各種データ表示
print "*** " + proj_name + " ***"
path = './RQanswers/RQ2_fullmerge_' + proj_name + '.csv'
print "[SATD have]"
rq2checker(path,1)
path = './RQanswers/RQ2-2_fullmerge_' + proj_name + '.csv'
print "[not have]"
rq2checker(path,2)

##ここでさらに重回帰分析を行うことになる
jukaiki(1)
jukaiki(2)

###diffsizeの分布を取りたい！
#https://webcache.googleusercontent.com/search?q=cache:vpWyhC0_C_YJ:https://qiita.com/Morio/items/d75159bac916174e7654+&cd=1&hl=ja&ct=clnk&gl=jp&client=safari

sns.set(style="darkgrid", palette="muted", color_codes=True)
out_path1 = './RQanswers/RQ2_fullmerge_' + proj_name + '.csv' #適宜チェンジ
out_path2 = './RQanswers/RQ2-2_fullmerge_' + proj_name + '.csv' #適宜チェンジ
data = pandas.read_csv(out_path_ex) #RQ2, 2-2で分けた方がいいのでは？+out_path_ex
#x_axis = np.linspace(0, 1000) #0-10M, 1M分割
#x_axis = np.linspace(0, 1000, 200) #対数使わない時用(青を見せたい場合は0,1000,200がいる)
x_axis = np.linspace(0, 30, 60) #対数用
x1 = data.iloc[:, 8] #説明変数１...diffsize(4なら通常，8ならlog
#logx1 = []
#for elem in x1:
#    if elem > 0:
#        logx1.append(math.log(elem))
#    else:
#        logx1.append(math.log(1))
fig, ax1 = plt.subplots() #コピペ
n,bins, patches = plt.hist(x1, x_axis, cumulative=False)
#可能なら第２軸で０〜１となるようなy軸を用意したいんだけど

# 第2軸用値の算出（この辺コピペ）
y2 = np.add.accumulate(n) / len(x1)
x2 = np.convolve(bins, np.ones(2) / 2, mode="same")[1:]
# 第2軸のプロット
ax2 = ax1.twinx()
lines = ax2.plot(x2, y2, ls='-', color='r', label='Cumulative ratio')
ax2.grid(visible=False)
#ここまでコピペ）

#sokan(1)

plt.show() #x軸，diffsize，y軸：diffsizeがxまでのものの個数

randomforest()

#vifも出したいね
#vif = pandas.DataFrame()
#vif["VIF Factor"] =


print "finish!"



#パッチの数の取り方．．currentで取ってjsonに変換した後に値を取得しカウントダウン式に取る？

#レビューコメントの取り方
#while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
#script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/comments"'