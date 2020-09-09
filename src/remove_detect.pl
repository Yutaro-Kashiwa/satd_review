use strict;
use warnings;
use Cwd;
use Time::Local 'timelocal';
use JSON;

#！！！１００１行目一時改造中！後で消す！！！
#idea:introduceの取り方をblameでなくSHAを使って日時情報を取るようにする．
#"git log [SHA] --pretty='format:%cd' --date=iso -n 1"ってコマンド．
#ハッシュの配列が欲しいなら「@%value」って感じかな．
#main..７１３行目〜

#元々の入力形式ー＞json．それぞれ辞書形式{}
#今回の入力形式ー＞sub_name, sha, path, start_line, comment,
#使うか怪しいけど今は一応なしで->end_line

my $DEBUG=1;
#test2
# project_name # proj_name is for one column of output
my ($project_name, $proj_name) = ($ARGV[0], $ARGV[0]);
$project_name =~ s/\//_/g;  # replace / -> _ in project_name

#our ($CWD_BRANCH, $BASE_BRANCH) = ($ARGV[1], $ARGV[1]); #使ってないぽいので凍結
our ($CWD_BRANCH, $BASE_BRANCH) = ("", "");
our $mode = $ARGV[1];

# delete *.diff and *.blame
my $sysname = `uname -s`;
my $option_xargs = "";
if ($sysname eq "Linux"){
    $option_xargs = "--no-run-if-empty";
}

#めちゃCPUに負荷かかるので凍結
#system("find . -name '*.diff' -print0 | xargs -0 $option_xargs rm");
#system("find . -name '*.blame' -print0 | xargs -0 $option_xargs rm");

# Read bug-fixing changes
#my $fname= $project_name . ".bug-fixing-changes"; #<-何故これでうまくいってたんだろう？
#my $fname= "input.txt";


####設定項目######################################################

our $base_dir = Cwd::getcwd(); #SATDgetディレクトリの場所
our $DIR_TARGET = $base_dir . "/DS/" . $proj_name;
my $OUT = "";
if ($mode eq "mode1"){
    $OUT = $base_dir . "/data/RQ5_" . $project_name . ".csv";
}
if ($mode eq "mode2"){
    $OUT = $base_dir . "/data/RQ5-2_" . $project_name . ".csv";
}



our $using_hash = "";

#our $fname = $base_dir . "/input_" . $project_name . ".txt"; #使うものに応じて帰ろ
#our $fname = $base_dir . "/comments/" . $project_name . ".txt"; #新しい方
our $fname = $base_dir . "/temp/sender_" . $project_name . ".json"; #新しい方


####設定ここまで###################################################

open(F_IN, $fname) or die ("File not found:" . Cwd::getcwd() . "/$fname\n");

#my $OUT =  $project_name . ".bug-inducing-changes";

open(F_OUT, ">>$OUT") or die ("Can't open file : $OUT\n");
#print F_OUT "PROJ,HASHID_FIX,HASHID_INDUCE,FILE,last_found,blame_LINE,COMMENT\n";
#print F_OUT "PROJ,Introduce_ID,Remove_ID,FILE,PASS,startLINE,endLINE,Intro_DATE,TIME,timediff,Remove_DATE,TIME,timediff,Intro_author,Remove_author,COMMENT,Last_found_id,survive,removed,same\n";

our %diffed_filelist=();
our %blamed_filelist=();
our @diff_lines = ();
our %diff_codes = ();
our %buginducing_commitid = ();
our %buginducing_commit_line_nums = ();
our %merge_commitid = ();

our $NEXT=100;

#our $blame_lines = 0; #181114 added.
our $true_induce = ""; #181114 added.
our $limit = 0; #for test

# file type for analysis
our $file_filter_mode = $ARGV[2]; # -E: Exclude  -I: Include
$file_filter_mode = "-I"; #181210 added.
#my @file_types = split(/,/,$ARGV[3]);
#our %file_types;
#$file_types{$_} = 1 for @file_types;

#if($file_filter_mode ne "-E" and $file_filter_mode ne "-I"){
#    print "[error] $file_filter_mode is not supported as filter mode\n";
#    print "   use -E : means exclude\n";
#    print "    or -I : means include\n";
#    exit (1);
#}

#if ($file_filter_mode eq "-I" and $ARGV[3] eq "'*'"){
    $file_filter_mode = "-A"; # all 
#}

my ($idx_proj, $idx_id, $idx_date, $idx_type, $idx_file) = (0, 1, 2, 3, 4);

