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


openstack_bot_list = ['Jenkins', 'Zuul'] #+後ろにCIがつくもの
qt_bot_list = ['Qt Sanity Bot', 'Qt CI Bot'] #ひとまとめにしておいたほうがいいかもしれない

#python2
#使い方：「python review_extract.py openstack nova 0」 という具合．
#引数1=プロジェクト名/リポジリ名
#目的：RQ3.コードレビューにより削除されたSATDの数と種類を見る
#     RQ4.コードレビューにより追加されたSATDの数と種類を見る
#種類はおそらく目視になるかと思われる．
#nova->673199まで取ることにする．8/4 15:05:00．
#時間は2019/07/08 19:11(秒数はなんでもOK）とする．
#最初のパッチでは何もしてないけど最後のパッチで消されてる，そんなSATDを調べる．
#あくまで比較対象となるのは１番目のパッチである，ということに注意点．

#レビューを経て削除されたSATDで考えられるパターンは
#・最初のパッチにはないが最後のパッチではa_commentsに分類されている（最後-最初のaの差集合）
#・最初のパッチではb_commentsに分類されているが最後のパッチでは存在しない．(最初-最後のbの差集合で取れる）
#の２つ．
#レビューを経て追加されたSATDで考えられるパターンは
#・最初のパッチにはないが最後のパッチではb_commentsに分類されている
#の１つ．
#レビューを経ずに削除されたSATD
#
#レビューを経ずに追加されたSATD
#???

#行数と文字列距離の情報も取ったほうがいいか?
#情報が足りない場合は1_ファイル名.jsonみたいな名前のファイルがdiff情報を全部保持してるからそれを活用すると良い．

#ついでにRQ5で使う「すり抜けたSATD」もここで取ろう．
#定義・・・最初のパッチにb_commentsで最後のパッチでもb_comments.
#        すなわち，最初のパッチのb - RQ3comments．もしくは，最初と最後のbの積集合．後者のがいい．


#TODO list
#1.SATD_haveに含まれる各変更に対し，query.jsonを開いて最後のパッチの番号と変更のあったファイルを取得する．
#  その後ファイルそれぞれについて，
#2-1.diff_1_url.jsonを開き，a_comments,b_commentsを取得する．
#2-2.diff_(最後のパッチ番号)_url.jsonを開き，a,b_commentsを取得する．
#2-3.条件に合うSATDを抽出し，それぞれRQ3_url.json, RQ4_url.jsonに格納する．
#  全ての変更に対して行われたら，
#3.RQ3_url.json, RQ4_url.jsonを根こそぎ調べ，数を調べる．
#  csv形式で出力すべきか．

#Q.途中で追加されて削除されたコメントも見れてる？
#A.大丈夫のはず...一応パッチ毎に見てl_a_comments, l_b_commentsを追加＋重複削除って処理をしてるし。

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

#異なるリビジョンの同一コメントを消す．O(n^2)なのでSATD数が多いと処理時間がかかる．気をつけて．
#RQ34用．
#やり方：resultリストに１つずつ要素を突っ込む．
#その際，resultリストの各要素見て，comment一致，ファイル名一致の2条件を満たしていたら中断し，appendしない．
#通常版と比べ，SHAを条件から取り除いている．また，文字列は全てスペースを無視する．
def samecheck(list, mode): #list = そのリビジョンのコメント， #mode = bなら追加処理
    result = []
    judge = True #同一のSATDを発見したらFalseにする．
    length = len(list) #いらないかも
    print "found SATDs = " + str(len(list))
    #最後のパッチから見たいし配列順序反転させる？　終わったらもう１回反転
    #list.reverse() #これいらなくない？
    for x in range(len(list)): #そのリビジョンのコメントそれぞれについて
        #print x
        str1 = list[x]["comment"].replace(" ", "")
        for y in range(len(result)): #その前までのリビジョンのコメントと比較する．
            #でかいデータならlen(list2)ではなくlen(result)にすべし．
            str2 = result[y]["comment"].replace(" ","")
            if str1 == str2 and list[x]["now_filename"] == result[y]["now_filename"]:
                #print "found same SATD"
                #last_found系の更新処理
                if mode == 'b':
                    result[y]["last_patch"] = list[x]["patch"]
                    result[y]["last_startline"] = list[x]["start_line"]
                judge = False
                break
        if judge == True:
            result.append(list[x])
        else:
            judge = True
    print "unique SATDs = " + str(len(result))
    #result.reverse()
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


    
    
