

データ取得関連(RQに入る前に始めにやっておくもの)

・prepare.py
resultフォルダ内に変数now_endの値に応じてディレクトリを生成する．

・review_extract.py
APIにアクセスしてGerritからjsonデータを受け取り保存する．
主にどのレビュー番号がどのサブプロジェクトに紐付いているかを調べるのに使う．
第二引数はメインプロジェクト名．
基本は１からレビュー番号順に取るが第三引数に入力された値があればそこからスタートする．
これが完了してないと各RQを行えない．

・merge.py
下記の古いバージョン．まず使わない．->削除

・merge_v2.py
複数の「temp/proj_info_(number).json」の辞書情報を結合し，保存する．
番号は適宜変更の必要あり．


＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿


RQ0(SATDを含むコードレビューがどの程度存在するのか)関連
（ちなみにどのRQもReviewGetterディレクトリのシェルファイルから起動する前提で作ってる）

・RQ0.py
RQ0実働ファイル．追加で引数をメインプロジェクト名，サブプロジェクト名，
レビュー番号のスタート地点，終了地点（＋必要ならば途中から始めたいときのスタート地点）の順で要する．
具体的には全パッチの差分ファイルを根こそぎ取ってSATDを探って
該当するSATDコメントを重複除去しながら保存する．

・RQ0copy.py
novaだけデータ量がバカでかかったのでほぼコピペ．
エラーログとかが重複しないように部分的に変えてるので並列時にはそれぞれで行う必要があった...はず（うろ覚え）
->削除

・RQ0-2.py, RQ0part.py
多分古くてもう使わないので削除．RQ0part.pyは遠隔で分割して実行する時に使ってたけど今はもうRQ0.pyでもやれるはず
→削除

・RQ0part_retry.py
ほぼRQ0.pyと同じ．
ただしAPIへのアクセス部分を省略しているので，
一度取ったAPIデータをそのまま上書きせずにもう一度実行したいときに使う．

・RQ0solo.py
部分的にデータが欠損してた！という時に使う．特にパッチセットが数百もあるときとか．
追加で引数をメインプロジェクト名，サブプロジェクト名，レビュー番号，パッチ番号の順で要する．

・RQ0_random.py
dict/result_RQ0_(sub_name).jsonの[SATD_have]キー内の配列を
シャッフルするのが目的だったと思うんだけどもう使ってなさそうだし必要ない気もする．
出力はcsv/random_(sub_name).csv
->一応削除

・RQ0merge.py
引数にメインプロジェクト名，サブプロジェクト名が必要．
RQ0.pyとかが終わった後に使用する．
サブプロジェクト単位で実験結果をまとめる．
出力はdata/RQ0_(proj_name)_(sub_name).csv

・RQ0fullmerge.py
RQ0merge.pyを完了させているのが条件．
RQ0merge.pyでサブプロジェクトごとに出してた結果をまとめてメインプロジェクト単位で出力する．
結果はターミナル上に直接表示．
ついでにdata/RQ0_(proj_name).jsonを出力する．
このjsonファイルはSATDを含むレビューと含まないレビューの番号を保存しているため後のRQに使用するはず．

・RQ0mergeforRQ1.py
上とかと似てそうで少し違う．SATDコメントの「追加」があったもののみをまとめる．はず．
出力はdata/RQ0_addSATDnumbers_(proj_name)_(sub_name).csv
->旧RQ1は没になったので不要．削除．

・RQ0fullmergeforRQ1.py
上と同じ．メインプロジェクト単位．->こっちも削除


＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿
RQ1(SATDを埋め込んだ開発者はレビュー依頼時に自身でSATDがある旨を宣言しているのか)関連
RQ0が終わってることが大前提．もう基本的に使ってないか．

・RQ1.py
引数はメインプロジェクト必須．サブプロジェクトはあってもなくても．
RQ0の情報を目視調査しやすい形のcsvファイルとして出力する．->削除

・RQ1large.py
使ってない．->削除

＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿
RQ2(SATDを含むレビューの不採録率・修正回数)関連
前提：RQ0が終わってる必要あり
　　　（RQ0fullmerge.pyでdata/RQ0_(proj_name).jsonを出力しているのが条件のはず）

・RQ2.py
実働ファイルその１．
引数にはメイン，サブプロジェクト名（＋任意で始点番号，終点番号）を要する．
得られたデータはdata/result_RQ2_(sub_name).csvに随時書き込む．

・RQ2-2.py
実働ファイルその２．
RQ2とほぼやることは同じだがあっちがSATDの含まれるレビューを見ていたのに対し，
こっちはSATDの含まれてないレビューを見ているのが違い．
出力はdata/result_RQ2-2_(sub_name).csv

・RQ2checker.py
RQ2.py, RQ2-2.pyの完了が必要．
簡単な結果を見る．

・RQ2fullmerge.py
メインプロジェクト単位でまとめる．
サブプロジェクト全てのcsvを使う．
出力はRQanswers/RQ2_fullmerge_(proj_name).csv , RQanswers/RQ2-2_fullmerge_(proj_name).csv
重回帰分析の結果もついでに直接出力．

・RQ2cor.py
相関とか図とかを表示して欲しい時に使う．

＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿
RQ34(レビュー途中にSATDが削除・追加される割合および理由)関連
前提：RQ0が終わってる必要あり

・RQ34.py
調査を行う本体．
まずはこれを実行しないと下記を実行する意味がない

・self_checker.py
セルフレビューのレビュー番号をjsonで保存する．
出力はdata/self_review_(sub_name).json

・RQ34merge.py
レビュー依頼時/途中で削除/追加されたコメントの"数だけ"を出力する．
出力はdata/RQ34_(proj_name)_(sub_name).csv

・RQ34comshuffle.py
どんなSATDコメントがあるかをとりあえずみたいときにRQ34の内容を全部混ぜて出してたはず．
多分結果を出すのには使わないはず．->とりあえず削除
出力はcsv/comment_shuffle_(sub_name).csv

・RQ34fullmerge.py
下記RQ34fullmerge2.pyの旧版．セルフレビューを分けてないので意味ないと思う．→一応削除
出力はdata/RQ34_(proj_name).csv

・RQ34fullmerge2.py
サブプロジェクト毎の結果を統合する．
出力はRQanswers/RQ34_(proj_name)_perReview.csv

・RQ34fullshuffle.py
レビュー依頼時/途中で削除/追加されたコメントをグループ分けして出力する．
出力は
RQanswers/comment_shuffle_RQ3_(proj_name).csv <-レビュー途中で削除
RQanswers/comment_shuffle_RQ4_(proj_name).csv <-レビュー途中で追加
RQanswers/comment_shuffle_del_(proj_name).csv <-レビュー依頼時に削除
RQanswers/comment_shuffle_add_(proj_name).csv <-レビュー依頼時に追加
の４つ．


・comment_randommix.py
何に使ってたっけ．出力は
csv/result_RQ34_(sub_name).csv
csv/result_RQ3_comments_(sub_name).csv
csv/result_RQ4_comments_(sub_name).csv
csv/result_add_unreview_(sub_name).csv
の４つ．->多分結果に使ってないと思うので削除


＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿


RQ5(リプリケーション)関連
・RQ5.py
コメントを取ってきてremove_detect.plに渡す．
出力はdata/RQ5_(sub_name).csv , data/RQ5-2_(sub_name).csv．
前者がレビュー途中で追加されたSATD，後者がレビュー依頼時に追加されたSATDについて．

・remove_detect.pl
実際に調べる実働部隊．昔のプログラムを使いまわしてちょっと改造したもの．

・RQ5fullmerge.py
RQ5.pyの結果をメインプロジェクトごとにまとめる．
出力はRQanswers/RQ5_(proj_name).csv．
生存期間についてはRQ5_surv_times_(proj_name).csv, RQ5-2_surv_times_(proj_name).csv