sub readMergeCommitID {
    my $merge = $_[0];
    #fname,rev,committer_date,committer_name,comment,keyword exists?,number only?,bugids,numbers,refactor,add,del,author_date,author_name,changeid
    open (MERGE, $merge);
    while(my $line = <MERGE>){
        chomp($line);
        my @lines = split(/,/, $line);
        $merge_commitid{$lines[1]} = $lines[1];
    }
    close MERGE;
}

sub chgBranch {
    if($CWD_BRANCH ne $BASE_BRANCH){
        system("git checkout $BASE_BRANCH");
        $CWD_BRANCH = $BASE_BRANCH;
    }
}

sub makeDirForDiffFile{
    my $file = $_[0];    
    my $dir_name = "";

    if($file =~ /(.*)\/.*/){
        $dir_name = $1;
    }
    if ($dir_name ne ""){
        if (!(-e $dir_name)){
            print "   $file: mkdir -p '$dir_name'\n" if($DEBUG);
            system("mkdir -p '$dir_name'");
        }
    }
}

sub getNewFileNameFromRenamedFilePath{
    my $file = $_[0];

    if($file =~ /(.*){(.*) => (.*)}(.*)/){
        $file = $1 . $3 . $4;
    }

    if($file =~ /(.*) => (.*)/){
        $file = $2;
    }

    return $file;
}

sub getOldFileNameFromRenamedFilePath{
    my $file = $_[0];

    if($file =~ /(.*){(.*) => (.*)}(.*)/){
        $file = $1 . $2 . $4;
    }

    if($file =~ /(.*) => (.*)/){
        $file = $1;
    }

    return $file;
}

sub checkRenameFilePath{
    my $file = $_[0];
    my $old = "";
    my $new = "";

    print "[checkRenameFilePath]:\n   $file\n";

    if($file =~ /(.*){(.*) => (.*)}(.*)/){
        $old = $1 . $2 . $4;
        $new = $1 . $3 . $4;
        print "     $old\n";
        print "     $new\n";

        return $old . "=>" . $new;
    }

    if($file =~ /(.*) => (.*)/){
        $old = $1;
        $new = $2;
        print "     $old\n";
        print "     $new\n";

        return $old . "=>" . $new;
    }

    return $file;
}

sub checkCommentAndCosmeticChanges{
    my $line = $_[0];
    my $ext = $_[1];

    if ($ext eq "java" or $ext eq "c" or $ext eq "h" or $ext eq "cc" or $ext eq "cp" or $ext eq "cpp" or $ext eq "cxx" or $ext eq "hpp" or $ext eq "hxx"){
        if($line =~ /^-\s*\*/){
            return 1;
        }

        if($line =~ /^-\s*\/\//){
            return 1;
        }

        # */
        if($line =~ /^-\s*\/\*/){
            return 1;
        }

        # only }
        if($line =~ /^-\s*}\s*$/){
            return 1;
        }
    }

    if ($ext eq "java"){
        # only });
        if($line =~ /^-\s*}\);\s*$/){
            return 1;
        }

        # only };
        if($line =~ /^-\s*}\;\s*$/){
            return 1;
        }
    }

    if ($ext eq "te"){
        # start from #
        if($line =~ /^-\s*#/){
            return 1;
        }

        # only };
        if($line =~ /^-\s*\'\)/){
            return 1;
        }
    }

    if ($ext eq "py"){
        # start from #
        if($line =~ /^-\s*#/){
            return 1;
        }
    }

    return 0;
}

#sub checkTargetFile{
#    my $file = $_[0];
    
    # extension
#    my $ext = $file;

#    $ext =~ s/.*\.(.*)/$1/;
#    my $flag = 0;
#    chomp($ext);

    # Include Mode + asterisk
#    if($file_filter_mode eq "-A"){
#        $flag = 1;
    # Include Mode
#    }elsif($file_filter_mode eq "-I"){
#        if (defined $file_types{$ext}) {
#            $flag = 1;
#        }
    # Exclude Mode
#    }elsif($file_filter_mode eq "-E"){
#        if (!(defined $file_types{$ext})) {
#            $flag = 1;
#        }
#    }else{
#        print "[error] $file_filter_mode is not supported as filter mode\n";
#        return -1;
#    }

#   return $flag;
#}