def sasyugo(list1, list2): #差集合．commentキーを見て被っているものがあったら消していく．
    #key:sub_Name, pass, start_line, end_line, SHA, now_filename, comment
    #start_lineとend_lineは前に追加削除があると意味がないので使用不可，他は必ず一致する
    #list1が最終パッチ側であることに注意．
    result1 = []
    result2 = []
    for elem1 in list1:
        find_flag = False #同じのが見つかったらTrue
        i = 0
        for elem2 in list2:
            if elem1["comment"] == elem2["comment"]:
                list2.pop(i)
                find_flag = True
                result1.append(elem1)
                break #基本的に１対１の対応関係のはずなので１回見つけたらbreak
            else:
                i += 1
        if find_flag == False: #同じコメントが見つからなかったら
            result2.append(elem1)
            
    return result1, result2


#RQ0から持ってきた.既に取ってきてるAPIの情報を利用してコード全文を返します．
#返り値はa_scriptまたはb_script, bool．a,bはmode引数を利用してどっちかのみ返す．
#boolはファイルなし（主にパッチ１では何も変化してない場合にそうなる）やskippedの時にFalse，
#無事取れてたらTrueとなる．
def code_reader(key, mode):
#key...ファイル名. path3から「diff_」を引けばファイル名が一致する
    #script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/files/' + url_key + '/diff"'
    #input = api_get(script)
    #if input.startswith("<!DOCTYPE HTML PUBLIC") == True: #api_getが異常終了した時に使う
    #    skip_flag = True
    #    print "skipped"
    #    error_ids.append(number)
    #    temp_dict = {"error_ids":error_ids}
    #    with open(t_path, 'w') as e:
    #        json.dump(temp_dict, e)
    #    break
    #ここから差分行の情報を取る必要がある．
    path2 = key #仮．本番までには必ずどこかへしっかり保存せよ
    if not os.path.isfile(path2):
        print "no exist file"                     #TODO:ここも専用処理にしよう
        return [], False
    
    with open(path2, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    
    #ここからは別関数に任せたほうがいいかも．
    a_script = []
    b_script = []
    #a_line = 1
    #b_line = 1
    skip_flag = False
    a_diff = [False] #配列[i] = i行目にコメントが存在するか #今回は使わないと思う．
    b_diff = [False] #0行目は必ずFalseで
    for diff in dic["content"]:
        for key2 in diff.keys(): #前のと後のやつの差分行の登録
            #k = diff[key2]
            if key2 == "a":
                for array in diff[key2]:
                    #print " diff[a]= " + str(diff[key2])
                    #a_script += array
                    a_diff.append(True)
                    a_script.append(array)
                    #a_line += 1
            if key2 == "b":
                for array in diff[key2]:
                    #print " diff[b]= " + str(diff[key2])
                    #b_script += array
                    b_diff.append(True)
                    b_script.append(array)
                    #b_line += 1
            if key2 == "ab":
                for array in diff[key2]:
                    #print " diff[ab]= " + str(diff[key2])
                    #a_script += array
                    #b_script += array
                    a_script.append(array)
                    b_script.append(array)
                    a_diff.append(False)
                    b_diff.append(False)
                    #a_line += 1
                    #b_line += 1
            if key2 == "skip":
                skip_flag = True
                print "skipped"
                return [], False
                #error_ids.append(number)
                #t_path = './dict/temp_RQ0_'+ sub_name +'.json' ####コピー時注意 #t_path記述箇所移動済み
                #temp_dict = {"error_ids":error_ids}
                #with open(t_path, 'w') as e:
                #    json.dump(temp_dict, e)
        if skip_flag == True: #skipが出てたらもう調べようがないです
            return [], False
        #a_line += 1
        #b_line += 1
        #とった情報をどう保存する？フルパス名で保存．
        #a,b_comments...ジェネレータをなんとかしないとだめ
        #print "a_script = " + str(a_script)
        #print "b_script = " + str(b_script)
    #print a_diff
    if skip_flag == True: #skipが出てたらもう調べようがないです
        return [], False
    
    if mode == 'a':
        return a_script, True #スクリプト本文を返り値とする．
    elif mode == 'b':
        return b_script, True
    else:
        raise modeError

#ここからlist2の部分をパッチ１のb_codeに変化させたい．

#同じ文面が元ファイルにあったらSATDの変化はないとみなす
def rq34body(list1, list2): #list1=最終パッチのコメント，list2=パッチ１でのコード
    result1 = [] #list1とlist2で一致がある方はこっち
    result2 = [] #一致がない方はこっち
    list1 = [list1] #今回は１個ずつ辞書型で取ってるのでリスト型にする．
    for elem1 in list1: #elem1...SATD１個分
        str1 = elem1["comment"]
        str1 = str1.replace(" ", "")
        str1_backup = str1
        #print "comment:" + str1
        find_flag = False #同じのが見つかったらTrue
        i = 0
        for elem2 in list2: #elem2...コード１行分
            #str2 = elem2["comment"]
            str2 = elem2
            str2 = str2.replace(" ", "")
            #print "code:" + str2
            #if elem1["comment"] == elem2["comment"]:
            if str1.find(str2) == 0: #先頭が一致しているかをチェック．str2.find(str1)は要るか？
                str1 = str1.replace(str2, "", 1) #一致箇所を削除．左削除で．lstripはリスキー
                if str1 == "": #残りの文字列が無になったら一致とする．
                    find_flag = True
                    result1.append(elem1)
                    break #基本的に１対１の対応関係のはずなので１回見つけたらbreak
                i += 1
            else:
                str1 = str1_backup #str1を元に戻してもう一度チェックする．
                if str1.find(str2) == 0: #先頭が一致しているかをチェック．str2.find(str1)は要るか？
                    str1.replace(str2, "", 1) #一致箇所を削除．左削除で．lstripはリスキー
                    if str1 == "": #残りの文字列が無になったら一致とする．
                        find_flag = True
                        result1.append(elem1)
                        break #基本的に１対１の対応関係のはずなので１回見つけたらbreak
                i += 1
        if find_flag == False: #同じコメントが見つからなかったら
            result2.append(elem1)
        print find_flag
    
    return result1, result2
#delについて．．パッチ１の時点で存在するということはその時は削除されてない．
#パッチ２以降で削除＝レビューを経て削除ってことになるから，返り値の受け取り方は(RQ3, del_unless_review)
#addについて．．パッチ１の時点で存在するということはその時既に追加されてる．＝レビューありで
#なので返り値の受け方は(RQ5, RQ4)


#関数名classterとか書いてるけどclassifierの間違い.
#l_a_comments...最終パッチのa_comments / l_b_comments...最終パッチのb_comments
def rq34classter(l_a_comments, l_b_comments, proj_name, number): #comments, modeのがいいかも
    RQ3comments = []
    RQ4comments = []
    del_unless_review = []
    RQ5comments = []
    adder1 = []
    adder2 = []
    for comment in l_a_comments:
        f_code = []
        judge = False #パッチ１のデータを取れたかどうかの判定
        file_path = comment["pass"] #now_filenameでも可能
        url_key = url_encode(file_path)
        p = str(comment["patch"])
        path3 = dir_calc(proj_name, number) + str(p) + '_' + url_key + '.json'
        if comment["patch"] == 1: #パッチ総数１ならレビューなしで追加/削除されたSATDと言える
            judge = True #２つ下の条件文に引っかからないようにするため．
            
            if os.path.isfile(path3): #
                (f_code, judge) = code_reader(path3, 'b') #削除後のコードにもそのSATDと同じがあったら削除してないとみなす
                if judge == True: #
                    #(RQ3comments, del_unless_review) = rq34body(l_a_comments, f_code)
                    #(RQ5comments, RQ4comments) = rq34body(l_b_comments, f_code)
                    (adder1, adder2) = rq34body(comment, f_code)
                    #RQ3comments.extend(adder1)
                    del_unless_review.extend(adder2)
            else:
                raise FilenaiyoError #skippedの場合はRQ0で除けてるのでここには来ないはず
                    
                #f_a_comments = f_file["a_comments"]
                #f_b_comments = f_file["b_comments"]
        else: #if judge == False: #os.path.isfile(path3)をORに加えるべきかもしれないけど一旦保留．
            #print "patch1 is not exist"
            #1番目のパッチが存在しない場合はパッチ１では何も変わってないってこと．
            #なのでl_a_commentsをそのままRQ3comments,l_bをRQ4commentsに打ち込む．
            if os.path.isfile(path3): #patch2以降は変更前コードに同じ文言があるか否かで判断．
                #Q.この条件分岐いる？ ->ただのインデント変化の変更を「変化してない」とすることができる．
                (f_code, judge) = code_reader(path3, 'b')
                if judge == True: #l_a, l_bはそれぞれ複数のファイルのものが混じってるのでこのやり方じゃだめ
                    #(RQ3comments, del_unless_review) = rq34body(l_a_comments, f_code)
                    #(RQ5comments, RQ4comments) = rq34body(l_b_comments, f_code)
                    (adder1, adder2) = rq34body(comment, f_code)
                    RQ3comments.extend(adder2)
                    #del_unless_review.extend(adder2)
                #RQ3comments.append(comment)
                #RQ4comments = l_b_comments
            else:
                raise FilenaiyoError #skippedの場合はRQ0で除けてるのでここには来ないはず
    
    for comment in l_b_comments:
        f_code = []
        judge = False #パッチ１のデータを取れたかどうかの判定
        file_path = comment["pass"] #now_filenameでも可能
        p = str(comment["patch"])
        url_key = url_encode(file_path)
        path3 = dir_calc(proj_name, number) + str(p) + '_' + url_key + '.json'
        #ここで該当ファイルが存在するか否かでの場合分けが必要．
        #print path3
        if comment["patch"] == 1: #パッチ総数１ならレビューなしで追加/削除されたSATDと言える
            #del_unless_review.append(comment)
            #RQ5comments.append(comment)
            judge = True #２つ下の条件文に引っかからないようにするため．
            
            if os.path.isfile(path3):
                (f_code, judge) = code_reader(path3, 'a')
                if judge == True: #l_a, l_bはそれぞれ複数のファイルのものが混じってるのでこのやり方じゃだめ
                    #(RQ3comments, del_unless_review) = rq34body(l_a_comments, f_code)
                    #(RQ5comments, RQ4comments) = rq34body(l_b_comments, f_code)
                    (adder1, adder2) = rq34body(comment, f_code)
                    RQ5comments.extend(adder2) #返り値がリスト型なのでextendを使う
                    #RQ4comments.extend(adder2)
            else:
                raise FilenaiyoError
                #f_a_comments = f_file["a_comments"]
                #f_b_comments = f_file["b_comments"]
            
        else: #if judge == False: #1つ目の条件は抜いても同じだけど意味的に
            #print "patch1 is not exist"
            #1番目のパッチが存在しない場合はパッチ１では何も変わってないってこと．
            #なのでl_a_commentsをそのままRQ3comments,l_bをRQ4commentsに打ち込む．
            #RQ4comments.append(comment)
                
            if os.path.isfile(path3):
                (f_code, judge) = code_reader(path3, 'a')
                if judge == True: #l_a, l_bはそれぞれ複数のファイルのものが混じってるのでこのやり方じゃだめ
                    #(RQ3comments, del_unless_review) = rq34body(l_a_comments, f_code)
                    #(RQ5comments, RQ4comments) = rq34body(l_b_comments, f_code)
                    (adder1, adder2) = rq34body(comment, f_code)
                    #RQ5comments.extend(adder1) #返り値がリスト型なのでextendを使う
                    RQ4comments.extend(adder2)
            else:
                raise FilenaiyoError #skippedの場合はRQ0で除けてるのでここには来ないはず
    
    return RQ3comments, RQ4comments, del_unless_review, RQ5comments

    #それぞれ，"comment"keyの要素のみ抽出する
    #パッチ総数が１個だけの時の例外処理も作る？
    
#def remove_detect(sha, RQ4comments, RQ5comments):
    #sha = str, RQ4 = list, RQ5 = list
    
    
    
    
####################################################################################
####################################################################################

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

if len(sys.argv) >= 3: #プログラム名の後に引数があるなら(argvはプログラム名も数に含めている)
    argvs = sys.argv
    proj_name = argvs[1]
    sub_name = argvs[2]
    if len(sys.argv) >= 4:
        ignore = argvs[3] #引数に値が存在すれば，その分だけすでに終わってることにする
        ignore = int(ignore)
    else:
        ignore = 0
else:
    raise HikisuuNaiyoError

#number = ignore #number..現在見ているレビューidのこと．


if proj_name == "openstack":
    address = "review.opendev.org" #address..プロジェクトによる固有ドメイン
if proj_name == "qt":
    address = "codereview.qt-project.org"



#number = int(number) #文字列ー＞数値

with open('./dict/result_RQ0_' + sub_name + '.json', 'r') as g:
    json_dic = json.load(g)

list_count = 0 #進捗表示用変数
error_ids = [] #checkoutに失敗したIDを格納する．
    
'''
if ignore >= 1: #途中から始める時の処理
    path = './dict/temp_RQ0.json'
    with open(path, 'r') as h:
        temp_dict = json.load(h)
    error_ids = temp_dict["error_ids"]
'''
with open('./config/'+ sub_name +'.txt','r') as h:
    string = h.readline()
temp_list = string.split(' ')
langs = temp_list[2:]
if "c" in langs:
    langs.append("h")
if "cpp" in langs:
    langs.extend(["hpp", "cc", "cxx", "cp", "hxx"])
print langs

#コメント記述タイプについて
langtype1 = ["c", "h", "cc", "cpp", "cxx", "cp", "hpp", "hxx", "qml", "m", "mm", "java", "js", "frag", "vert", "g"] #c言語タイプ
langtype2 = ["py", "sh", "pro", "pl"] # pythonタイプ
#厳密にはsh,qmake(pro),plは複数行コメントアウトは存在しない
#shは一応<<任意の文字列〜任意の文字列で可能だが今は無視
langtype3 = ["vb", "vbs"] #visualbasicタイプ(シングルクォート
langtype4 = ["xq"] #xqueryタイプ (:  :)

#TODO list
#1.SATD_haveに含まれる各変更に対し，query.jsonを開いて"最後"のパッチの番号と変更のあったファイルを取得する．
#  その後ファイルそれぞれについて，
#2-1.diff_(最後のパッチ番号)_url.jsonを開き，a,b_commentsを取得する．
#2-2.diff_1_url.jsonを開き，a_comments,b_commentsを取得する．
#2-3.条件に合うSATDを抽出し，それぞれRQ3_url.json, RQ4_url.jsonに格納する．
#  全ての変更に対して行われたら，
#3.RQ3_url.json, RQ4_url.jsonを根こそぎ調べ，数を調べる．
#  csv形式で出力すべきか．
#他：パッチ数１の場合はスキップ．

#number...レビューナンバー
for number in json_dic["SATD_have"]:
    list_count += 1
    if int(number) < int(ignore): #途中から始めたいとき用
        continue
    skip_flag = False
    print "now number = " + str(number)
    print "now:" + str(list_count) +"/"+ str(len(json_dic["SATD_have"]))
    #先ずは全パッチ情報をゲットせよ．
    #パッチ総数をどうやってとるか？
    patch = 1
    #script = 'curl "https://'+ address +'/changes/?q=' + str(number) + '&o=CURRENT_REVISION"'
    #input = api_get(script)
    path = dir_calc(proj_name, number) + 'query.json'
    #with open(path, 'w') as f:
    #    f.write(input)
    with open(path, 'r') as h:
        #ここからjson->辞書形式で当該ファイルを読み込み
        dic = json.load(h)
    if not ("current_revision" in dic[0]):
        error_ids.append(number)
        print "skipped" #NEWかABANDONEDの場合はcurrentが存在しない． #ってわけでもないらしい
        continue
    x = dic[0]["current_revision"] #出力は長さ１のリストの中に辞書が入ってるので[0]必要。
    total_patch = dic[0]["revisions"][x]["_number"] #その変更のパッチ総数．
    total_patch = int(total_patch) #パッチ総数
    
    #if total_patch == 1: #パッチ数１の場合，全てレビューなしで削除・追加されたものとする．
    #    continue #####ここ変えなさい
    #パッチ１の場合も同じようにやればOKか？
    #patch = total_patch

    RQ3comments = []
    RQ4comments = []
    RQ5comments = [] #...add_unress_review
    del_unless_review = []
    l_a_comments = []
    l_b_comments = []
    while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
        
            #if skip_flag == True: #skipが出てたらもう調べようがないです
            #    break
            #print "now_patch:" + str(patch) + "/" + str(total_patch)
            #script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/files"'
            #input = api_get(script)
        path = dir_calc(proj_name, number) + 'diff_files_' + str(patch) + '.json'
        if not os.path.isfile(path): #暫定対応
            patch += 1
            continue
        with open(path, 'r') as h:
            #ここからjson->辞書形式で当該ファイルを読み込み
            l_dic = json.load(h)
        #各ファイルについてa,b_commentsをとって比較する．
        for key in l_dic.keys():
            lang_flag = False
            #print key
            if key == "/COMMIT_MSG":
                continue
            for la in langs:
                #print la
                if key.endswith(la): #サブプロジェクトに応じて変えるべき．forで．
                    lang_flag = True
                    lang = la
                    break
            if lang_flag == False: #言語が指定に一致しなかったら見ない
                continue
            url_key = url_encode(key)
            path2 = dir_calc(proj_name, number) + 'diff_' + str(patch) + '_' + url_key + '.json'
            if not os.path.exists(path2): #暫定対応
                print "no exist path"
                continue #本当にこれでOKか？コミットの結果最終的に全ての変更が破棄されたパターンもあるはず
                #->それなら最終パッチの変更リストに存在してないので大丈夫．
            with open(path2, 'r') as h: #SATDを保存しているファイルを呼び出す
                l_file = json.load(h)
                for com in l_file["a_comments"]:
                    com["patch"] = patch #何番目のパッチかについての情報がないので追加
                    #com["last_patch"] = patch #何パッチ目まで存在しているかをここへ保存する.RQ4で使う
                    #com["last_startline"] = 0 #最後に発見したパッチ内での開始行.RQ4で使う
                    #aの場合は基本は行は変化しないはずだし下２つは不要かな
                for com in l_file["b_comments"]:
                    com["patch"] = patch #何番目のパッチかについての情報がないので追加
                    com["total_patch"] = total_patch #last_patchと比較させる必要があるので
                    com["last_patch"] = patch #何パッチ目まで存在しているかをここへ保存する
                    com["last_startline"] = com["start_line"]
                l_a_comments += l_file["a_comments"] #ここでコメントリスト追加
                l_b_comments += l_file["b_comments"]
                #print l_file["a_comments"]
        patch += 1
                
                
    #パッチ毎の処理はここまで．
    #ここでl_a/b_commentsに入ったコメントから重複を抜かなきゃならない．
    l_a_comments = samecheck(l_a_comments, 'a')
    l_b_comments = samecheck(l_b_comments, 'b')
    
    #patch1なら全部レビューなしの方へ，patch1ファイルがないなら全部レビューありの方へ．
    #ここはSATD単位で処理する
    (RQ3comments, RQ4comments, del_unless_review, RQ5comments) = rq34classter(l_a_comments, l_b_comments, proj_name, number)
    
    #ここからRQの情報を取る
    #(RQ3comments, del_unless_review) =  sasyugo(l_a_comments, f_a_comments)
    #(RQ4comments, RQ5comments) = sasyugo(l_b_comments, f_b_comments)
    #RQ5comments = sekisyugo(l_b_comments, f_b_comments)
    #del_unless_review = sekisyugo(l_a_comments, f_a_comments)
    #行数と文字列距離の情報も取ったほうがいいか．それともdiffファイルで直接調べるのが得策？
    #行数取っても多分意味ない
    #改めてコメントを二つのファイルで抽出するというやり方もあるが時間的にあんまりやりたくない
    #ここから出力
    RQ34 = [{"RQ3comments":RQ3comments, "RQ4comments":RQ4comments, "RQ5comments":RQ5comments, "del_unless_review":del_unless_review}]
    #path4 = dir_calc(proj_name, number) + 'RQ34' + '_' + url_key + '.json' #old
    #全ファイル一気にとるようになったので保存ファイル変更
    path4 = dir_calc(proj_name, number) + 'RQ34_info.json'
    with open(path4, 'w') as h: #SATDを保存しているファイルを呼び出す
        json.dump(RQ34, h, sort_keys=True)
    #patch += 1
#もしかしたらunicode文字への変換処理が必要かもしれない．




#パッチの数の取り方．．currentで取ってjsonに変換した後に値を取得しカウントダウン式に取る？

#レビューコメントの取り方
#while patch <= total_patch: #各パッチについてコメントとレビューの情報を取る
    #script = 'curl "https://'+ address +'/changes/' + str(number) + '/revisions/' + str(patch) + '/comments"'
