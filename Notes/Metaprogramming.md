## Metaprogramming

[MIT 6.NULL - Metaprogramming](https://missing.csail.mit.edu/2020/metaprogramming/)

### Build systems

概念：dependencies, targets, rules

`make`和`Makefile`
* 根据modify time确定什么文件需要regenerate
```shell
target: prerequisite1 prerequisite2 ...
	command1
	command2 (需要tab)
```
```shell
paper.pdf: paper.tex plot-data.png
	pdflatex paper.tex

plot-%.png: %.dat plot.py
	./plot.py -i $*.dat -o $@
```


```shell
# specify all source files here
SRCS = hw.c helper.c

# specify target here (name of executable)
TARG = hw

# specify compiler, compile flags, and needed libs
CC   = gcc
OPTS = -Wall -O
LIBS = -lm

# this translates .c files in src list to .o’s
OBJS = $(SRCS:.c=.o)

# all is not really needed, but is used to generate the target, default directive
all: $(TARG)

# this generates the target executable
$(TARG): $(OBJS)
	$(CC) -o $(TARG) $(OBJS) $(LIBS)
	
# this is a generic rule for .o files
%.o: %.c
  $(CC) $(OPTS) -c $< -o $@

# and finally, a clean line
.PHONY: clean
clean:
	rm -f $(OBJS) $(TARG)
```
* 第一个directive是default goal
* indent后面的命令是建立依赖的语句
* [.PHONY](https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html)避免clean和名为clean的文件冲突

```shell
SUBDIRS = foo bar baz

.PHONY: subdirs $(SUBDIRS)

subdirs: $(SUBDIRS)

$(SUBDIRS):
        $(MAKE) -C $@

foo: baz
```

* 配合[git ls-files](https://git-scm.com/docs/git-ls-files)，写make的[标准targets](https://www.gnu.org/software/make/manual/html_node/Standard-Targets.html#Standard-Targets)
* 可以利用`.git/hooks`中的[`pre-commit`](https://git-scm.com/docs/githooks#_pre_commit)在每次commit之前make特定的文件

### Dependency management
概念：repository, versioning, version number, [semantic versioning](https://semver.org/)

- If a new release does not change the API, increase the patch version.
- If you *add* to your API in a backwards-compatible way, increase the minor version.
- If you change the API in a non-backwards-compatible way, increase the major version.

这三条是入门概括。严格说，patch 对应兼容的 bug 修复；“公共 API 没变”并不意味着只能升 patch，重大内部功能或改进也可升 minor。完整规则见下文。

- [Rust's build system](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html)，可帮助理解版本号以及dependency管理

lock file: a file that lists the exact version you are *currently* depending on of each dependency

* vendoring: copy all the code of your dependencies into your own project

makedepend工具能帮助寻找依赖

#### SemVer：兼容性承诺与发布

来源：[Semantic Versioning 2.0.0](https://semver.org/#semantic-versioning-specification-semver)、[中文译文](https://semver.org/lang/zh-CN/)、[FAQ](https://semver.org/#faq)。以下按英文规范归纳；原规范由 Tom Preston-Werner 发起，采用 [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/)。

SemVer 用版本号传递公共 API 的兼容性变化，让依赖方判断升级范围。前提是先明确公共 API；代码或文档都可以定义契约，但边界应精确、完整。版本数字本身不能证明兼容性。

标准格式为 `MAJOR.MINOR.PATCH`，三项均为非负整数、不能带前导零，按数值递增，如 `1.9.0 → 1.10.0`。对稳定版本（major > 0）：

| 变更 | 版本处理 | 从 `2.4.7` 出发的例子 |
| --- | --- | --- |
| 仅修复错误，保持向后兼容 | 必须升 patch | `2.4.8` |
| 增加兼容的公共功能，或将公共功能标记为 deprecated | 必须升 minor，patch 归零 | `2.5.0` |
| 公共 API 有不兼容变化 | 必须升 major，minor / patch 归零 | `3.0.0` |
| 私有实现有重大新功能或改进 | 可以升 minor | `2.5.0` |

minor 可以包含 patch 级变化，major 可以包含两者；同批变更中只要有不兼容 API 变化，就应按 major 发布。判断依据是契约影响，而非代码行数或改动难度。

- `0.y.z` 用于初始开发，公共 API 尚不稳定，规范允许随时变化；不能直接套用稳定版本的兼容性承诺。`1.0.0` 表示公共 API 已界定，并以它为后续版本变化的基准。
- 弃用先更新文档并发一个 minor，移除时升 major；正式移除前，至少留一个包含弃用信息的 minor，让使用者迁移。
- 已发布版本的内容不可修改，修正必须发布新版本。若误把 breaking change 发成 minor，应记录问题并发新 minor 恢复兼容，不能覆盖旧包；若恢复行为又会严重影响使用者，FAQ 建议按实际影响判断是否发 major。
- 更新依赖也看公共契约与目的：不改变公共 API 时，修 bug 与增加功能分别按 patch / minor 判断；不能仅凭“依赖版本变了”就认定为 breaking change。

工程应用：项目可把函数签名、承诺的行为、CLI、配置格式或对外数据 schema 纳入公共契约。若破坏已承诺的行为，即使签名不变也可能不兼容；未声明的内部实现则不能自动等同于公共 API。

#### 预发布、构建信息与依赖升级

扩展格式：`MAJOR.MINOR.PATCH-prerelease+build`，两个后缀均可选，例如 `2.5.0-rc.1+sha.a1b2c3`。

- `-prerelease` 表示先行版，可能尚未满足该正式版本预期的兼容性；它低于同一版本核心的正式版。`+build` 是构建元数据，比较优先级时必须忽略；`2.5.0+001` 与 `2.5.0+002` 优先级相同，不代表产物内容相同。
- 两种后缀都是以点分隔的非空标识符，只能用 ASCII 字母、数字和 `-`；先行版的纯数字标识符不能带前导零，因此 `rc.01` 非法，构建元数据 `+001` 合法。
- 先比较 major / minor / patch 的数值，再比较先行版标识符：纯数字按数值，含字母或连字符按 ASCII；纯数字低于非数字；共同前缀相同时，标识符更多的优先级更高。

```text
2.5.0-alpha < 2.5.0-alpha.1 < 2.5.0-alpha.beta < 2.5.0-beta
2.5.0-beta.2 < 2.5.0-beta.10 < 2.5.0-rc.1 < 2.5.0
```

`v2.5.0` 是常见 Git tag 写法，真正的 SemVer 字符串为 `2.5.0`，不包含 `v`。

若依赖了 `2.4.0` 新增的 API，可将兼容的正式版本范围设为 `>=2.4.0, <3.0.0`；范围过紧会锁死升级，过松会接受潜在的不兼容版本。`^` / `~` 的含义、`0.y.z` 的范围策略及是否纳入先行版由具体包管理器定义，不属于 SemVer 本身。版本范围决定允许升级到哪里，lock file 固定当前实际解析的依赖；两者职责不同。

工程上，先声明契约，再用兼容性测试验证消费者行为，最后按影响发布并记录迁移路径。SemVer 是维护者的承诺，升级仍需验证，不能用“版本号允许”替代测试。接口设计与质量保障见 [Software Engineering](./Software-Engineering.md#interfaces)。

### Continuous integration(CI) systems

“stuff that runs whenever your code changes”

* e.g. Travis CI, Azure Pipelines, and GitHub Actions
* Pages is a CI action that runs the Jekyll blog software on every push to `master` and makes the built site available on a particular GitHub domain

**testing**

- Test suite: a collective term for all the tests
- Unit test: a “micro-test” that tests a specific feature in isolation
- Integration test: a “macro-test” that runs a larger part of the system to check that different feature or components work *together*.
- Regression test: a test that implements a particular pattern that *previously* caused a bug to ensure that the bug does not resurface.
- Mocking: the replace a function, module, or type with a fake implementation to avoid testing unrelated functionality. For example, you might “mock the network” or “mock the disk”.

### Github Pages
1. Set up a simple auto-published page using [GitHub Pages](https://help.github.com/en/actions/automating-your-workflow-with-github-actions). Add a [GitHub Action](https://github.com/features/actions) to the repository to run `shellcheck` on any shell files in that repository (here is [one way to do it](https://github.com/marketplace/actions/shellcheck)). Check that it works!
2. [Build your own](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/building-actions) GitHub action to run [`proselint`](http://proselint.com/) or [`write-good`](https://github.com/btford/write-good) on all the `.md` files in the repository. Enable it in your repository, and check that it works by filing a pull request with a typo in it.


#### Inbox
个人blog的建立：

调研之后决定用动态blog，[halo](https://halo.run/)是傻瓜式操作，[在阿里云上部署](https://blog.csdn.net/weixin_43160252/article/details/104864279)