sub getDiffLog {
    my $diff_name = $_[0];
    my $file = $_[1];
    my $sha = $_[2];
    my $rtn_syscall=0;

    my $newfilepath = "";
    my $oldfilepath = "";
    if ($file =~ /=>/){ # for rename
        $newfilepath = getNewFileNameFromRenamedFilePath($file);
        $oldfilepath = getOldFileNameFromRenamedFilePath($file);
    }

    ###############################################################
    # Get Diff LOG
    ###############################################################
    #my $diff_name = $files[$j] . ".diff";
    if(!defined($diffed_filelist{$diff_name})){
        ### Get Diff LOG
        # git log -p <filename> > GIT_HOME/<filename>.diff
        #my $script = "git log -p " . $files[$j] . " > " . $diff_name;

        my $dir_name = "";
        if ($newfilepath ne ""){ # for rename
            makeDirForDiffFile($newfilepath);
            makeDirForDiffFile($oldfilepath);
        }else{
            makeDirForDiffFile($file);
        }

        #@Yasu　change the commad for diff to use options for blank and white spaces
        #@Yasu add -- for safe (more time required)
        #git diff <sha>~..<sha> -w -b --ignore-space-at-eol --ignore-blank-lines -- tools/testcon/mainwindow.cpp
        my $script = "git diff " . $sha . "~.." . $sha . " -w -b  --ignore-space-at-eol --ignore-blank-lines -- '" . $file . "' > '" . $diff_name. "'";
        
        #@Yasu 2016/11/24 for renamed files
        if ($newfilepath ne ""){
            $script = "git diff " . $sha . "~.." . $sha . " -w -b  --ignore-space-at-eol --ignore-blank-lines -- '" . $oldfilepath . "' '" . $newfilepath . "' > '" . $diff_name . "'";    
        }

        $rtn_syscall = system($script);
        print "   diff_run $rtn_syscall:  $script\n" if($DEBUG);
        $diffed_filelist{$diff_name} = $rtn_syscall;
    }else{
        print "   reuse:  $diff_name\n" if($DEBUG);
    }

    return $rtn_syscall;
}

sub parseDiffLog {
    my $diff_name = $_[0];
    my $file = $_[1];
    my $sha = $_[2];
    my $rtn_syscall;

    my $newfilepath = "";
    my $oldfilepath = "";
    if ($file =~ /=>/){ # for rename
        $newfilepath = getNewFileNameFromRenamedFilePath($file);
        $oldfilepath = getOldFileNameFromRenamedFilePath($file);
    }

    open(F_DIFF, $diff_name) or die ("File not found:" . Cwd::getcwd() . "/$diff_name\n");
    my @diff = <F_DIFF>;

    # extension
    my $ext = $file;
    if ($file =~ /=>/){ # for rename
        $ext = $newfilepath;
    }
    $ext =~ s/.*\.(.*)/$1/;

    # for analysing diff log
    my $line=0;
    my $range=0;
    my $flag=0;
    
    for(my $k=0; $k <= $#diff; $k++){
        chomp($diff[$k]);
        
        # this file is just added
        if($diff[$k] =~/^new file mode \d*/){
            &chgBranch();
            return $NEXT;
        }

        # this file is just added
        if($diff[$k] =~/^deleted file mode \d*/){
            &chgBranch();
            return $NEXT;
        }

        if($diff[$k] =~/^@@ -(\d*),(\d*) \+\d*,\d* @@/){
            $line=$1 - 1;
            $range=$2;
            $flag=1; # we identify the line and range for analysis
            next;
        }

        # the line and range for analysis are not identified yet
        if ($flag != 1){
            next;
        }

        if($diff[$k] =~/^ /){
            $line = $line + 1;
            # print "      [diff:blank] $line: " . $diff[$k] . "\n" if($DEBUG);
            next;
        }

        #if($diff[$k] =~/^-.*\w/){              # this deleted line is the place of bug
        if($diff[$k] =~/^-.*\S/){               # to detect the pattern to delete ----------------------
            $line = $line + 1;

            my $flagComment = checkCommentAndCosmeticChanges($diff[$k], $ext);
            if ($flagComment == 1){
                print "      [comm] $line: " . $diff[$k] . "\n" if($DEBUG);
                next;
            }else{
                print "      [diff] $line: " . $diff[$k] . "\n" if($DEBUG);
                push(@diff_lines, $line);

                # to save actual code
                $diff[$k] =~ s/^\-//;
                $diff_codes{$line} = $diff[$k];
                next;
            }
        }

        if($diff[$k] =~/^-\s*/){               # skip only blank
            $line = $line + 1;
            next;
        }

        if($diff[$k] =~/^\+.*/){next;}            # skip if this line is just added

        print "      [WARNINGS][unclassified] $line: " . $diff[$k] . "\n" if($DEBUG);
    }
    close F_DIFF;
    
    if($#diff_lines < 0){
        print "   No deleted lines in this diff\n" if($DEBUG);
        &chgBranch();
        return $NEXT;
    }    

    return 0;
}

