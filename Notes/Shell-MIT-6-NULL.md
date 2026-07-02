[toc]

###  Shell

### MIT 6.NULL课程
https://missing.csail.mit.edu/ ，介绍了如何利用工具提升效率

#### Lecture1. Course overview + the shell
* shell：空格分割输入，`~` is short for "home"，`.`表示当前文件夹
  * `.`在UNIX系统的[遗留问题](https://plus.google.com/101960720994009339267/posts/R58WgWwN9jp)
* environment variable: `echo $PATH`; `vim ~/.zshrc`
  * `$PATH`可以作为输入
* connecting programs：
  * <和>：rewire the input and output streams; >>可append
  * `cat < hello.txt > hello2.txt`
  * wire: `ls -l | tail -n1`，``
  * `curl --head --silent baidu.com | grep --ignore-case content-length | cut -f2 -d ' '`
* sudo: super user，linux系统可改/sys下面的sysfs

`echo 1 | sudo tee /sys/class/leds/input6::scrolllock/brightness`

* [shell中不同类型quotes的含义](https://www.gnu.org/software/bash/manual/html_node/Quoting.html)

#### Lecture2. Shell Tools and Scripting
##### shell scripting
* foo=bar, \$foo	注意等号前后不能有space，否则被当成参数
* 单引号和双引号的区别：同样套在\$foo上，前者是literal meaning，而" "会替换成变量值
* shell scripting也有if、case、while、for、function特性
  * source mcd.sh后即可使用。cd如果在function内部使用，针对的是子shell，不影响外部，因此直接用./mcd.sh不合适
```shell
#!/bin/bash
mcd(){
	mkdir -p "$1"
	cd "$1"
}
```
  * if else
  * for特性的实用例子
```shell
POLICIES=("FIFO" "LRU" "OPT" "UNOPT" "RAND" "CLOCK")
for policy in "${POLICIES[@]}"
do
    for i in 1 2 3 4
    do
        ./paging-policy.py -c -f ./vpn.txt -p "$policy" -C "$i"
    done
    echo ""
done
```

* case-esac 语句的使用

```shell
while [ "$#" -gt 0 ]; do
    case $1 in
    -c | --clang)
        clang=1
        ;;
    -g | --gcc)
        gcc=1
        ;;
    --lto)
        lto=1
        ;;
    --thinlto)
        thinlto=1
        ;;
    esac
    shift
done
```

* `set -e`：遇到错误，shell script 直接退出
* `shift`: 含义是 `$0` 不移动，将 `$1` 起始的若干参数干掉 

##### special variables

  * `$0` - Name of the script
  * `$1 to \$9` - Arguments to the script. $1 is the first argument and so on.
  * `$@` - All the arguments
      * `$*` 同义，[区别是它在“”包围下会当成一个参数](http://c.biancheng.net/view/807.html)
  * `$#` - Number of arguments
      * 最后一个参数：`${!#}`
  * `$?` - Return code of the previous command
  * `$$` - Process Identification number for the current script
  * `!!` - Entire last command, including arguments. A common pattern is to execute a command only for it to fail due to missing permissions, then you can quickly execute it with sudo by doing sudo !!
  * `$_` - Last argument from the last command. If you are in an interactive shell, you can also quickly get this value by typing Esc followed by .
  * `$!` - last backgrounded job
* ||和&& operator：机制和 error code 联系，true 和 false 命令返回固定的error code
  * [linux中，&和&&, |和|| ,&> 与 >的区别](https://blog.csdn.net/sunfengye/article/details/78973831)
  * `false || sleep 10s` 固定error code为零
```shell
false || echo "Oops, fail"
# Oops, fail

true || echo "Will not be printed"
#

true && echo "Things went well"
# Things went well

false && echo "Will not be printed"
#

false ; echo "This will always run"
# This will always run

```

##### [shell中 ${}, ##, %%, :- , :+,  ? 的使用](https://blog.csdn.net/qq_43193797/article/details/90906007)

```shell
percent=${PERCENT:-50}
```

##### [Linux-shell中各种替换的辨析](https://www.cnblogs.com/chengd/p/7803664.html)

* variable substitution：`$var, ${var}`
* command substitution: `for file in $(ls)`，可以用`' '`代替`$( )`，但后者辨识度更高
* process substitution: 生成返回temporary file，`diff <(ls foo) <(ls bar)`

```shell
#!/bin/bash

echo "Starting program at $(date)" # Date will be substituted

echo "Running program $0 with $# arguments with pid $$"

for file in $@; do
    grep foobar $file > /dev/null 2> /dev/null
    # When pattern is not found, grep has exit status 1
    # We redirect STDOUT and STDERR to a null register since we do not care about them
    if [[ $? -ne 0 ]]; then
        echo "File $file does not have any foobar, adding one"
        echo "# foobar" >> "$file"
    fi
done

```
* 2>，重定向 stderr
* &> 或 >&，重定向到 stderr
  * `&>word` <=> `>word 2>&1`
  * `$command > result 2>&1`，STDOUT、STDERR 均重定向到 result
* `-ne`，更多的查看man test，比如`-n 文件存在为真 -z 不存在为真`
* “test command”， \[\[和\[的区别：http://mywiki.wooledge.org/BashFAQ/031 ，`[[`是compound command，存在special parsing context，寻找reserved words or control operators 
  * `if [[ -e $file ]] && [[ $var == true]] `
* `--`
  *  to signify the end of command options
  * `grep -- -v file`
  

##### shell globbing 通配
* wildcard通配符：?和* 	`ls *.sh`
* {}: `mv *{.py,.sh} folder`, `mv abc{000..120}* folder`
* `touch {foo,bar}/{a..h}`

* 利用[shellcheck](https://github.com/koalaman/shellcheck)检查shell scripts的错误

* [shebang](https://en.wikipedia.org/wiki/Shebang_(Unix))line 进行解释，可以利用env命令
  * `#!/usr/bin/env python`
  * ` #!/usr/bin/env -S /usr/local/bin/php -n -q -dsafe_mode=0`

##### shell 引号嵌套

https://zhuanlan.zhihu.com/p/146462733

最简单的方法就是单双引号交替

##### shell中的容错：set -e、trap

```shell
set -e
function cleanup {{
	rm ...;
}}
trap cleanup EXIT SIGKILL
```

**shell函数和scripts的区别：**

- Functions have to be in the same language as the shell, while  scripts can be written in any language. This is why including a shebang  for scripts is important.
- Functions are loaded once when their definition is read. Scripts  are loaded every time they are executed. This makes functions slightly  faster to load but whenever you change them you will have to reload  their definition.
- Functions are executed in the current shell environment whereas  scripts execute in their own process. Thus, functions can modify environment variables, e.g. change your current directory, whereas scripts can’t. Scripts will be passed by value environment variables  that have been exported using [`export`](http://man7.org/linux/man-pages/man1/export.1p.html)
  * 比如cd只能在function中影响到外界shell
- As with any programming language functions are a powerful  construct to achieve modularity, code reuse and clarity of shell code.  Often shell scripts will include their own function definitions.

##### 实用技巧

* `alias ll='ls -aGhlt'`

* marco记录directory，polo前往

```shell
#!/bin/bash
marco(){
        foo=$(pwd)
        export MARCO=$foo
}
polo(){
        cd "$MARCO" || echo "cd error"
}
```

* 实用小工具，比如可以抢实验室GPU（实现的功能相对原题有改动）
  * 简化版：`mycount=0; while (( $mycount < 15 )); do ./my_script;((mycount=$mycount+1)); done;`


```shell
#!/usr/bin/env bash
debug(){
        echo "start capture the program failure log"
        cnt=-1
        ret=0
        while [[ $ret -eq 0 ]]; do
                sh "$1" 2>&1
                ret=$?
                cnt=$((cnt+1))
                # let cnt++
                if [[ $# -eq 2 ]];then
                        sleep "$2"
                fi
        done
        echo "succeed after ${cnt} times"
}
```

* import envs from main process

  * `. <(xargs -0 bash -c 'printf "export %q\n" "$@"' -- < /proc/${MAIN_PID}/environ)`
    * [关于`%q`](https://github.com/progrium/bashstyle/issues/20#issuecomment-68955878)，"causes printf to output the corresponding argument in a format that can be reused as shell input"
      * Prints `''` for the null/empty string.
      * Prints the string normally if it has no spaces, using backslashes to escape shell-recognized characters like quotes or semicolons.
      * Prints the string in single-quotes ("shell quoting") if it has spaces, using `'\''` to escape single-quotes.
      * Prints the string in a `$'...'` "ANSI C" style string, with backslashed-escaped command sequences, if it has special/non-printing characters like newlines.

##### shell tools

**帮助文档**

* XX -h
* man XX
* :help 或 ? (interactive)
* [tldr](https://tldr.sh/)：比man好用！

**shell中的查找**

* 查找文件：find, fd, locate，见底部命令解释
* 查找代码：见【code-reading】笔记
* 查找shell指令

	* `history | grep find`
  
  * Ctrl-r，可结合[fzf](https://github.com/junegunn/fzf/wiki/Configuring-shell-key-bindings#ctrl-r)，[教程](https://www.jianshu.com/p/d64553a37d69)：高效查找，手动选择
  
  * [zsh-history-substring-search](https://github.com/zsh-users/zsh-history-substring-search): 键盘上下键寻找历史
  
  * [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions)：键盘右键快速键入
  * 如果输入命令有leading space，不会记入历史数据；如果不慎记入，可修改`.bash_history`或`.zsh_history`
  
* 查找目录
  * [fasd](https://github.com/clvv/fasd): 用[frecency](https://developer.mozilla.org/en/The_Places_frecency_algorithm)(frequency+recency)这个指标排序，这一指标最早用于火狐浏览器
  * [autojump](https://www.baidu.com/link?url=mmPr58MUREjyOpep_Bjba3FyOvqmlUlHSjwpit3kmUPWMWCrvvrUjx1-MKzWeBCsFBiJoXKF-A3Qk23C07rCTa&wd=&eqid=c4204f66000031cb000000065ebf6b15)
  * More complex tools exist to quickly get an overview of a directory structure [`tree`](https://linux.die.net/man/1/tree), [`broot`](https://github.com/Canop/broot) or even full fledged file managers like [`nnn`](https://github.com/jarun/nnn) or [`ranger`](https://github.com/ranger/ranger)

* Shell编辑

  * `Ctrl-a`光标移动到行前

  * ESC进入Vim-mode，ESC-v进入Vim直接编辑

##### Shell 终端

*   iTerm2: macOS 下的终端神器，高度可定制，支持分屏、自定义配色、快捷键等。
*   MobaXterm: Windows 下的强大终端，内置 X11 server，支持 SSH, FTP, MOSH 等多种远程协议，并且有图形化的文件传输界面。

##### zsh
* [oh-my-zsh](https://github.com/ohmyzsh/ohmyzsh)
* [zsh的10个优点](https://blog.csdn.net/rapheler/article/details/51505003)，[zsh介绍](https://www.cnblogs.com/dhcn/p/11666845.html)
* [MacOS配置iTerm2+zsh+powerline](https://www.jianshu.com/p/2e8c340c9496)
* autojump: j, jc, jo, jco, j A B
* [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions)
* [zsh-history-substring-search](https://github.com/zsh-users/zsh-history-substring-search)
* [zsh-completions](https://github.com/zsh-users/zsh-completions): tab自动补全，比如输cd按tab会自动识别文件夹；输git add会自动识别需要add的文件

Aliases
* pyfind
* pyclean [dirs]
* pygrep \<text\> 

#### Lecture3. Editors(Vim)
* [我的Vim笔记](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Output/Vim.md)

#### Lecture 4.Data Wrangling

**What are other useful data wrangling tools?**

Some of the data wrangling tools we did not have time to cover during the data wrangling lecture include `jq` or `pup` which are specialized parsers for JSON and HTML data respectively. The  Perl programming language is another good tool for more advanced data  wrangling pipelines. Another trick is the `column -t` command that can be used to convert whitespace text (not necessarily aligned) into properly column aligned text.

More generally a couple of more unconventional data wrangling tools  are vim and Python. For some complex and multi-line transformations, vim macros can be a quite invaluable tools to use. You can just record a  series of actions and repeat them as many times as you want, for  instance in the editors [lecture notes](https://missing.csail.mit.edu/2020/editors/#macros) (and last year’s [video](https://missing.csail.mit.edu/2019/editors/)) there is an example of converting a XML-formatted file into JSON just using vim macros.

For tabular data, often presented in CSVs, the [pandas](https://pandas.pydata.org/) Python library is a great tool. Not only because it makes it quite easy to define complex operations like group by, join or filters; but also  makes it quite easy to plot different properties of your data. It also  supports exporting to many table formats including XLS, HTML or LaTeX.  Alternatively the R programming language (an arguably [bad](http://arrgh.tim-smith.us/) programming language) has lots of functionality for computing  statistics over data and can be quite useful as the last step of your  pipeline. [ggplot2](https://ggplot2.tidyverse.org/) is a great plotting library in R.

#### Lecture 5.Command-line Environment

##### PTY：终端、shell 和 job control 的边界

参考：[pty(7)](https://man7.org/linux/man-pages/man7/pty.7.html)、[Bash Job Control Basics](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Basics.html)、[tcsetpgrp(3)](https://man7.org/linux/man-pages/man3/tcsetpgrp.3.html)。

* PTY（pseudo-terminal）不是 shell，而是一对虚拟字符设备：master 端由终端模拟器、SSH、tmux、expect、script 等控制；slave 端表现得像真实终端，通常成为 bash / 程序的 `stdin/stdout/stderr`。

```text
键盘/窗口/SSH client/tmux pane
  -> PTY master
  -> kernel tty line discipline / termios
  -> PTY slave (/dev/pts/N)
  -> bash/readline/前台程序
```

* shell job control 依赖三层对象：
  * session：一次登录或交互会话的进程集合，通常由登录 shell 作为 session leader。
  * process group：一个 pipeline 通常被 bash 放进同一个进程组，也就是一个 job。
  * controlling terminal：session 绑定的终端。终端里只有一个 foreground process group；`Ctrl-C` / `Ctrl-Z` 由内核终端驱动发给这个前台进程组，而不是只发给某个 PID。
* `fg/bg/jobs` 的本质：bash 维护 job 表，并通过 `setpgid()` 划分 job、通过 `tcsetpgrp()` 把某个 job 的进程组切到终端前台。后台 job 读 controlling terminal 会收到 `SIGTTIN`；如果设置了 `stty tostop`，后台写终端也可能被 `SIGTTOU` 挂起。
* pipe / redirect 只是字节流，不提供终端语义；PTY = 字节流 + 终端驱动 + termios 模式 + foreground process group + 窗口尺寸等状态。所以很多交互程序会用 `isatty()` 判断自己是否连着终端。
* 常见现象：
  * `bash -c`、普通脚本、CI、管道里默认没有 interactive job control；如果没有 controlling terminal 或不在前台，会看到 `cannot set terminal process group` / `no job control in this shell`。
  * `ssh -t`、`docker exec -it`、`kubectl exec -it` 的 `-t` 就是在远端/容器侧分配 PTY；没有 `-t` 时适合跑非交互命令，但全屏 UI、readline、密码输入、`Ctrl-C` 语义可能不完整。
  * tmux/screen 是 PTY broker：外层连接一个终端，内部每个 pane 再给 shell 一个 `/dev/pts/N`。detach 后 shell 不随外层终端关闭，是因为会话由 tmux server 持有。

##### Job Control
杀进程
* signals: software interrupts

* `Ctrl-C`:`SIGINT`; `Ctrl-\`:`SIGQUIT`; `kill -TERM PID` :`SIGTERM`
* [SIGINT、SIGQUIT、 SIGTERM、SIGSTOP区别](https://blog.csdn.net/pmt123456/article/details/53544295)

```python
#!/usr/bin/env python
import signal, time

def handler(signum, time):
    print("\nI got a SIGINT, but I am not stopping")

signal.signal(signal.SIGINT, handler)
i = 0
while True:
    time.sleep(.1)
    print("\r{}".format(i), end="")
    i += 1
```

**Pausing and backgrounding processes**

* 暂停并放入后台：`Ctrl-Z`,`SIGTSTP`
* 继续暂停的job：`fg和bg`；`jobs`搭配`pgrep`
* `$!` - last backgrounded job
* 命令行后缀`&`在背景运行命令
* 关闭终端发出`SIGHUP`信号，使子进程终止，解决方案：
  1. 运行前`nohup` 
  2. 运行后`disown` 
  3. `tmux`
* `SIGKILL`和`SIGSTOP`都不能被相关的系统调用阻塞，因此`SIGKILL`不会触发父进程的清理部分，可能导致子进程成为孤儿进程；如果是`SIGINT`，可能会有handler处理资源，比如有些数据还在内存，需要刷新到磁盘上。

##### tmux: terminal multiplexer

基于我的键位（[配置文件](https://github.com/huangrt01/dotfiles/blob/master/tmux.conf)）

- Sessions - a session is an independent workspace with one or more windows    

  - `tmux` starts a new session.
  - `tmux new -s NAME` starts it with that name. `tmux rename-session -t 0 database` 重命名
  - `tmux ls` lists the current sessions
  - Within `tmux` typing `<C-a> d/D`  detaches the current session
  - `tmux a` attaches the last session. You can use `-t` flag to specify which

- Windows

   \- Equivalent to tabs in editors or browsers, they are visually separate parts of the same session    

  - `<C-a> c` Creates a new window. To close it you can just terminate the shells doing `<C-d> / exit`
  - `<C-a> N` Go to the *N* th window. Note they are numbered
  - `<C-a> p` Goes to the previous window
  - `<C-a> n` Goes to the next window
  - `<C-a> ,` Rename the current window
  - `<C-a> w` List current windows

- Panes

   \- Like vim splits, panes let you have multiple shells in the same visual display.    
  - 配置下可以用鼠标选取/缩放pane
  - `<C-a> -` Split the current pane horizontally
  - `<C-a> |` Split the current pane vertically
  - `<Alt> <direction>` Move to the pane in the specified *direction*. Direction here means arrow keys.
  - `<C-a> z` make a pane go full screen. Hit `<C-a> z` again to shrink it back to its previous size
  - `<C-a> [` Start scrollback. You can then press `<space>` to start a selection and `enter` to copy that selection.
  - `<C-a> <space> ` Cycle through pane arrangements.

* 其它操作
  * `<C-a> r ` reload配置文件
  * `Shift + Command + c`，配合iTerm2复制文件

* For further reading, [here](https://www.hamvocke.com/blog/a-quick-and-easy-guide-to-tmux/) is a quick tutorial on `tmux` and [this](http://linuxcommand.org/lc3_adv_termmux.php) has a more detailed explanation that covers the original `screen` command. You might also want to familiarize yourself with [`screen`](http://man7.org/linux/man-pages/man1/screen.1.html), since it comes installed in most UNIX systems.
* tmux是client-server的实现模式
* [tmux customizations](https://www.hamvocke.com/blog/a-guide-to-customizing-your-tmux-conf/)

##### Aliases
* `alias ll`可print出alias的对象
* `unalias ll`可解除alias
```shell
# alias base
alias v='vim'
alias ll='ls -aGhlt'
alias la='ls -a'
alias l='ls -CF'
alias cls='clear'

alias gs='git status'
alias gc='git commit'
alias gqa='git add .'

alias v="vim"
alias mv="mv -i" # -i prompts before overwrite
alias mkdir="mkdir -p" # -p make parent dirs as needed
alias df="df -h" # -h prints human readable format

alias vfzf='vim $(fzf)' #vim打开搜索到的结果文件
alias cdfzf='cd $(find * -type d | fzf)'
alias gitfzf='git checkout $(git branch -r | fzf)'


# alias docker
alias dkst="docker stats"
alias dkps="docker ps"
alias dklog="docker logs"
alias dkpsa="docker ps -a"
alias dkimgs="docker images"
alias dkcpup="docker-compose up -d"
alias dkcpdown="docker-compose down"
alias dkcpstart="docker-compose start"
alias dkcpstop="docker-compose stop"

```

##### Dotfiles
* [Anish: 很详尽的tutorial](https://www.anishathalye.com/2014/08/03/managing-your-dotfiles/)
* [有关dotfile的种种](https://dotfiles.github.io/)
* [shell-startup的机理](https://blog.flowblok.id.au/2013-02/shell-startup-scripts.html)

e.g.
- `bash` - `~/.bashrc`, `~/.bash_profile`
- `git` - `~/.gitconfig`
- `vim` - `~/.vimrc` and the `~/.vim` folder
- `ssh` - `~/.ssh/config`
- `tmux` - `~/.tmux.conf`

管理方法：单独的文件夹，版本控制，**symlinked** into place using a script
  * 用git的submodule
  * [Dotbot](https://github.com/anishathalye/dotbot) 

* **Easy installation**: if you log in to a new machine, applying your customizations will only take a minute.
* **Portability**: your tools will work the same way everywhere.
* **Synchronization**: you can update your dotfiles anywhere and keep them all in sync.
* **Change tracking**: you’re probably going to be maintaining your dotfiles for your entire programming career, and version history is nice to have for long-lived projects.

一些有用的构造代码块：
```shell
# $HOME/dotfiles
BASEDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(uname)" == "Linux" ]]; then {do_something}; fi

# Check before using shell-specific features
if [[ "$SHELL" == "zsh" ]]; then {do_something}; fi

# You can also make it machine-specific
if [[ "$(hostname)" == "myServer" ]]; then {do_something}; fi

# Test if ~/.aliases exists and source it
if [ -f ~/.aliases ]; then
    source ~/.aliases
fi
```

在`~/.gitconfig`里加

```
[include]
    path = ~/.gitconfig_local
```

##### Remote Machines
* [装虚拟机](https://hibbard.eu/install-ubuntu-virtual-box/)
  * `sudo apt-get install --reinstall lightdm && sudo systemctl start lightdm`图形界面
  * `Ctrl+Alt+A`打开终端
  * 自动/手动设置共享文件夹：`sudo mkdir -p /media/sf_<FolderName> && 
  sudo mount -t vboxsf -o rw,gid=vboxsf FolderName /media/sf_FolderName `
* ssh可执行命令
  * `ssh foobar@server ls | grep PATTERN` 
  * `ls | ssh foobar@server grep PATTERN`
* [用SSH连GitHub](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)
```shell
ssh-keygen -t rsa -b 4096 -C "huangrt01@163.com"
eval "$(ssh-agent -s)"
ssh-add -K ~/.ssh/id_rsa
pbcopy < ~/.ssh/id_rsa.pub  #适合MacOS , Linux用xclip
# 上github添加SSH Key

ssh -T git@github.com

ssh-keygen -y -f ~/.ssh/id_rsa
```
* [ssh agent及其forwarding特性](https://www.ssh.com/ssh/agent#ssh-agent-forwarding)
* ssh连虚拟机
```shell
ssh -p 2222 cs144@localhost
# ssh will look into .ssh/authorized_keys to determine which clients it should let in.
ssh-copy-id -i ~/.ssh/id_rsa.pub -p 2222 cs144@localhost
# or
cat .ssh/id_ed25519.pub | ssh foobar@remote 'cat >> ~/.ssh/authorized_keys'
```
* ssh传文件
  - `ssh+tee`, the simplest is to use `ssh` command execution and STDIN input by doing `cat localfile | ssh remote_server 'tee serverfile'`. Recall that [`tee`](http://man7.org/linux/man-pages/man1/tee.1.html) writes the output from STDIN into a file.
  - [`scp`](http://man7.org/linux/man-pages/man1/scp.1.html) when copying large amounts of files/directories, the secure copy `scp` command is more convenient since it can easily recurse over paths. The syntax is `scp -P 2075 -r path/to/local_file remote_host:path/to/remote_file`
  - [`rsync`](http://man7.org/linux/man-pages/man1/rsync.1.html) improves upon `scp` by detecting identical files in local and remote, and preventing  copying them again. It also provides more fine grained control over  symlinks, permissions and has extra features like the `--partial` flag that can resume from a previously interrupted copy. `rsync` has a similar syntax to `scp`.
* Port Forwarding: `localhost:PORT or 127.0.0.1:PORT`
  * Local Port Forwarding: ssh端口重定向：`-L 9999:127.0.0.1:8097，比如在服务器开`jupyter notebook`
    * <img src="Shell-MIT-6-NULL/001.png" alt="Local Port Forwarding" style="zoom:100%;" />
  * Remote Port Forwarding
    * <img src="Shell-MIT-6-NULL/002.png" alt="Remote Port Forwarding" style="zoom:100%;" />
* `ssh -K`: 穿越服务器，打开GSSAPIDelegateCredentials, 可转存tgt
* ssh configuration: `~/.ssh/config`，server side: `/etc/ssh/sshd_config`，调端口、X11 forwarding等
```shell
Host vm
    User foobar
    HostName 172.16.174.141
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    LocalForward 9999 localhost:8888

# Configs can also take wildcards
Host *.mit.edu
    User foobaz
```

* 其它
  * openconnect: `sudo openconnect --juniper  https://sslvpn.tsinghua.edu.cn -u 2015010356` 
  
  * vscode remote-ssh中[ssh_config的配置细节](https://linux.die.net/man/5/ssh_config) 
  
  * [Mosh](https://mosh.org/), the mobile shell, improves upon ssh, allowing roaming connections, intermittent connectivity and  providing intelligent local echo.
  
  * [sshfs](https://github.com/libfuse/sshfs) can mount a folder on a remote server locally, and then you can use a local editor.

##### Shells & Frameworks

zsh的新特性
- Smarter globbing, `**`: `**/README.md`可递归地列出相应文件
- Inline globbing/wildcard expansion
- Spelling correction
- Better tab completion/selection (`XXX -`加`tab`会列出说明，很贴心)
- Path expansion (`cd /u/lo/b` will expand as `/usr/local/bin`)


##### Terminal Emulators
[comparison](https://anarc.at/blog/2018-04-12-terminal-emulators-1/)

重点：

- Font choice
- Color Scheme
- Keyboard shortcuts
- Tab/Pane support
- Scrollback configuration
- Performance (some newer terminals like [Alacritty](https://github.com/jwilm/alacritty) or [kitty](https://sw.kovidgoyal.net/kitty/) offer GPU acceleration).

**Exercises**
* pidwait，用于跨终端的控制
```shell
#!/bin/bash
pidwait(){
	try=0
	while [[ $try -eq 0 ]]; do
		kill -0 "$1" || try=1
		sleep 1
	done
}
```
* [background port forwarding](https://mpharrigan.com/2016/05/17/background-ssh.html)


#### Lecture 6.Version Control (Git)
* [我的Git笔记](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Output/git.md)

#### Lecture 7.Debugging and Profiling

* [我的Debugging and Profiling笔记](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Output/Debugging-and-Profiling.md)

#### Lecture 8.Metaprogramming

* [我的Metaprogramming笔记](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Output/Metaprogramming.md)

#### Lecture 9.Security and Cryptography
* [我的Security&Privacy&Cryptography笔记](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Output/Security-Privacy-Cryptography.md)

#### Lecture 10.Potpourri
[Potpourri](https://missing.csail.mit.edu/2020/potpourri/)

[ubuntu无sudo权限以及非root的用户apt安装软件](https://blog.csdn.net/qq_24406903/article/details/88376829)

##### **Keyboard remapping**

Mac-os karabiner，right command -> escape

##### **Daemons** - systemd

* e.g. sshd, systemd
  * `systemctl --user status`

* Systemd can be interacted with the `systemctl` command in order to `enable`, `disable`, `start`, `stop`, `restart` or check the `status` of services (those are the `systemctl` commands).
  * 如果出现端口占用，可以先stop再disable相关service


* [systemd入门教程](https://www.ruanyifeng.com/blog/2016/03/systemd-tutorial-commands.html)
* Systems Intro
  * https://docs.fedoraproject.org/en-US/quick-docs/systemd-understanding-and-administering/
  * 特点：
    * Aggressive parallelization capabilities
    * Uses socket and D-Bus activation for starting services
    * Offers on-demand starting of daemons, keeps track of processes using Linux cgroups
    * Supports snapshotting and restoring of the system state
    * Maintains mount and automount points
    * Implements an elaborate transactional dependency-based service control logic.


* **运维操作**

```shell
cd .config/systemd/user/
systemctl start/stop/restart/reload/condrestart(如果运行中则重新启动)/status/enable/disable/mask/is-enabled foo
```

```
systemctl
systemctl list-unit-files --type=service
ls /lib/systemd/system/*.service /etc/systemd/system/*.service

ls /etc/systemd/system/*.wants/
systemctl list-dependencies graphical.target


# Used when you create a new service file or modify any configuration
systemctl daemon-reload
```

* Modify service

  * `systemctl edit httpd.service`

  * To replace an option that can be set multiple times, it must cleared first, otherwise the override file will add the option a second time.

  * ```
    systemctl restart httpd
    ```

```
[Service]
Restart=always
RestartSec=30

[Service]
ExecStart=
ExecStart=<new command>

systemctl restart httpd
# systemctl edit --full httpd.service
```

* create service
  * /etc/systemd/system/foo.service

```
[Unit]
Description=My custom service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/sleep infinity

[Install]
WantedBy=multi-user.target
```

* Converting SysVinit services to systemd

* man systemd.unit

* [Common service parameters](https://docs.fedoraproject.org/en-US/quick-docs/systemd-understanding-and-administering/#_common_service_parameters)

* Mapping runlevels to targets

  



##### **Daemons** - macOS launchd / LaunchAgent

参考：[Apple Creating Launch Daemons and Agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)、[Apple Terminal: script management with launchd](https://support.apple.com/en-ca/guide/terminal/apdc6c1077b-5d5d-4d35-9c19-60f2397b2369/mac)、[launchd.info](https://www.launchd.info/?lang=en)

macOS 上长期运行服务优先用 `launchd`，而不是手写 `nohup ... &`。常见分层：

* `~/Library/LaunchAgents/*.plist`：当前用户登录后运行，适合个人自动化、IM bridge、本地 agent。
* `/Library/LaunchAgents/*.plist`：所有用户登录后可运行，由管理员安装。
* `/Library/LaunchDaemons/*.plist`：系统启动后以 root 或指定用户运行，不依赖图形登录。

`LaunchAgent` 的核心是 plist：`ProgramArguments` 指向真实命令，`WorkingDirectory` 固定工作目录，`StandardOutPath` / `StandardErrorPath` 落日志，`RunAtLoad=true` 表示加载后立即启动，`KeepAlive` 表示退出后由 `launchd` 拉起。

```shell
# 注册 / 启动当前用户 agent
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.example.agent.plist
launchctl kickstart -k "gui/$(id -u)/com.example.agent"

# 查看 / 停止
launchctl print "gui/$(id -u)/com.example.agent"
launchctl bootout "gui/$(id -u)/com.example.agent"
```

维护经验：

* 不要依赖交互 shell 环境，plist 里显式写 `PATH`、`HOME`、必要环境变量。
* plist 如果写入 token / secret，权限至少收紧到 `chmod 600`。
* `RunAtLoad=true` 解决“登录后自动启动”，`KeepAlive` 解决“异常退出后自动拉起”；两者不是一回事。
* Mac 可以锁屏或熄屏，但系统睡眠后长连接会断；常驻 agent 需要在电源设置里阻止自动睡眠，或用 Amphetamine / `caffeinate` 保持唤醒。
* 修改 plist 后通常需要 `bootout` 再 `bootstrap`，只改文件不一定会让已加载的 job 生效。

##### **FUSE**

[FUSE](https://en.wikipedia.org/wiki/Filesystem_in_Userspace) (Filesystem in User Space)

- [sshfs](https://github.com/libfuse/sshfs) - Open locally remote files/folder through an SSH connection.
- [rclone](https://rclone.org/commands/rclone_mount/) - Mount cloud storage services like Dropbox, GDrive, Amazon S3 or Google Cloud Storage and open data locally.
- [gocryptfs](https://nuetzlich.net/gocryptfs/) - Encrypted overlay system. Files are stored encrypted but once the FS is mounted they appear as plaintext in the mountpoint.
- [kbfs](https://keybase.io/docs/kbfs) - Distributed filesystem with end-to-end encryption. You can have private, shared and public folders.
- [borgbackup](https://borgbackup.readthedocs.io/en/stable/usage/mount.html) - Mount your deduplicated, compressed and encrypted backups for ease of browsing.

##### **Backups**

a copy of the data in the same disk is not a backup, because the disk is the single point of failure for all the data

Synchronization solutions are not backups

Some core features of good backups solutions are versioning, deduplication and security.

[backups lecture](https://missing.csail.mit.edu/2019/backups/)

##### **APIs**

 “[OAuth](https://www.oauth.com/)” is a protocol you will often see used. At its heart, OAuth is a way to give you tokens that can “act as you” on a given service, and can only be used for particular purposes. Keep in mind that these tokens are *secret*, and anyone who gains access to your token can do whatever the token allows under *your* account!

[IFTTT](https://ifttt.com/) is a website and service centered around the idea of APIs — it provides integrations with tons of services, and lets you chain events from them in nearly arbitrary ways.

##### **Common command-line flags/patterns**

Command-line tools vary a lot, and you will often want to check out their `man` pages before using them. They often share some common features though that can be good to be aware of:

- Most tools support some kind of `--help` flag to display brief usage instructions for the tool.
- Many tools that can cause irrevocable change support the notion of a “dry run” in which they only print what they *would have done*, but do not actually perform the change. Similarly, they often have an “interactive” flag that will prompt you for each destructive action.
- You can usually use `--version` or `-V` to have the program print its own version (handy for reporting bugs!).
- Almost all tools have a `--verbose` or `-v` flag to produce more verbose output. You can usually include the flag multiple times (`-vvv`) to get *more* verbose output, which can be handy for debugging. Similarly, many tools have a `--quiet` flag for making it only print something on error.
- In many tools, `-` in place of a file name means “standard input” or “standard output”, depending on the argument.
- Possibly destructive tools are generally not recursive by default, but support a “recursive” flag (often `-r`) to make them recurse.
- Sometimes, you want to pass something that *looks* like a flag as a normal argument. For example, imagine you wanted to remove a file called `-r`. Or you want to run one program “through” another, like `ssh machine foo`, and you want to pass a flag to the “inner” program (`foo`). The special argument `--` makes a program *stop* processing flags and options (things starting with `-`) in what follows, letting you pass things that look like flags without them being interpreted as such: `rm -- -r` or `ssh machine --for-ssh -- foo --for-foo`.

##### **VPNs**

[Don't use VPN services.](https://gist.github.com/joepie91/5a9909939e6ce7d09e29)

##### **Markdown**

[Markdown](https://commonmark.org/help/)

##### **Hammerspoon (desktop automation on macOS)**

[Hammerspoon](https://www.hammerspoon.org/) 

- Bind hotkeys to move windows to specific locations
- Create a menu bar button that automatically lays out windows in a specific layout
- Mute your speaker when you arrive in lab (by detecting the WiFi network)
- Show you a warning if you’ve accidentally taken your friend’s power supply

```
command + option + 方向键
```

resources:
- [Learn Lua in Y minutes](https://learnxinyminutes.com/docs/lua/)
- [Getting Started with Hammerspoon](https://www.hammerspoon.org/go/)
- [Sample configurations](https://github.com/Hammerspoon/hammerspoon/wiki/Sample-Configurations)
- [Hammerspoon APIs](http://www.hammerspoon.org/docs/)
- [Anish’s Hammerspoon config](https://github.com/anishathalye/dotfiles-local/tree/mac/hammerspoon)

##### **Booting + Live USBs**

When your machine boots up, before the operating system is loaded, the [BIOS](https://en.wikipedia.org/wiki/BIOS)/[UEFI](https://en.wikipedia.org/wiki/Unified_Extensible_Firmware_Interface) initializes the system. During this process, you can press a specific key combination to configure this layer of software. For example, your computer may say something like “Press F9 to configure BIOS. Press F12 to enter boot menu.” during the boot process. You can configure all sorts of hardware-related settings in the BIOS menu. You can also enter the boot menu to boot from an alternate device instead of your hard drive.

[Live USBs](https://en.wikipedia.org/wiki/Live_USB) are USB flash drives containing an operating system. You can create one of these by downloading an operating system (e.g. a Linux distribution) and burning it to the flash drive. This process is a little bit more complicated than simply copying a `.iso` file to the disk. There are tools like [UNetbootin](https://unetbootin.github.io/) to help you create live USBs.

Live USBs are useful for all sorts of purposes. Among other things, if you break your existing operating system installation so that it no longer boots, you can use a live USB to recover data or fix the operating system.

##### **Docker, Vagrant, VMs, Cloud, OpenStack**

docker和VM的区别：docker运行的时候和host共享kernel，在Linux中用LXC机制，利用一系列isolation机制spin up a program that thinks it’s running on its own hardware but it’s actually sharing the hardware and kernel with the host

[Vagrant](https://www.vagrantup.com/) is a tool that lets you describe machine configurations (operating system, services, packages, etc.) in code, and then instantiate VMs with a simple `vagrant up`. [Docker](https://www.docker.com/) is conceptually similar but it uses containers instead.

Popular services include [Amazon AWS](https://aws.amazon.com/), [Google Cloud](https://cloud.google.com/), and [DigitalOcean](https://www.digitalocean.com/).

##### **Notebook programming**

[Notebook programming environments](https://en.wikipedia.org/wiki/Notebook_interface) can be really handy for doing certain types of interactive or exploratory development. Perhaps the most popular notebook programming environment today is [Jupyter](https://jupyter.org/), for Python (and several other languages). [Wolfram Mathematica](https://www.wolfram.com/mathematica/) is another notebook programming environment that’s great for doing math-oriented programming.

##### **Q&A**

[Writing an OS in Rust](https://os.phil-opp.com/)

- `/bin` - Essential command binaries
- `/sbin` - Essential system binaries, usually to be run by root
- `/dev` - Device files, special files that often are interfaces to hardware devices
- `/etc` - Host-specific system-wide configuration files
- `/home` - Home directories for users in the system
- `/lib` - Common libraries for system programs
- `/opt` - Optional application software
- `/sys` - Contains information and configuration for the system (covered in the [first lecture](https://missing.csail.mit.edu/2020/course-shell/))
- `/tmp` - Temporary files (also `/var/tmp`). Usually deleted between reboots.
- `/usr/` - Read only user data    
- `/usr/bin` - Non-essential command binaries
  - `/usr/sbin` - Non-essential system binaries, usually to be run by root
  - `/usr/local/bin` - Binaries for user compiled programs
- `/var` - Variable files like logs or caches

关于package manager的选择

* use the language-specific package manager whenever possible, and to use  isolated environments (like Python’s virtualenv) to avoid polluting the  global environment.
* Depending on the operating system and the hardware architecture, some of these packages might come with binaries or might need to be compiled.  For instance, in ARM computers like the Raspberry Pi, using the system  package manager can be better than the language specific one if the  former comes in form of binaries and the later needs to be compiled.  This is highly dependent on your specific setup.





### Linux命令按字母分类
#### a
* ag
  * Flags 含义与 grep 相似
  * http://conqueringthecommandline.com/book/ack_ag
* alias
  * `alias pip3="python3 -m pip"`
  * 非交互模式下启用 alias 扩展
```shell
shopt -s expand_aliases
shopt expand_aliases # show current status
```

* apt
  * 坑：krb5在docker中安装 https://askubuntu.com/questions/1017999/install-kerberos-client-without-interactive-session
  * -y：静默模式
```shell
sudo apt update # 更新源
sudo apt dist-upgrage

sudo apt install
sudo apt remove
sudo apt autoremove
```



* awk: 一种控制台编程工具，寻找和处理pattern
  * 入门[wiki](https://zh.wikipedia.org/wiki/AWK)
  * 数据统计：
    * `awk -F'[ ,]+' '{print $1,$3,$5,$7}' | awk '{ for (i=1; i<=NF; i++) { sum[i]+= $i }} END { for (i=1; i<=NF; i++) {printf "%.9f ", sum[i]/NR}}'`：算均值
      * ``-F'[]'`内空格和逗号都是分隔符，`+`表示将连续分隔符视为一个
    * `history | awk '{$1="";print substr($0,2)}' | sort | uniq -c | sort -n | tail -n 10` ：得到使用频率最高的10个命令
  * `awk '$NF!~/\.so/{next} {$0=$NF} !a[$0]++' /proc/1585728/maps`
    * `$NF!~/\.so/{next}` – If the last column doesn’t contain “*.so*“, we ignore it
    * `{$0=$NF}` - If the last column contains a shared library, we replace the line by the last column, which is the filename of the library
    * `*!a[$0]++*` is an *awk* trick to [remove duplicate lines](https://www.baeldung.com/linux/uniq-by-column)
  * `find . -name "*@to_be_deleted" | awk -F"@to_be_deleted" '{print "mv " $0 " " $1}'|sh`：将文件夹内文件名中的某个pattern删掉
  * 循环打印：`awk 'BEGIN { for (i=0; i<10; i++) printf("%02d ", i) }'`

#### b
* `bash -x run.sh` 显示shell脚本执行过程中的实际命令
* bg: resume后台暂停的命令
#### c
* cat
* cd
* chmod：
  * `sudo chmod 777 -R` 文件修改为可执行
  * `Permissions 0644 for ‘~/.ssh/id_rsa’ are too open` => `chmod 0600 ~/.ssh/id_rsa`
* chown: 用于设置文件所有者和文件关联组的命令
  * ``sudo chown root:root /usr/bin/rclone``
```shell
HOST_PERM="$(id -u):$(id -g)"
chown $HOST_PERMS $file
```

* cloc: 代码行数统计
* curl
  * -I/--head: 只显示传输文档，经常用于测试连接本身
  `curl --head --silent baidu.com | grep --ignore-case content-length | cut -f2 -d ' '`
  * [curl查询公网出口ip](https://www.jianshu.com/p/e9b26711c9de) `curl cip.cc`
* cut
  * 使用 -f 选项提取指定字段：`cut -f2,3 test.txt`
* cp
  * [-H vs -L](https://superuser.com/questions/593196/cp-h-vs-cp-l-what-is-a-command-line-symbolic-link), 两者都是 follow symbolic links，区别在于 -r 时表现不同
* cron: a daemon your system already runs to perform scheduled tasks
* c++filt: demangle C++/Java symbols

#### d
* d: zsh的特点，可显示最近10个目录，然后`cd -数字`进入
* date：日期
* dd

  * you have *very* large devices to copy, so that experimenting to determine the best block-size is worthwhile.
  * you have to copy only part of a disk. You can specify `count` to limit how many blocks are copied.

  * you want to resume an interrupted copy. You can't do so with `cp`, but you can try with `dd`, by using the `seek` and `skip` options.

  * you want to pipe it to the standard input of something (admittedly, `cat` will work here too):

    ```
    dd if=/dev/sda bs=10M | ssh host dd of=/dev/sdb
    ```

  * `dd` usefulness is very well discussed in this Unix and Linux post: [dd vs cat — is dd still relevant these days?](https://unix.stackexchange.com/q/12532/70524)
* declare
  * https://www.runoob.com/linux/linux-comm-declare.html

```shell
declare -a NAMES=(
	a \
	b \
	c \
	d \
)
```

* df: disk情况
* disown
* diff：[Linux中diff的渊源](https://www.cnblogs.com/moxiaopeng/articles/4853352.html)
  * `diff -Naur`  比较两个文件夹

* dmesg: kernel log

* docker

```
docker logs --tail 100 $pod
```

* `dpkg -i ***.deb`
* `du -h -d 1 $file`
  * `du -h -d 1 $file | sort -rh`


#### e
* echo: 输出输入，空格分割
* env: 进入环境
  * 读man env，` #!/usr/bin/env -S /usr/local/bin/php -n -q -dsafe_mode=0`，利用env来传参。（FreeBSD 6.0之后不能直接传参，解释器会把多个参数合成一个参数）
* [export](http://man7.org/linux/man-pages/man1/export.1p.html)

#### f
* [fd](https://github.com/sharkdp/fd)：作为find的替代品
  * colorized output, default regex matching, Unicode support, more intuitive syntax
* [fg](https://blog.csdn.net/carolzhang8406/article/details/51314894): Run jobs in foreground
* find：1）寻找文件； 2）机械式操作
  * -iname：大小写不敏感

```shell
# Find all directories named/including src
find . -name src -type d
find . -name "*src*" -type d
# Find all python files that have a folder named test in their path
find . -path '**/test/**/*.py' -type f
# Find all files modified in the last day
find . -mtime -1
# Find all zip files with size in range 500k to 10M
find . -size +500k -size -10M -name '*.tar.gz'

# Delete all files with .tmp extension
find . -name '*.tmp' -exec rm {} \;
# Find all PNG files and convert them to JPG
find . -name '*.png' -exec convert {} {.}.jpg \;

find /tmp -maxdepth 1 -mmin +720 -name "tmp*" -delete

```
* [fuck](https://github.com/nvbn/thefuck#the-fuck-----): 流行的纠正工具

#### g

* grep

```shell
# specify lines of trailing context
-A 10
# ignore cases
-i
# "NOT"筛选
grep -v "trash"
# “OR”筛选
grep -E "key1|key2"  
# “AND”筛选
grep -E "key1.*key2"
# 颜色
--color

grep -o '^20120603 08:02:..' $file | sort | uniq -c

```

* gunzip

```shell
gunzip 1.gz
gunzip -v 1.gz
gunzip -v -S "mygz" 1.mygz # 按指定后缀名解压
```



#### h
#### i
* [icdiff](): 分屏比较文档
  * `icdiff button-{a,b}.css`
* ifconfig
#### j
* jobs
#### k

* krb5

```shell
export DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get install -y krb5-user
```



#### l
* less
  * `space / B` 翻页
* locate
  * Most would agree that `find` and `fd` are good but some of you might be wondering about the efficiency of  looking for files every time versus compiling some sort of index or  database for quickly searching. That is what [`locate`](http://man7.org/linux/man-pages/man1/locate.1.html) is for. `locate` uses a database that is updated using [`updatedb`](http://man7.org/linux/man-pages/man1/updatedb.1.html). In most systems `updatedb` is updated daily via [`cron`](http://man7.org/linux/man-pages/man8/cron.8.html). Therefore one trade-off between the two is speed vs freshness. Moreover `find` and similar tools can also find files using attributes such as file size, modification time or file permissions while `locate` just uses the name. A more in depth comparison can be found [here](https://unix.stackexchange.com/questions/60205/locate-vs-find-usage-pros-and-cons-of-each-other).
* ls
  * -l: long listing format; drwxr-xr-x，d代表文件夹，后面3*3代表owner、owning group、others的权限
  * r：read，w：modify，x：execute
  * -t: 按时间排序
* lsof: 查看文件占用
  * 也可查看端口占用，接 grep 即可 
#### m
* man: q退出
  * `fork(2)` -> `man 2 fork`
* mkdir
* mv
#### n
* [nc(netcat)](https://zhuanlan.zhihu.com/p/83959309): TCP/IP 的瑞士军刀
  * 端口测试：`nc localhost $port`
* netstat
* nohup
  * [如何优雅地让Python程序在后台运行](https://atomlab.org/post/code/python-background/)
```shell
# 将标准输出放到name.log中，并且记录该进程的pid到run.pid中
nohup python -u main.py > name.log 2>&1 & echo $! > run.pid

# 若存在run.pid文件，则加载它并杀掉该进程
[[ -f run.pid ]] && kill $(cat run.pid)
```

#### o 

* open:
  * -n用来多开
  * `open -a "sublime text" ~/temp.diff`


#### p
* [pandoc](https://github.com/jgm/pandoc)
  * `pandoc test1.md -f markdown -t html -s -o test1.html
  `
  * `pandoc -s --toc -c pandoc.css -A footer.html MANUAL.txt -o example3.html`
  
* pbcopy: 复制到剪贴板 `pbcopy < file`

* pgrep: 配合jobs
  * `pgrep -f 100` 全命令行匹配
  
* ping

* pip
  * pip list
  
  * pip show requests
  
  * ```Bash
    pip uninstall requests
    ```
  
  * ```Bash
    pip freeze > requirements.txt
    ```
  
  * ```shell
    python -m ensurepip --upgrade # 如果损坏
    pip install /path/to/package #安装一个本地的Python包
    pip install package== 显示可安装的版本
    pip install -r requirements.txt #从requirements.txt文件中安装包
    pip cache purge #清理缓存
    pip install package_name==version_number #安装指定版本的包
    pip install --upgrade package_name #升级已安装的包
    pip install --user package_name #这将在用户的本地目录中安装该库
    pip install --no-dependencies package_name #安装名为xx的Python包但忽略其依赖项
    pip install --find-links=URL package_name #从指定的URL中找到并安装名为"myproject的Python包
    ```
  
* pkill = pgrep + kill

  * `pkill -9 -f 100` 
  * `pkill -f "^.*autoops.api*" -n`

* pmap: Displays the memory map of a process.

* ps aux

* pstree

* pushd: 目录栈，方便切换目录
  * 配合popd

* pwd: print cwd
#### q
#### r

* rsync
  * `rsync -avz /path/to/source/ user@remote:/path/to/destination/`

#### s
* scp

```shell
scp $file user@ip:/home/$folder
scp -r $folder
```

* script
  
  * 记录终端操作记录，按`C-d`退出
  * 可用于demo演示终端操作
  
* sed
  * `-i.bak`: 直接修改文件并创建备份。


```shell
sed -i.bak "s/version='[0-9]\+\.[0-9]\+\.[0-9]\+'/version='$NEW_VERSION'/" setup.py
```

* sha1sum:  `printf 'hello' | sha1sum`  

* sha256sum

* source

```shell
# "." 等价于 source
```



* strings

  * https://www.howtogeek.com/427805/how-to-use-the-strings-command-on-linux/

  * ```
    sudo strings /dev/mem | less
    ```

#### t
* tac: 反向
* tar
  * 报错可能需要sudo


```shell
tar cvzf 压缩文件名.tar.gz 被压缩文件夹 # gz文件
tar xvzf 压缩文件名.tar.gz -C 目标文件夹 # 否则解压到当前路径
tar xvf  压缩文件名.tar.xz
```



* tail
  * `ls -l | tail -n1`
  * -f：不断读最新内容，实时监视
* tee: Read from standard input and write to standard output and files (or commands).
  * 和`xargs`有相似之处，都是转化stdin用于他用
  * `echo "example" | tee /dev/tty | xargs printf "[%s]"`
* tig
  * tig是一个基于ncurses的git文本模式接口。它的功能主要是作为一个Git存储库浏览器，但也可以帮助在块级别上分段提交更改，并充当各种Git命令输出的分页器
* time
* tmux 
* top

  * -d 10: 10s采样
  * -H: 显示线程
  * -H -p $pid：显示指定进程下的线程
  * 按 1 键显示 per cpu core 利用率
  * 按 e/E 切换内存单位
  * 按 f 键增加显示项目


##### top 指标含义

VIRT：virtual memory usage 虚拟内存

1、进程“需要的”虚拟内存大小，包括进程使用的库、代码、数据等

2、假如进程申请100m的内存，但实际只使用了10m，那么它会增长100m，而不是实际的使用量

RES：resident memory usage 常驻内存

1、进程当前使用的内存大小，但不包括swap out

2、包含其他进程的共享

3、如果申请100m的内存，实际使用10m，它只增长10m，与VIRT相反

4、关于库占用内存的情况，它只统计加载的库文件所占内存大小

SHR：shared memory 共享内存

1、除了自身进程的共享内存，也包括其他进程的共享内存

2、虽然进程只使用了几个共享库的函数，但它包含了整个共享库的大小

3、计算某个进程所占的物理内存大小公式：RES – SHR

4、swap out后，它将会降下来

DATA

1、数据占用的内存。如果top没有显示，按f键可以显示出来。

2、真正的该程序要求的数据空间，是真正在运行中要使用的。

* traceroute: -w 1

* tree: 显示树形文件结构, `-L`设置层数
#### u

* `uname -a` 查内核版本
* `ulimit -a`
  * `ulimit -s xxx` 修改线程栈大小


#### v
#### w
* wait：`wait pid`，不加pid则等待所有进程
* `watch -n 5 $cmd`
* wc: -l
  * [source code](https://www.gnu.org/software/cflow/manual/html_node/Source-of-wc-command.html#Source-of-wc-command)
    * 这段代码只将连续的字母作为一个字，连续的数字等不作为word
    * isword用来判断当前字符是否处于一个字，isword实现的功能不完善

* which：找到程序路径
* [wget](https://blog.csdn.net/wangshuminjava/article/details/79916655): 断点续传-c    后台-b

#### x
* xargs：[解决命令的输入来源问题](https://blog.csdn.net/vanturman/article/details/84325846)：命令参数有标准输入和命令行参数两大来源，有的命令只接受命令行参数，需要xargs来转换标准输入
  * e.g. ` ls | xargs rm`
  * `-0`: 分隔符用NULL
#### y
* youget
  * 自动补全：`curl -fLo ~/.zplug/repos/zsh-users/zsh-completions/src/_youget https://raw.githubusercontent.com/soimort/you-get/develop/contrib/completion/_you-get`
#### z

### bugs
* `_arguments:450: _vim_files: function definition file not found`
```shell
rm ~/.zcompdump*
rm ~/.zplug/zcompdump*
exec zsh
```
