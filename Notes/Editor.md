[toc]

### Macbook

#### 手机远程协作

* 手机作为开发辅助设备的优势：
  * 便携性，随时处理简单任务
  * 作为第二屏使用
  * 利用手机的特性（摄像头、传感器等）

* 推荐工具：
  * VS Code Remote + 手机SSH连接
  * 远程桌面工具：TeamViewer、AnyDesk
  * Git客户端：Working Copy (iOS)

##### Working Copy 使用指南（iOS）

**适用场景**：随时随地快速提交任务、修改笔记、记录灵感

**配置步骤**：
1. 在 App Store 下载 Working Copy
2. 克隆 CS-Notes 仓库（支持 HTTPS 或 SSH）
3. 配置 Git 用户信息（姓名、邮箱）

**快速提交任务流程**：
1. 打开 Working Copy，进入 CS-Notes 仓库
2. 找到 `.trae/documents/INBOX.md` 文件
3. 点击编辑，在文件末尾按格式添加任务条目
4. 提交修改（Commit），填写提交信息如 "Add todo: 研究 AI Agent 应用"
5. 推送到远程仓库（Push）

**常用操作**：
- 拉取最新代码：Pull
- 查看文件历史：History
- 对比修改：Diff
- 分支管理：Branches

**最佳实践**：
- 提交信息使用清晰的描述
- 小步提交，避免大段改动
- 定期 Pull 保持代码最新
- 配合 Trae 的 "执行 todos" 指令完成任务闭环

#### 快捷键

* ctrl + 左右箭头：切屏

#### 豆包App 快捷键

* option + S: 语音输入
* option + space: 唤起豆包
* shift + option + A: 截图

### Codex

* @ 引用文件
* `codex -i`
* `/skills`

#### Codex App 快捷键