sub getBlameLOG {
    my $blame_name = $_[0];
    my $file = $_[1];
    my $sha = $_[2];
    my $rtn_syscall=0;

    my $prev_sha = $sha . "~";  

    my $newfilepath = "";
    my $oldfilepath = "";
    if ($file =~ /=>/){ # for rename
        $newfilepath = getNewFileNameFromRenamedFilePath($file);
        $oldfilepath = getOldFileNameFromRenamedFilePath($file);
    }

    if(!exists($blamed_filelist{$blame_name})){
        ### Get Blame LOG
        $blamed_filelist{$blame_name} = 1;
        my $script = "git blame $prev_sha -lsf -- '" . $file . "' > '" . $blame_name . "'";

        #@Yasu 2016/11/24 for renamed files
        if ($newfilepath ne ""){
            $script = "git blame $prev_sha -lsf -- '" . $oldfilepath . "' > '" . $blame_name . "'";
        }

        $rtn_syscall = system($script);
        print "   blame_run $rtn_syscall:  $script\n" if($DEBUG);
    }else{
        print "   reuse:  $blame_name\n" if($DEBUG);
    }

    return 0;
}

sub parseBlameLOG {
    my $blame_name = $_[0];
    my $file = $_[1];
    my $sha = $_[2];
    my $rtn_syscall;

    open(F_BLAME, $blame_name) or die ("File not found:" . Cwd::getcwd() . "/$blame_name\n");
    my @blame = <F_BLAME>;
    foreach my $diff_line (@diff_lines){
        if($blame[$diff_line-1] =~/^(.*?) /){
            my $bug_sha = $1;
            print "      $diff_line: " . $blame[$diff_line-1] if($DEBUG);

            # to confirm we analyze same code
            my $temp_diff_code = $diff_codes{$diff_line};
            my $temp_blame_code = $blame[$diff_line-1];
            # this regular expression can address two patterns:
            #   3fc515e77aa8a6bc3218dbd36b8ffbb9e7bf5b97 601)     message = _("Connection to swift failed") + ": %(reason)s"
            #   2daf95464f18e57edd0409413142f18b11a7745b cinder/rpc/impl_kombu.py                   85)     cfg.BoolOpt('rabbit_durable_queues',
            $temp_blame_code =~ s/^.*? \d*?\) (.*)/$1/;
            chomp($temp_blame_code);
            if ($temp_diff_code ne $temp_blame_code){
                print "      [WARNINGS] diff: $temp_diff_code\n";
                print "                blame: $temp_blame_code\n";
                return -1;
            }

            $temp_blame_code = $blame[$diff_line-1];
            $temp_blame_code =~ s/^.*? (.*?) *?\d*?\) .*/$1/;
            # checkFileTypeOfRenamedFile
            if (checkTargetFile($temp_blame_code) ne 1){
                print "    => [Skip]:" . $temp_blame_code . "\n"; 
                next;
            }
            
            #18/11/12:added
            $temp_blame_code = $blame[$diff_line-1];
            $temp_blame_code =~ s/^.*? .*? *?(\d*?)\) .*/$1/;
            chomp($temp_blame_code);
            if(!exists($buginducing_commit_line_nums{$bug_sha})){
                $buginducing_commit_line_nums{$bug_sha} = $temp_blame_code;
            }else{
                $buginducing_commit_line_nums{$bug_sha}.= " " . $temp_blame_code;
            }
            
            if(!exists($merge_commitid{$bug_sha})){
                $buginducing_commitid{$bug_sha} = 1;
            }else{
                # to treat merge conflict
                $buginducing_commitid{$bug_sha} = 1;
                print "      [merge] $file  $sha\n";
                print "         $diff_line: " . $blame[$diff_line-1];
                print "         " . $bug_sha . " is a merge commit, but should solve merge conflict!\n";
                # git diff 5e8ae0357^2..c47b04696a9d1dab04c4a59ed9ce4c28aa00fe98~ src/plugins/platforms/windows/qwindowswindow.cpp
            }
        }
    }
    close F_BLAME;

    return 0;
}

#181116:added. uses $id, $changed_file, $code_strs, $true_line
sub line_renewer{
    my $id = $_[0];
    my $changed_file = $_[1];
    my $code_strs = $_[2];
    my $true_line = $_[3];
    
    
    my $reader = $base_dir . "/data_logs/reader.txt";
    my $script = "git show " . $id . ':' . $changed_file . " > " . $reader;
    print $script . "\n";
    system($script); #実行
    #181115:file reader
    #print "code_strs = " . $code_strs . '| '; #for test
    my $count = 1;
    open(IN, $reader); #これちゃんと動く？
    while(<IN>){
        #print "read = " . $_ ;
        chomp($_);
        #if ($_ eq $code_strs){
        if($_ =~ /${code_strs}/){
            $true_line = $count;
            last;
        }
        if(eof(IN)){
            $true_line = 9999; #for meaning fail
            last;
        }
        $count++;
    }
    close(IN);
    return $true_line;
}

#181212:added.
sub getBlamedata{
    my $string = $_[0];
    my $openfile = $_[1];
    my $date = "";
    my $time = "";
    my $zisa = "";
    my $committer = "";
    my $code = ""; #その行に書いてあること
    
    print "bef_code=" . $string . "\n";
    #１個ずつ処理して消すバージョン．
    #if($sw == 1){
    #TODO:ここに「blame内容を取得させる」処理を追加したい．

    $string =~ /([0-9]{4}\-[0-9]{2}\-[0-9]{2})/; #match yyyy-mm-dd
    $date = $1; #日付取得
    $string =~ s/([0-9]{4}\-[0-9]{2}\-[0-9]{2})//;
    
    $string =~ /([0-9]{2}\:[0-9]{2}\:[0-9]{2})/; #match hh:mm:ss
    $time = $1;
    $string =~ s/([0-9]{2}\:[0-9]{2}\:[0-9]{2})//;
    
    $string =~ /(\+[0-9]{4}|\-[0-9]{4})/; #match +nnnn or -nnnn
    $zisa = $1;
    $string =~ s/(\+[0-9]{4}|\-[0-9]{4})//;
    
    #}
    
    #上のを一気にするならこっち
    #if($sw == 2){
    #    $string =~ /([0-9]{4}\-[0-9]{2}\-[0-9]{2}) ([0-9]{2}\:[0-9]{2}\:[0-9]{2}) (\+[0-9]{4}|\-[0-9]{4})/; # $1=date, $2=time, $3=zisa
    #my $date = $1;
    #my $time = $2;
    #my $zisa = $3;
    #<-ここで該当文字列消去
    #}
    
    $string =~ /\((.+)(\s{4}[0-9]+\)\s+)(.+)(\n)/; #match in ( ) （あってる自信がない）
    $committer = $1;
    $code = $3;
    print "aft_string=" . $string . "\n";
    print "aft_code=" . $code . "\n";
    $committer =~ s/\s+$//; #delete needless space
    
    return ($date, $time, $zisa, $committer, $code, $string);
}