> 来源：[Commands - Codex app](https://developers.openai.com/codex/app/commands)

* 双击左右 `Command`：Appshots，把当前 Mac 前台窗口及可用文本作为附件发给 Codex thread；如果 60 秒内和某个 thread 互动过，会优先追加到最近 thread。
* `Cmd + J`：切换 Terminal / Shell
* Opt + N: 唤起侧边对话
* `Cmd + Shift + P` 或 `Cmd + K`：打开命令面板
* `Cmd + B`：切换侧边栏
* `Cmd + Option + B`：切换 Diff 面板
* `Cmd + N`（或 `Cmd + Shift + O`）：新建线程
* `Cmd + F`：当前线程内查找
* `Cmd + Shift + [` / `Cmd + Shift + ]`：上一个 / 下一个线程
* `Cmd + [` / `Cmd + ]`：后退 / 前进
* `Ctrl + L`：清空 Terminal
* `shift + tab`: plan mode

### Trae

Trae 是深度融合 AI 能力的 IDE，有 IDE 模式和 SOLO 模式两种开发模式。

* 核心特点：
  * 内置 SOLO Coder 智能体，可独立完成复杂开发任务
  * 支持 Skills 扩展 AI 能力
  * 双重开发模式：IDE 模式（保留原有流程）和 SOLO 模式（AI 主导任务）
  * 开放的智能体生态

#### AI 长记性配置

结合 Trae 机制让 AI 保持记忆和经验积累的方法：

* Trae 自动记忆机制：
  * 对话历史自动保留，提供上下文连贯性
  * 同一项目中的多次交互会保持记忆

* 项目上下文配置：
  * 利用 `.trae/` 目录下的配置文件提供项目特定信息
  * 创建项目介绍文档，让 AI 了解项目背景和架构

* 记忆机制：
  * **CLAUDE.md**（或类似命名的项目配置文件）：相对固定的上下文信息，不适合频繁修改
  * **PROGRESS.md**：记录经验教训、错误总结，让 AI 避免重复犯错
  * 对话历史：保持上下文连贯性

* 实践技巧：
  * 重要决策和学习点及时记录到笔记中
  * 新任务开始时，让 AI 回顾相关历史对话和笔记
  * 使用 Skills 来标准化特定类型的任务处理方式
  * 及时记录关键决策和学习点
  * 定期整理和优化记忆内容
  * 在新任务开始前让 AI 回顾相关经验

#### 快捷键

* 报告问题：Command + K Command + R

#### 插件

* BasedPyright
  * BasedPyright 默认设置了较为严格的类型检查，为避免被过度干扰，建议将其调低 。步骤如下：
    * 打开 Editor 设置，搜索 pyright type checking mode。
    * 将默认的 recommended 模式修改为 basic 模式。
* ruff

#### MCP

> 官网：https://docs.trae.ai/ide/tutorial-mcp-figma?_lang=zh
>
> 公众号
&gt;
&gt; TRAE 友推荐 MCP，快快码住！（来源：http://xhslink.com/o/ErNKkiaabY）
&gt; - [一R] MCP 推荐-Rednote
&gt; - [二R] MCP 推荐- Feedback Enhanced
&gt; - [三R] APM 使用与本地 MCP 集成方案






### Vim

[Editor War](https://en.wikipedia.org/wiki/Editor_war)

[Stack Overflow survey](https://insights.stackoverflow.com/survey/2019/#development-environments-and-tools)

[Vim emulation for VS code](https://github.com/VSCodeVim/Vim)：个人觉得Vim+VSCode是绝配，Vim负责文本编辑，VSCode负责插件等高级功能

[在VSCode中使用Vim的正确方式](https://zhuanlan.zhihu.com/p/141248420)

**Vim的设计逻辑：a modal editor，多模态的编辑器**

- Normal (ESC): for moving around a file and making edits，ESC很重要，我用[Karabiner](https://mac.softpedia.com/get/System-Utilities/KeyRemap4MacBook.shtml)把MacOS的右Command键设成了ESC
- Insert (i): for inserting text
- Replace (R): for replacing text，无需删除，在文本上覆盖编辑；`r`替换字符
- Visual (plain (v), line (V), block (C-v)) mode: for selecting blocks of text
  * `^V = Ctrl-v = <C-v>`
- Command-line (:): for running a command

**Vim基础**
* 插入，按i进入，Esc退出
* 概念：Buffers, tabs, and windows
  *  buffer和window关系：一对多
* Command-line
  * :q   quit (close window)
  * :w   save (“write”)
  * :wq   save and quit    = `ZZ`
  * :e {name of file}   open file for editing   **利用这一命令和:sp在文件间复制粘贴**
  * `:E` 打开netrw文件浏览器
  * :ls   show open buffers
  * :help {topic}   open help，`Ctrl-D`显示补全命令列表
  * `:r`提取和合并文件；`:r !ls`可读取存放外部命令输出

#### Vim’s interface is a programming language
**Movement**：也称作“nouns”，因为指代chunks of text

* Basic movement: `hjkl`左下上右
* Words: `w` (下一个词开头), `b` (本词或上一个词开头), `e` (本词或下一个词末尾，常和`a`搭配)
* Lines: `0` (beginning of line), `^` (first non-blank character), `$` (end of line)
* Paragraph (原文没写): `{ and }` 
* Screen: `H` (top of screen), `M` (middle of screen), `L` (bottom of screen)
* Scroll: `Ctrl-U (up), Ctrl-D (down)`
* File: `gg` (beginning of file), `G` (end of file), `Ctrl-G`显示行号信息, `数字+G`移动到某一行
* Line numbers: `:{number}` or `{number}G` (line {number})
* Misc: `%` (corresponding item，比如括号匹配)
* Find: `f{character}`, `t{character}`, `F{character}`, `T{character}`
  - find/to forward/backward {character} on the current line
  - `,` / `;` for navigating matches
* [Search](https://www.cnblogs.com/wayneliu007/p/10322453.html): `/{regex}`向后搜索, `n` / `N` for navigating matches
  * `？{regex}`向前搜索
  * 退出查找高亮状态：`:nohl`
  * `:set ic`忽略大小写；`:set hls is`; 选项前加no可关闭选项`:set noic`
    * `/\cword`不区分大小写查找

**Selection**：Visual modes 

* plain (v) 
* line (V)
* block (Ctrl-v) 
* `v`键提取后按`: ... w ABC`可以保存文件

**Edits**: "Verbs"

* `i`进入insert模式
* `o` / `O` insert line below / above
* `d{motion}` delete {motion}    
  - e.g. `dw` is delete word, `d$` is delete to end of line, `d0` is delete  to beginning of line
* `c{motion}` change {motion}    
  - e.g. `cw` is change word
  - like `d{motion}` followed by `i`
* `x` delete character (equal do `dl`)
* `s` substitute character (equal to `xi`)
* visual mode + manipulation    
  - select text, `d` to delete it or `c` to change it
* `u` to undo, `<C-r>` to redo，`U`撤销行内命令
  * vim plugin: undotree[https://github.com/mbbill/undotree] 
  * [how to persistently undo](https://vim.fandom.com/wiki/Using_undo_branches#Persistent_undo)
* `y` to copy / “yank” (some other commands like `d` also copy)
* `p` to paste
* Lots more to learn: e.g. `~` flips the case of a character
* d, y, c均可双写，表示单行操作
* `A a S s `附加操作，相当于操作后移一格
* `y`操作符命令会把文本复制到一个寄存器3中。然后可以用`p`命令把它取回。因为`y`是一个操作符命令，所以可以用`yw`来复制一个word. 同样可以使用counting, 如用`y2w`命令复制两个word，`yy`命令复制一整行，`Y`也是复制整行的内容，复制当前光标至行尾的命令是`y$`
  { }段首段尾

**Counts**:

- `3w` move 3 words forward
- `5j` move 5 lines down
- `7dw` delete 7 words

**Modifiers**: 接在nouns后面，i=inside，a=around，t=to

- `ci(` change the contents inside the current pair of parentheses
- `ci[` change the contents inside the current pair of square brackets
- `da'` delete a single-quoted string, including the surrounding single quotes
- `d2a` 删除到a之前

#### Vim拓展
./vimrc: [课程推荐config](https://missing.csail.mit.edu/2020/files/vimrc), instructors’ Vim configs ([Anish](https://github.com/anishathalye/dotfiles/blob/master/vimrc), [Jon](https://github.com/jonhoo/configs/blob/master/editor/.config/nvim/init.vim) (uses [neovim](https://neovim.io/)), [Jose](https://github.com/JJGO/dotfiles/blob/master/vim/.vimrc))

plugin: [推荐网站](https://vimawesome.com/)，git clone到`~/.vim/pack/vendor/start/`
* [ctrlp.vim](https://github.com/ctrlpvim/ctrlp.vim): fuzzy file finder

* [ack.vim](https://github.com/mileszs/ack.vim): code search

* [nerdtree](https://github.com/scrooloose/nerdtree): file explorer
  
  * 手动输`vim -u NONE -c "helptags ~/.vim/pack/my_plugs/start/nerdtree/doc" -c q`激活帮助插件，配置在了我的dotfiles里
  
* [vim-easymotion](https://github.com/easymotion/vim-easymotion): magic motions

* [ale](https://github.com/dense-analysis/ale#installation-with-vim-plug)

  * `:ALEGoToDefinition`
  * `:ALEFindReferences`
  * `:ALEHover`
  * `:ALESymbolSearch`


#### Vim-mode的其它应用
* Shell：If you’re a Bash user, use `set -o vi`. If you use Zsh, `bindkey -v`. For Fish, `fish_vi_key_bindings`. Additionally, no matter what shell you use, you can `export EDITOR=vim`. This is the environment variable used to decide which editor is launched when a program wants to start an editor. For example, `git` will use this editor for commit messages.

* Readline: Many programs use the [GNU Readline](https://tiswww.case.edu/php/chet/readline/rltop.html) library for their command-line interface. 
  * Readline supports (basic) Vim emulation too, which can be enabled by adding the following line to the `~/.inputrc` file: `set editing-mode vi`
  * With this setting, for example, the Python REPL will support Vim bindings.

* Others:

  There are even vim keybinding extensions for web [browsers](http://vim.wikia.com/wiki/Vim_key_bindings_for_web_browsers), some popular ones are [Vimium](https://chrome.google.com/webstore/detail/vimium/dbepggeogbaibhgnhhndojpepiihcmeb?hl=en) for Google Chrome and [Tridactyl](https://github.com/tridactyl/tridactyl) for Firefox. You can even get Vim bindings in [Jupyter notebooks](https://github.com/lambdalisue/jupyter-vim-binding).

#### Vim的其它特性积累

* Q: 如果文件太大打不开怎么办？
  * A: 先`grep -nr $target $FILE`获取行号，然后`vim $FILE +N`进入定位所在。

* 粘贴文本
  * `:set paste`
  * `:set nopaste`

* 缩进操作：
  * 先 `v` 进入visual模式选定要缩进的内容，再 `shift + </>` 进行整体的左右缩进
  * 对齐缩进：`v`选中第二、三行，然后`=`，与第一行对齐缩进
* 补全：连续按 `Ctrl-P`



buffer操作：` :ls,:b num, :bn（下一个）, :bp（前一个）, :b#(上次的buffer) `

window操作： `:sp / :vsp` split window，`C-w + hjkl`切换

tab操作：`gt`切换tab

跳转操作：

* `Ctrl-O/I` 进入更旧/新的位置

* Marks - In vim, you can set a mark doing `m<X>` for some letter `X`. You can then go back to that mark doing `'<X>`. This let’s you quickly navigate to specific locations within a file or even across files.

查找替换：
* `:%s/foo/bar/g`
  * replace foo with bar globally in file
  * `%`表示修改全文件而不是第一个匹配串，`/g`表示全行/全文件匹配，`/gc`会提示每个匹配串是否替换 
  * `:#,#s/...`表示对行号之间的内容操作
* ` :%s/\[.*\](\(.*\))/\1/g`
  
  - replace named Markdown links with plain URLs
  

命令操作：
* `:g/pattern/command`，对匹配行执行命令
* `.`复制操作
* 外部命令：`:!`

Advanced Text Objects - Text objects like searches can also be composed with vim commands. E.g. `d/<pattern>` will delete to the next match of said pattern or `cgn` will change the next occurrence of the last searched string.





#### Macros
- `q{character}` to start recording a macro in register `{character}`

- `q` to stop recording

- `@{character}` replays the macro

- Macro execution stops on error

- `{number}@{character}` executes a macro {number} times

- Macros can be recursive    

  - first clear the macro with `q{character}q`
  - record the macro, with `@{character}` to invoke the macro recursively  (will be a no-op until recording is complete)

- Example: convert xml to json   ([file](https://missing.csail.mit.edu/2020/files/example-data.xml))    

  - Array of objects with keys “name” / “email”

  - Use a Python program?

  - Use sed / regexes        

    - `g/people/d`
    - `%s/<person>/{/g`
    - `%s/<name>\(.*\)<\/name>/"name": "\1",/g`
    - …

  - Vim commands / macros        

    - `Gdd`, `ggdd` delete first and last lines

    - Macro to format a single element (register `e`)            
      - Go to line with `<name>`
      - `qe^r"f>s": "<ESC>f<C"<ESC>q`

    - Macro to format a person            

      - Go to line with `<person>`
      - `qpS{<ESC>j@eA,<ESC>j@ejS},<ESC>q`

    - Macro to format a person and go to the next person            

      - Go to line with `<person>`
      - `qq@pjq`

    - Execute macro until end of file            

      - `999@q`

    - Manually remove last `,` and add `[` and `]` delimiters
  - [在vimrc中存宏](https://stackoverflow.com/questions/2024443/saving-vim-macros) 

<img src="Editor/vim.png" alt="vim" style="zoom:100%;" />


#### Resources

- `vimtutor` is a tutorial that comes installed with Vim
- [Vim Adventures](https://vim-adventures.com/) is a game to learn Vim
- [Vim Tips Wiki](http://vim.wikia.com/wiki/Vim_Tips_Wiki)
- [Vim Advent Calendar](https://vimways.org/2019/) has various Vim tips
- [Vim Golf](http://www.vimgolf.com/) is [code golf](https://en.wikipedia.org/wiki/Code_golf), but where the programming language is Vim’s UI
- [Vi/Vim Stack Exchange](https://vi.stackexchange.com/)
- [Vim Screencasts](http://vimcasts.org/)
- [Practical Vim](https://pragprog.com/book/dnvim2/practical-vim-second-edition) (book)

### Clion

#### 基础设置

* python interpreter

##### Git

* git插件生效
  * `git config --global --add safe.directory /xxx`

##### Format

* **Format: option + shift + F**

* **设置：command + Option + shift + L**

* 细节：
  * 需要重启IDE才能在KeyMap里看到
  * 设置 External Tools，不要设置 Remote

![-](./Editor/image-20250310171321679.png)





#### 快捷键

* 文件栏：`command + shift + E`
* 改代码：
  * 快速修复警告/上下文操作：`command + .`

* 写代码
  * **包围模版：command + option + T**
  * 复制和删除行：
    * ![image-20250215160720438](./Editor/image-20250215160720438.png)

  * 补全：
    * 显式激活：command + I
    * 智能补全：command + shift + 下箭头

  * 向下拉取某行：option + 下箭头

* 注释：
  * 行注释：command + /
  * 块注释：shift + /

* 选代码：
  * ![image-20250215163426680](./Editor/image-20250215163426680.png)
  * 扩展选区：command + shift + ctrl + 右箭头


* 重构：
  * F2
  * 上下文重构：shift + ctrl + R
  * 更改签名：command + F6
  * 提取常量：command + option + V； 接Tab改名
  * 提取方法：command + option + M
* 文件操作：
  * command + shift + F
  * command + shift + H，文件替换

#### 读代码

* **跳转到类型声明：**
  * **command + shift + 点击**

* **切换Tab：**
  * **command + shift + 【/】**
* **展开**
  * expand to **到级别（custom）**
    * **command + shift + J/K 1/2/3/4/5**
  * **某块区域**
    * **command + option + [或]**
  * 全部区域：
    * Command K-J、K-0
* 搜索：
  * 随处搜索：两次shift 或者 `F1`
  * 查文件：command + P
  * 查方法或全局变量：command + T
  * 上下切换：command + G / command + shift + G

* **方法的详细用法：**
  * **shift + option + F12**
* **最近文件：command + E**
* 文件视图
  * command + option + O
  * command + 7

#### 代码辅助

* 还原代码： 右键 本地历史记录
* **显示方法签名：**
  * **command + shift + space**
* 右键 显示汇编
* 打开文档：command K + command I，连续点
* 类型匹配补全 (custom)：
  * command + shift + 下箭头
* 后缀补全：输入`.`，比如生成make_unique
* 补全建议：Command I + Tab

#### 编译



#### 运行

* ctrl + F5
* conda环境配置
  * ![image-20250411122027844](./Editor/image-20250411122027844.png)




#### Debug

* 打断点：F9
* step into: f11
* step over: f10
* 重新运行：command + ; + L
* Python AssertionError断点

![image-20250213180054012](./Editor/image-20250213180054012.png)

* C++ Extension
  * 尝试了一下clion官方的debug C++ extension的方法，没有成功
    - https://www.jetbrains.com/help/clion/debugging-python-extensions.html#debug-custom-py



#### 测试

![image-20250213180134525](./Editor/image-20250213180134525.png)

### VSCode

#### 快捷键

* 查文件：`ctrl + P`，@追加符号，冒号追加行

* 头文件和源文件切换：`option + O`
  * 搜索switch获知快捷键
* 折叠函数：
  * 折叠：`Command K + 1/2/3/4` （按住command）
  * unfold：`Command K + J`

* 跳转前一次/后一次光标位置：`ctrl + - ` / `shift + ctrl + -`
* Format： `Option + Shift + F` 
* 历史打开文件切换：`ctrl + TAB`
* `ctrl + command + P`
  * Settings

* 打开终端：ctrl + `

#### 插件

参考「dotfiles：README」




#### Format

* Yapf
  * `pip install yapf`
  *  `Option + Shift +F` 自动格式化代码
  * .vscode/settings.json

```
{
	"python.linting.enabled": true,
	"python.linting.pylintPath": "pylint",
	"editor.formatOnSave": false,
	"python.formatting.provider": "yapf", // or "black" here
	"python.linting.pylintEnabled": false,
	"python.formatting.yapfArgs": [
		"--style={based_on_style: google, indent_width: 2}" // column_limit: 80
	]
}
```



#### clang系列

##### 安装clang

```shell
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-13.0.1/clang+llvm-13.0.1-x86_64-linux-gnu-ubuntu-18.04.tar.xz
tar xvf clang+llvm-13.0.1-x86_64-linux-gnu-ubuntu-18.04.tar.xz

sudo ln -s xxx/bin/clang /usr/bin/clang-13.0
```

* clang-format: https://clang.llvm.org/docs/ClangFormat.html
  * style-options: https://clang.llvm.org/docs/ClangFormatStyleOptions.html
  * `clang-format -style=llvm|Google -dump-config > .clang-format`

```shell
# 格式化main.cpp, 结果直接写到main.cpp
clang-format -i main.cpp
# 支持对指定行格式化，格式化main.cpp的第1，2行
clang-format -lines=1:2 main.cpp
```

* clang-tidy: https://clang.llvm.org/extra/clang-tidy/
* clangd插件：https://clangd.llvm.org/installation
  * `sudo apt install clangd-13`
  * command-p # 跳转符号

```yaml
---
Checks: >
  -*,
  bugprone-*,
  clang-analyzer-*,
  cppcoreguidelines-*,
  -cppcoreguidelines-avoid-c-arrays,
  -cppcoreguidelines-pro-type-cstyle-cast,
  -cppcoreguidelines-pro-bounds-constant-array-index,
  -cppcoreguidelines-pro-type-union-access,
  -cppcoreguidelines-pro-type-vararg,
  -cppcoreguidelines-avoid-magic-numbers,
  -cppcoreguidelines-avoid-non-const-global-variables,
  -cppcoreguidelines-pro-bounds-array-to-pointer-decay,
  -cppcoreguidelines-special-member-functions,
  -cppcoreguidelines-pro-bounds-pointer-arithmetic,
  hicpp-*,
  -hicpp-avoid-c-arrays,
  -hicpp-use-auto,
  -hicpp-vararg,
  -hicpp-no-array-decay,
  -hicpp-signed-bitwise,
  -hicpp-special-member-functions,
  modernize-*,
  -modernize-use-trailing-return-type,
  -modernize-avoid-c-arrays,
  -modernize-pass-by-value,
  -modernize-avoid-bind,
  -modernize-use-auto,
  performance-*,
  -performance-no-int-to-ptr,
  portability-*,
  readability-*,
  -readability-magic-numbers,
  -readability-redundant-access-specifiers,
  -readability-convert-member-functions-to-static,
  -readability-implicit-bool-conversion,
  -readability-identifier-length

WarningsAsErrors: ''
HeaderFilterRegex: ''
FormatStyle: none
InheritParentConfig: true
User: gycherish
CheckOptions:
  - { key: readability-identifier-naming.AbstractClassPrefix, value: I }
  - { key: readability-identifier-naming.AbstractClassCase, value: CamelCase }
  - { key: readability-identifier-naming.ClassCase, value: CamelCase }
  - { key: readability-identifier-naming.ClassMemberCase, value: camelBack }
  - { key: readability-identifier-naming.ClassMemberPrefix, value: m_ }
  - { key: readability-identifier-naming.FunctionCase, value: camelBack }
  - { key: readability-identifier-naming.EnumCase, value: CamelCase }
  - { key: readability-identifier-naming.EnumConstantCase, value: CamelCase }
  - { key: readability-identifier-naming.GlobalConstantCase, value: UPPER_CASE }
  - { key: readability-identifier-naming.NamespaceCase, value: lower_case }
  - { key: readability-identifier-naming.ProtectedMemberCase, value: camelBack }
  - { key: readability-identifier-naming.ProtectedMemberPrefix, value: m_ }
  - { key: readability-identifier-naming.PrivateMemberCase, value: camelBack }
  - { key: readability-identifier-naming.PrivateMemberPrefix, value: m_ }
  - { key: readability-identifier-naming.StructCase, value: CamelCase }
  - { key: readability-identifier-naming.TemplateParameterCase, value: CamelCase }
  - { key: readability-identifier-naming.VariableCase, value: camelBack }
...
```





#### json配置

##### launch.json

* VSCode with GDB

  * sourceFileMap 解决找不到源文件的问题
  * `gdb --directory`

```
{  
    "version": "0.2.0",
    "configurations": [
        {   //出现在vscode界面上的名字
            "name": "(gdb) 启动",
            // debugger类型 这是gdb
            "type": "cppdbg",
            "request": "launch",
             //可执行文件位置
            "program": "/home/huangruiteng/../workspace/program",
            "args": ["--arg1=abc", "--directory=/home/huangruiteng/.../workspace"],
            //是否进入后暂停
            "stopAtEntry": false,
            //工作目录
            "cwd": "/home/huangruiteng/.../workspace",
            "environment": [],
             //是否使用外部终端
            "externalConsole": false,
             // dubug之前要运行的任务
            //"preLaunchTask": "Build Fortran", 
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "为 gdb 启用整齐打印",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                },
                {
                    "description":  "将反汇编风格设置为 Intel",
                    "text": "-gdb-set disassembly-flavor intel",
                    "ignoreFailures": true
                }
            ],
            "sourceFileMap": {
                "/.../bazel-buildfarm/default/operations/.../abc.cpp": "/home/huangruiteng/.../workspace/.../abc.cpp"
            }
            // debug程序位置 gdb的位置
            "miDebuggerPath": "/usr/bin/gdb", 
        },
    ]
}
```

##### settings.json

```json
{
	"python.linting.enabled": true,
	"python.linting.pylintPath": "pylint",
	"editor.formatOnSave": false,
	"python.formatting.provider": "yapf", // or "black" here
	"python.linting.pylintEnabled": false,
	"python.formatting.yapfArgs": [
		"--style={based_on_style: google, indent_width: 2}" // column_limit: 80
	],
  "terminal.integrated.scrollback": 100000,
}
```



##### c_cpp_properties.json

* 配置 compile_commands.json
  * https://www.zhihu.com/question/353722203/answer/945067523


```JSON
{
    "configurations": [
        {
            "name": "Linux",
            "includePath": [
                "${workspaceFolder}/**",
                "${workspaceFolder}/../**"
            ],
            "defines": [],
            "compilerPath": "/usr/bin/clang-13.0",
            "cStandard": "c11",
            "cppStandard": "c++14",
            "intelliSenseMode": "linux-clang-x64",
            "compileCommands": "xxx/build/compile_commands.json",
            "compilerArgs": [
                "-O3"
            ],
            "configurationProvider": "ms-vscode.cmake-tools"
        }
    ],
    "version": 4
}
```

![cmake-tool](Editor/cmake-tool.png)

##### tasks.json（禁用c++/c后，不需要此文件）

```
{
    "tasks": [
        {
            "type": "cppbuild",
            "label": "C/C++: g++ 生成活动文件",
            "command": "/usr/bin/g++",
            "args": [
                "-fdiagnostics-color=always",
                "-g",
                "${fileDirname}/../a.cc",
                "${fileDirname}/../b.cc",
                "${fileDirname}/../c.cc",
                "${file}",
                "-o",
                "${fileDirname}/${fileBasenameNoExtension}",
                "-lpthread"
            ],
            "options": {
                "cwd": "${fileDirname}"
            },
            "problemMatcher": [
                "$gcc"
            ],
            "group": "build",
            "detail": "编译器: /usr/bin/g++"
        }
    ],
    "version": "2.0.0"
}
```
#### issues

* [remote ssh can't connect - Server installation process already in progress](https://github.com/microsoft/vscode-remote-release/issues/2507)
	* remove the hardlink `/home/sma/.vscode-server/bin/78a4c91400152c0f27ba4d363eb56d2835f9903a/vscode-remote-lock.sma.78a4c91400152c0f27ba4d363eb56d2835f9903a'`
	


### Sublime Text

* Ctrl + M 括号匹配

* Shift + Ctrl + M 选中该级括号内容

### Typora

* command + /  切换编辑模式
* shift + command + L 打开边栏
* control + command + 1/2/3 切换边栏类型