#181116:added. for getting only comment.
#TODO: should be able to react /* */
sub comment_get{
    my $str = $_[0];
    if($str =~ /\s+\/\/|\/\/\s+|\/\*/){ #if have // or /* .
        $str = $& . $' ; #get match part and after part
    }
    elsif($str =~ /\*\//){ #if have */
        $str = $` . $& ; #get before part and match part
    }
    else{
        $str = "";
    }
    return $str;
}


sub get_unixtime{
    my $date = $_[0];
    my $time = $_[1];
    my $zisa = $_[2];
    my $unixtime = 0;
    
    my ($year, $month, $day) = split(/\-/, $date);
    my ($hour, $min, $sec) = split(/\:/, $time);
    #git上の時刻はタイムスタンプを考慮しているので逆算する必要がある．
    #直接時間を足したり引いたりすると２５時とかになってエラーするのでunixtimeに直接処理した方が良い．
    if($zisa =~ /\+/){
        $zisa =~ s/\+//;
        $zisa =~ s/00$//;
        #print $zisa . "\n";
        #$hour -= $zisa;
        $unixtime -= $zisa * 3600;
    }
    if($zisa =~ /\-/){
        $zisa =~ s/\-//;
        $zisa =~ s/00$//;
        #print $zisa . "\n";
        #$hour += $zisa;
        $unixtime += $zisa * 3600;
    }
    print $sec . "," . $min . "," . $hour . "," . $day . "," . $month . "," . $year . "\n";
    $unixtime += timelocal($sec, $min, $hour, $day, $month - 1, $year - 1900);
    
    print $unixtime . "\n";
    return $unixtime;
}

#181116:added. for conbine multi lines. uses @lines,
#sub conbine_lines{
#    my @lines = $_[0]; #リストを引数に取るときも$でいいの？
#     #if (隣接linesがあったら)→行の内容を結合(改行を挟むのも忘れずに)隣接行の後ろの方の番号を削除．
#     #returnは@linesでいいかな
#}
##################################################################################

    
########################################################################################
#先ずは入力のtxtファイルを読み込むところから．
#入力を読み，行数，パス，ファイル名，内容を得る．
#行数がダブる可能性を考慮すると辞書形式をとるのは得策ではなさそう．
#サブルーチンでできるのはせいぜい１行分のデータを返すくらいかな？　　追記：一旦ストップ
#sub reader{
#    my @list;
#
#}

########################################################################################
########################################################################################
########################################################################################
########################################################################################
my $address = ""; #基本的に$base_dir . "/blamelog.txt" とかを代入する.  後で実装．

my $sw = 1; #スイッチ
my $start_line = 0; #SATD行の始点
my $end_line = 0; #終点
my $date = ""; #result of blame
my $time = "";
my $zisa = "";
my $committer = "";
my $intro_pass = ""; #pass when SATD introduced.
my $date2 = ""; #result of blame reverse(= last_found)
my $time2 = "";
my $zisa2 = "";
my $committer2 = "";
my $last_found_id = "";
my $date3 = ""; #infomation about remove.
my $time3 = "";
my $zisa3 = "";
my $committer3 = "";
my $removed_id = "";
my $intro_unixtime = 0;
my $last_unixtime = 0;
my $read_unixtime = 0;
my $survive_time = 0;
my $has_removed = 0;
my $same_person = "";
my $pass = "";
my $code = "";
my $change_id = "";
my $data_num = 0;
my $succeed_num = 0;
my $errored_num = 0;

my $line_length = 0;

#my $merge = $project_name . ".git_all_merges";
#&readMergeCommitID($merge);

#$p = $proj_name; #正規表現への変数利用がうまくいかなかった時の代替策

#my $dummy = <F_IN>; #line 1 output.(not use)
chdir $DIR_TARGET;
print "changed dir to " . Cwd::getcwd . "\n";

our $input = "";
while (my $line = <F_IN>){ #これでいいのか？ #json読み込み
    $line =~ s/\\n/ /g; #jsonデコード関連でエラーが出る場合はここをコメントアウトしろ．
    $input = $input . $line; #先に全部読ませる．
}

#my $number = $ARGV[1];
#my $SHA = $ARGV[2];
#my $start_line = $ARGV[3];
#my $end_line = $ARGV[4];
#my $path = $ARGV[5];


#$input = $json_data; #jsonデータ作る

#print $input;
#my @comments = decode_json($input); #@%はダメぽい
#my $comments = decode('utf-8', encode_json($input));
my $comments = JSON->new()->decode($input);

#新データの保持情報
#comment, SHA, start_line, end_line, pass(SATDgetからの相対パス), proj_name

#&chgBranch();
#while(<F_IN>){ #要変更（リストにeachすることになるはず）
foreach my $var (@$comments){
    print "--------------------------------------------------------------\n";
    $data_num += 1;
    #!!!!まずはchange_idを用いてgit内でのSHAを導き出せ!!!!
    print "Sent_hash=" . $var->{SHA} . "\n";
    $change_id = $var->{change_id};
    #git logで検索をかける
    our $script = "";
    $script = "git log --oneline --pretty=format:%H --grep=" . $change_id;
    print $script . "\n";
    my $output = `$script`; #標準出力はバッククォートで
    print "True_hash=" . $output . "\n";
    #ここで２個以上の結果が引っかかったらどうする？ー＞ひとまず最初の１件を取るようにしよう
    my @sha_list = split(/\n/, $output);
    my $true_hash = $sha_list[0];
    $using_hash = $true_hash;
    if($true_hash eq ""){
        print "grep not found. Using normal hash.\n";
        $using_hash = $var->{SHA};
    }
    
    print "line:" . $var->{start_line} . '-' . $var->{end_line} . "\n"; #for debug

    $start_line = $var->{start_line};
    $end_line = $var->{end_line};
    
    my $line_length = $var->{start_line} - $var->{end_line} + 1;
    
    #print "bef_pass:" . $list[4] . "\n";
    print "bef_pass:" . $var->{pass} . "\n";
    
    

    #$proj_name = $var{"proj_name"}; #必要なら使え
    #$list[4] =~ s/\/$proj_name\///; #delete "/(project_name)/" (blame用の名前整形）
    $pass = $var->{pass};
    $pass =~ s/\.\/DS\/$proj_name\///; #delete "/(project_name)/" (blame用の名前整形）(新手法用）
    
    
    #print "aft_pass:" . $list[4] . "\n";
    print "aft_pass:" . $pass . "\n";
    
    
    #$using_hash = $var->{SHA};
    #181213:行数が１じゃない場合も今は頭の行($start_line)だけ取ることにする．
    #if($using_hash eq ""){ #こっちはまず使わない
    #    $script = "git blame -l -L " . $start_line . ',+1 ' . $list[4] . '/' . $list[3] . " > blamelog.txt"; #+0かも.TODO:そもそもここうまくいってないかも
    #}
    #else{
    #    $script = "git blame -l -L " . $start_line . ',+1 ' . $using_hash . ' -- ' . '"' . $list[4] . '/' . $list[3] . '"' .  " > blamelog.txt"; #過去のあるリビジョンから遡る場合はこちら．
    #}
    
    if($using_hash eq ""){ #こっちはまず使わない
        $script = "git blame -l -L " . $start_line . ',+1 ' . $pass . " > blamelog.txt"; #+0かも.TODO:そもそもここうまくいってないかも
    }
    else{
        $script = "git blame -l -L " . $start_line . ',+1 ' . $using_hash . ' -- ' . '"' . $pass . '"' .  " > blamelog.txt"; #過去のあるリビジョンから遡る場合はこちら．
    }
        
    print $script . "\n";
    eval{
        system($script) == 0 or die "hoge\n"; #
    };
    if($@){
        print "!!!!SHA not found!!!!\n";
        $errored_num += 1;
        next;
    }
    
    open(IN2, "blamelog.txt"); #このへんの処理もっと楽にできない？(string = system()としたり)
    my $string = <IN2>;
    #$string = ハッシュ名 (変更者 日付 時間 時差 行数) コメント内容となっている．
    #変更者は苗字と名前の間にスペースがあるので取得しづらいかも
    #->手法案1：()のうちから" 日付 時間 時差 行数"を消せば()の中身が人名だけになるので正規表現でそれをとって()を消す？
    #2：リストで撮ったものをそのまま結合する（＊姓名の間にスペースのないor２つある人物がいたらアウト＊）
    #3：リストを[0]から順に見ていって日付の正規表現にマッチしたところを日付とみなす
    #２行以上使用することになったらこのあたりの処理も少し変わると思う．
    close IN2;
    #blameの日付，時間，時差を取得．
    my $error_str = "fatal: bad object " . $using_hash . "\n";
    if($string eq $error_str){
        print "SHA not found!!!\n";
        next;
    }
    
    ($date, $time, $zisa, $committer, $code, $string) = &getBlamedata($string, "blamelog.txt");
    

    my $temp_print = $date . ', ' . $time . ', ' . $zisa . "\n"; #for debug
    print "temp print = " . $temp_print;
    print "string = " . $string;
    
    #$string =~ /\((.+)( \s*[0-9]+\))/; #match in ( ) （あってる自信がない）
    #my $committer = $1;
    #$committer =~ s/\s+$//; #delete needless space
    print $committer . "\n"; #for debug
    
    my @list2 = split(/ /, $string); #used only for getting commit_id
    my $intro_id = $list2[0];
    #
    
    my $blamed_line = $start_line;
    #uses $id, $changed_file, $code_strs, $true_line
    #my $fullpass = $list[4] . '/' . $list[3];
    my $fullpass = $pass;
    
    
    #blame時点でのファイル名が変化している場合はhashの直後にそのパスが出る．「(」が[1]になければそれはパスのはず．
    if($list2[1] !~ /^\(/){
        $intro_pass = $list2[1];
    }
    else{
        $intro_pass = $fullpass;
    }

    
    #$blamed_line = &line_renewer($intro_id, $fullpass, $list[2] , $blamed_line);
    $blamed_line = $start_line;
    if($blamed_line == 9999){
        $blamed_line = $start_line;
    }

    
    #ここから除去時期の特定を試みる．
    #まだ除去ID取ってない．
    #Q.導入時のファイル名が違った場合はどうする？ A.わざわざblame後のハッシュを使う必要はないと思うのですがそれは？
    #changed $intro_id -> $using_hash
    $script = "git blame -l -L " . $start_line . ',+1' . " --reverse " . $using_hash . " > blamelog2.txt"  . " -- " . '"' . $fullpass . '"';
    system($script);
    print "\n" . $script . "\n";
    open(IN3, "blamelog2.txt");
    $string = <IN3>;
    close IN3;
    print "output:" .  $string;
    ($date2, $time2, $zisa2, $committer2, $code, $string) = &getBlamedata($string, "blamelog2.txt");
    print $date2 . '/' . $time2 . '/' . $zisa2 . '/' . $committer2 . '/' . $string . '/' . "\n";
    
    @list2 = split(/ /, $string); #used only for getting commit_id
    $last_found_id = $list2[0];
    

        
    
    #このblame reverseで取れるハッシュは最後にあったものなので，除去を見つけるにはもう１つ後のハッシュを見る必要がある．
    #けどproj.git_hashでは検出できない．git logの--sinceと--reverseを使う手もあるがなんでか上手くいかない．
    #妥協案：git log -- $fullpass > changelog.txt; で全部取る．フォーマットで１行単位にするとなおよい．
    
    
    #my $time2_for_log =
    #$script = "git log --reverse " . $last_found_id . '^'; #これじゃ前の方を示すからだめ
    #9999個出力させてるけど減らしてもいい．
    $script = "git log --pretty='format:%H  %cd  %an' --date=iso --reverse -9999 -- " . '"' . $fullpass . '"' . " > changelog.txt";
    #%H=fullhash, %cd=commit_time, %an=author name. reverseなので出力は古い順に出る．スペース二つ区切り．
    #ちなみにcommitter nameは%cn
    system($script);
    print -s "changelog.txt";
    our $line_count = 0;

    open(IN_LOG, "changelog.txt");
    #ここから時間の比較．
    print "\n";
    print 'date1:';
    my $intro_unixtime = &get_unixtime($date, $time, $zisa);
    #if($intro_unixtime > 1459866400){ #先行研究のデータセット時のみ2016-04-05 14:26:40以降なら見ない．結果変わっちゃうもんね．
    #    next;
    #}
    print 'date2:';
    $last_unixtime = &get_unixtime($date2, $time2, $zisa2);
    print "nan\n";
    if($intro_unixtime > $last_unixtime){ #なんか変で除去手前のコミットが混入より前の時刻だった時．
        print "hoge";
        next;
        #$date2 = $date;
        #$time2 = $time;
        #$zisa2 = $zisa;
        #$last_unixtime = $intro_unixtime;
    }
    while(<IN_LOG>){
        $line_count = $line_count + 1;
        #print $_; #for test
        my @loglist = split(/  /, $_); #divide by double space. 0=hash, 1=day time tdiff, 2=commiter
        #ここでunix時間への変換を行った方が楽だと思う．
        ($date3, $time3, $zisa3) = split(/ /, $loglist[1]);
        if(($date eq $date3) and ($time eq $time3) and ($zisa eq $zisa3)){
            $committer = $loglist[2]; #blameはauthorでなくcommitterを取ってるかも．
            chomp($committer);
        }
        $read_unixtime = &get_unixtime($date3, $time3, $zisa3);
        #if($read_unixtime > 1459866400){ #先行研究のデータセット時のみ2016-04-05 14:26:40以降ならガン無視．
        #    $date3 = ""; #処理内容は下と同じ．
        #    $time3 = "";
        #    $zisa3 = "";
        #    $removed_id = "";
        #    $committer3 = "";
        #    $has_removed = 0;
        #    last;
        #}
        if($last_unixtime < $read_unixtime){
            $removed_id = $loglist[0];
            $committer3 = $loglist[2];
            chomp($committer3);
            $has_removed = 1;
            last;
        }
        if(eof){
            #$date3 = "2019-01-27"; #右打ち切り
            #$time3 = "15:40:00";
            #$zisa3 = "+0900";
            $date3 = "";
            $time3 = "";
            $zisa3 = "";
            $removed_id = "";
            $committer3 = "";
            $has_removed = 0;
            last;
        }
    }
    close IN_LOG;
    if ($line_count == 0){ #空ファイル用
        print "changelog is empty!\n";
        $date3 = "";
        $time3 = "";
        $zisa3 = "";
        $removed_id = "";
        $committer3 = "";
        $has_removed = 0;
    }
    
    if($date3 ne ""){
        $intro_unixtime = &get_unixtime($date, $time, $zisa);
        $survive_time = $read_unixtime - $intro_unixtime;
        $survive_time /= 86400; #sec -> day
        $survive_time = sprintf("%.2f", $survive_time);
    }
    else{
        $survive_time = "";
    }
    
    if($committer3 ne ""){
        if($committer eq $committer3){
            $same_person = "1";
        }
        else{
            $same_person = "0";
        }
    }
    else{
        $same_person = "0";
    }
    
    #my $file = $list[3];
    my $file = $var->{now_filename};
    #my $pass = $list[4];
    #my $passa = $pass; #passa ...passが被っちゃったので．でもこれ後ろで使ってないよね？
    #my $comment = $list[2];
    my $comment = $var->{comment}; #commentキーは実はプログラム中では使用していない．
    $comment =~ s/\"/\"\"/g; #" -> ""

    #our $find_id = $var->{SHA}; #後で消す

    #'","'って入力大丈夫なのかな・・・？要チェック．
    #正しくできてるか見るにはcinderの１６５行目あたりのコメント欄のズレをチェック．
    my $temp_out = $proj_name . "," . $intro_id . "," . $removed_id . "," . $file . "," . $intro_pass . ","  . $blamed_line . "," . $end_line . "," . $date . "," . $time . "," . $zisa . "," . $date3 . "," . $time3 . "," . $zisa3 . ',"' . $committer . '","' . $committer3 . '","' . $comment . '",' . $last_found_id . "," . $survive_time . "," . $has_removed . "," . $same_person . "\n";
    print F_OUT $temp_out;
    print "\n"; #for debug;
    $succeed_num += 1;
}

print '----------------------------------' . "\n";
print "data_num = " . $data_num . "\n";
print "succeed_num = " . $succeed_num . "\n";
print "errored_num = " . $errored_num . "\n";
print "end===============================\n";
###########################


close F_OUT;
close F_IN;
