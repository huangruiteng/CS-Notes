## Debugging and Profiling

[toc]

### Testing

* [Test-driven development(TDD)](https://en.wikipedia.org/wiki/Test-driven_development) 软件开发流程
  * Fake and mock object methods
* 也可参考【C++笔记】《The Art of Writing Readable Code》- chpt 14
* 也可参考【protobuf等基本工具笔记】gtest



[MIT 6.NULL - Debugging and Profiling](https://missing.csail.mit.edu/2020/debugging-profiling/)

### Debugging

#### 概要

* 提问的艺术 —— 如何有效地提问、Debug
  * https://www.yuque.com/keep/up/ur2rk0giu3mghqdc

#### Printf Debugging and Logging
脑力劳动debug，借助打印信息思考和推断问题所在

信息除了Printf，还可以Logging，更灵活（可以输出到文件、sockets、remote servers），可复用

[Here](https://missing.csail.mit.edu/static/files/logger.py) is an example code that logs messages:

```shell
$ python logger.py
# Raw output as with just prints
python logger.py log
# Log formatted output
$ python logger.py log ERROR
# Print only ERROR levels and above
$ python logger.py color
# Color formatted output
```
利用颜色信息： [ANSI escape codes](https://en.wikipedia.org/wiki/ANSI_escape_code)

```shell
#!/usr/bin/env bash
for R in $(seq 0 20 255); do
    for G in $(seq 0 20 255); do
        for B in $(seq 0 20 255); do
            printf "\e[38;2;${R};${G};${B}m█\e[0m";
        done
    done
done
```

#### HTTP 调用：保留原始错误与关联证据

- **先保留 HTTP 事实，再解释解析异常**：记录状态码、Content-Type、耗时，以及按白名单保留的响应头和脱敏、限长的正文摘要，再尝试解析预期格式。网关可能返回文本或 HTML，盲调 `response.json()` 会产生第二层解析错误；反过来，JSON 解码成功也不等于 HTTP 请求成功。[Requests：JSON 与状态码的区别](https://requests.readthedocs.io/en/latest/user/quickstart/#json-response-content)
- **标识的生成、传播、回传是三件事**：客户端自带 request ID 不保证服务端采纳或原样返回；没有响应 ID，只说明调用方没拿到它，不能证明服务端没生成 ID、没记录日志或没收到请求。以 Envoy 为例，请求 ID 生成、外部 ID 保留、响应回传分别配置；需要用接收端日志验证关联，而不是把客户端标记当成已确认的服务端 ID。[HTTP connection manager](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/network/http_connection_manager/v3/http_connection_manager.proto)
- **Request ID 不天然等于 Trace ID**：请求关联标识的作用域由系统约定；W3C `traceparent` 携带 trace-id、parent-id 与 flags，服务必须正确传播并记录才能关联调用。仅有一个响应头或一个 ID，不足以还原完整调用链。[W3C Trace Context](https://www.w3.org/TR/trace-context/#traceparent-header)
- **软件标识不是节点身份证明**：`Server` 响应头描述软件产品，可能被省略或改写；同类代理也可以部署在多个位置。定位需结合受控时间窗口、请求关联记录和实际处理日志，不能仅凭产品名称锁定故障节点。[RFC 9110 §10.2.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.4)

#### Third party logs

* 一个简化版 Google's logging
  * https://github.com/google/re2/blob/main/util/logging.h

* UNIX系统中第三方库的log常存在`/var/log`
  * the [NGINX](https://www.nginx.com/) webserver places its logs under `/var/log/nginx`
* `systemd`, a system daemon that controls many things in your system such as which services are enabled and running 
  * `/var/log/journal`，可用`journalctl`显示
  * macOS上`var/log/system.log`，但更多人用system log，用 [`log show`](https://www.manpagez.com/man/1/log/) 显示
  * 参考[data wrangling]()，需要对log信息处理，也可以用[lvav](http://lnav.org/)，体验更好

```shell
logger "Hello Logs"
# On macOS
log show --last 1m | grep Hello
# On Linux
journalctl --since "1m ago" | grep Hello
```

#### Debuggers

##### gdb

**C++**: [`gdb`](https://www.gnu.org/software/gdb/) (and its quality of life modification [`pwndbg`](https://github.com/pwndbg/pwndbg)) and [`lldb`](https://lldb.llvm.org/)

[Debugging with GDB 教程](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html)

gdb：c(continue), l(ist), s(tep), n(ext), b(reak), p(rint), r(eturn), run, q(uit), watch

* up, down
  * `up n`
  * `up-silently n`

* 特有：start, finish, cond, disable, where
  * `cond 3 this==0xXXX`

* 参数
  * `gdb --args sleep 20` debug带参数的binary
  * `-q`  quiet模式
  * `-ex`: 执行gdb命令
    * `-ex "run"`
  
* bt(backtrace), frame X 进帧
* `info b`
* `watch -l ` 同时监视表达式本身和表达式指向的内容
* `attach $pid` debug正在运行的进程
* `ptype` 打印变量类型；打印stl使用 [python pretty print](https://gist.github.com/daverigby/99dae6997bced43a8fcdbfcb15e36116)
* `gcore` attach后制造core文件
* `call`
  *  `call (void)'xxx::Logger::setLogLevel'(3)` 注意引号让gdb不会因为找不到符号而报错
  * [how does gdb call functions](https://jvns.ca/blog/2018/01/04/how-does-gdb-call-functions/)


```c++
//增加print的可读性
set print pretty on/off
//显示完整 STL 结构
set print elements 0

//显示智能指针对象指向的变量
p ((Object*) my_ptr)->attribute //利用类型转换
p *(my_ptr._M_ptr)
  
//显示vector内部值
p *(my_vec._M_impl._M_start)@my_vec.size()  //打印大小
p *(my_vec._M_impl._M_start+0)
p (my_vec._M_impl._M_start)[N-1] //打印第N个成员
p *(my_vec._M_impl._M_start)@N  //打印前N个成员
  
//pb相关
p *(std::string*)(X.rep_.elements) //repeated string, 字段X

```

* Q: 都是问号
  * info sharedlibrary
  * set solib-search-path $PATH

##### [gdb的多线程调试](https://blog.csdn.net/lf_2016/article/details/59741705)

* info frame
* info args
* info locals

* info threads:显示当前可调试的所有线程,GDB会给每一个线程都分配一个ID。前面有*的线程是当前正在调试的线程。
* `info reg`
* thread ID:切换当前调试的线程为指定ID的线程。
* `thread apply all command`:让所有被调试的线程都执行command命令。
  * `thread apply all bt` **把各个线程的调用栈打出来**

* `thread apply ID1 ID2 … command`:让线程编号是ID1，ID2…等等的线程都执行command命令。
* `set scheduler-locking on|off|step`:在使用step或continue命令调试当前被调试线程的时候，其他线程也是同时执行的，如果我们只想要被调试的线程执行，而其他线程停止等待，那就要锁定要调试的线程，只让他运行。
  * off:不锁定任何线程，所有线程都执行。
  * on:只有当前被调试的线程会执行。
  * step:阻止其他线程在当前线程单步调试的时候抢占当前线程。只有当next、continue、util以及finish的时候，其他线程才会获得重新运行的
* `show scheduler-locking`：查看当前锁定线程的模式。



* `gdb -q --batch -ex "set height 0" -ex "thread apply all bt full" [可执行文件] [core文件]`
  * -q: 不打印gdb的版权消息
  * --batch: 执行批处理，不进入交互模式
  * -ex: 执行gdb 命令
  * "set height 0": 不对输出进行分页
    



Gdb 的汇编级别调试

* `ni`, `si`



打印变量到文件

```c++
set logging file $file_name
set logging on
thread apply all bt
set logging off
set logging overwrite on/off
set logging redirect on/off
show logging
```



Gdb STL support tools: https://sourceware.org/gdb/wiki/STLSupport



##### [gdb-watchpoint](https://undo.io/resources/gdb-watchpoint) MUSTDO

* [How to search memory for a byte sequence with GDB command find?](https://undo.io/resources/gdb-watchpoint/how-search-byte-sequence-memory-gdb-command-find/)
* [Debug mode](https://undo.io/resources/gdb-watchpoint/build-for-debug-in-gdb/)
  * DWARF is a pun on ELF, which stands for Executable and Linking Format. DWARF goes with ELF.
  * dwarf的不同版本
    * -g2: dwarf4
    * -g3
    * `-g3 -Og` 平衡性能和debug信息
  * `readelf --debug-dump a.out | less`
  * `readelf --debug-dump=loc a.out | less`
  * `print $pc`
* [Split-dwarf](https://undo.io/resources/gdb-watchpoint/reduce-binary-size-compile-time-split-dwarf/)
  * Even with incremental builds, the linker still needs to read all of the debug information in order to do things like remove duplications, for example.



##### 100个gdb小技巧

https://wizardforcel.gitbooks.io/100-gdb-tips/content/index.html

6. 打印

* 打印变量
  * `p/t` 打印二进制变量

* 打印内存的值
  * 格式为“`x/nfu addr`”。含义为以`f`格式打印从`addr`开始的`n`个长度单元为`u`的内存值
    * n：输出单元的个数。
    * f：是输出格式。比如`x`是以16进制形式输出，`o`是以8进制形式输出，`t`是二进制输出。
    * u：标明一个单元的长度。`b`是一个`byte`，`h`是两个`byte`（halfword），`w`是四个`byte`（word），`g`是八个`byte`（giant word）

* gdb with Gtest
  * `--gtest_break_on_failure`





**Python**: [`ipdb`](https://pypi.org/project/ipdb/) is an improved `pdb` that uses the [`IPython`](https://ipython.org) REPL enabling tab completion, syntax highlighting, better tracebacks,  and better introspection while retaining the same interface as the `pdb` module.

* ipdb命令: `p locals()`, j(ump), pp([`pprint`](https://docs.python.org/3/library/pprint.html)), restart
* [pdb turorial](https://github.com/spiside/pdb-tutorial), [pdb depth tutorial](https://realpython.com/python-debugging-pdb)

[CS107 GDB and Debugging教程](https://web.stanford.edu/class/archive/cs/cs107/cs107.1202/resources/gdb)

[CS107 Software Testing Strategies](https://web.stanford.edu/class/archive/cs/cs107/cs107.1202/testing.html)

[lldb的使用](https://www.jianshu.com/p/9a71329d5c4d)

[macOS上配置VSCode的gdb调试环境](https://zhuanlan.zhihu.com/p/106935263?utm_source=wechat_session)  

```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "envFile": "${workspaceFolder}/.env",
            "console": "integratedTerminal",
            "env": {
              "ENV1":"123",
              "ENV2":"abc",
            },
            "args": ["-version","4"]
        }
    ]
}
```

#### Sanitizers

[如何高效解决 C++内存问题，Apache Doris 实践之路｜技术解析](https://zhuanlan.zhihu.com/p/561441347) TODO

* [ASan](https://en.wikipedia.org/wiki/AddressSanitizer)
  * `-fsanitize=address`

*  [UBSan](https://developers.redhat.com/blog/2014/10/16/gcc-undefined-behavior-sanitizer-ubsan/)
  * `-fsanitize=undefined`

* [ThreadSan](https://github.com/google/sanitizers/wiki/ThreadSanitizerCppManual)
  * `-fsanitize=thread`

* Note
  * 在程序里使用 Pthreads 库有一个额外的好处: 分析工具认得它们，懂得其语意。 线程分析工具如 Intel Thread Checker 和 Valgrind-Helgrind 等能识别 Pthreads 调 用，并依据 [happens-before](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) (TODO) 关系分析程序有无 data race。



#### Specialized Tools

Under some circumstances, you may need to look at the network packets to figure out the issue in your program. Tools like [`tcpdump`](https://www.man7.org/linux/man-pages/man1/tcpdump.1.html) and [Wireshark](https://www.wireshark.org/) are network packet analyzers that let you read the contents of network packets and filter them based on different criteria.

For web development, the Chrome/Firefox developer tools are quite handy. They feature a large number of tools, including:

- Source code - Inspect the HTML/CSS/JS source code of any website.
- Live HTML, CSS, JS modification - Change the website content,  styles and behavior to test (you can see for yourself that website  screenshots are not valid proofs).
- Javascript shell - Execute commands in the JS REPL.
- Network - Analyze the requests timeline.
- Storage - Look into the Cookies and local application storage.

#### Static Analysis
* [Static Analysis介绍](https://en.wikipedia.org/wiki/Static_program_analysis)
  * formal methods 
  * Python: [`pyflakes`](https://pypi.org/project/pyflakes) , [`mypy`](http://mypy-lang.org/), [`shellcheck`](https://www.shellcheck.net/)
  * English也有静态分析！
  * 静态分析可以融入编辑器, vim:[`ale`](https://vimawesome.com/plugin/ale) or [`syntastic`](https://vimawesome.com/plugin/syntastic) 
* [Static Analysis仓库整理](https://github.com/analysis-tools-dev/static-analysis#go)
* 《C/C++ thread safety analysis》，见【compiling笔记】，clang线程安全注解
* [awesome linters整理](https://github.com/caramelomartins/awesome-linters#go)
  * Python:  [`pylint`](https://github.com/PyCQA/pylint) and [`pep8`](https://pypi.org/project/pep8/) 是stylistic linters，[`bandit`](https://pypi.org/project/bandit/) 可查security问题
    * `python -m autopep8 -i -r $FOLDER`
* A complementary tool to stylistic linting are code formatters such as [`black`](https://github.com/psf/black) for Python, `gofmt` for Go, `rustfmt` for Rust or [`prettier`](https://prettier.io/) for JavaScript, HTML and CSS.

#### Coredump 相关

* Linux 默认会把 core dump 写到当前目录，而且文件名是固定的 core。为了不让新的 core dump 文件冲掉旧的，我们可以通过 sysctl 设置 kernel.core_pattern 参数(也可以修改 /proc/sys/kernel/core_pattern)，让每次 core dump 都产生不同的文件
  * core_pattern: `|/usr/share/apport/apport %p %s %c %d %P`
  * https://wiki.ubuntu.com/Apport
  * 修改core位置
    * `echo "/data/coredump/core.%e.%p" > /proc/sys/kernel/core_pattern`
    * %E：程序文件的完整路径（路径中的/会被!替代）
    * %p：进程 ID
    * %t：进程奔溃的时间戳
    * %s：哪个信号让进程奔溃
  * `ulimit -c unlimited`
  * 判断是否是core文件：`readelf -h core`

#### Dynamic Tracing

* [动态追踪技术](https://blog.openresty.com.cn/cn/dynamic-tracing/)
  * 动态追踪技术允许我们使用非侵入式的方式，不用去修改我们的操作系统内核，不用去修改我们的应用程序，也不用去修改我们的业务代码或者任何配置，就可以快速高效地精确获取我们想要的信息，第一手的信息，从而帮助定位我们正在排查的各种问题
  * 调试技术需要贯通各个软件层次的抽象和封装
  * 火焰图：on-CPU, off-CPU
* dtrace
  * Even if what you are trying to debug is a black box binary there are tools that can help you with that. Whenever programs need to perform actions that only the kernel can, they use [System Calls](https://en.wikipedia.org/wiki/System_call). There are commands that let you trace the syscalls your program makes. In Linux there’s [`strace`](https://www.man7.org/linux/man-pages/man1/strace.1.html) and macOS and BSD have [`dtrace`](http://dtrace.org/blogs/about/). `dtrace` can be tricky to use because it uses its own `D` language, but there is a wrapper called [`dtruss`](https://www.manpagez.com/man/1/dtruss/) that provides an interface more similar to `strace` (more details [here](https://8thlight.com/blog/colin-jones/2015/11/06/dtrace-even-better-than-strace-for-osx.html)).
  * [strace入门](https://blogs.oracle.com/linux/strace-the-sysadmins-microscope-v2)
  * 参考snippet - cpu-profiling


* [systemtap](https://sourceware.org/systemtap/documentation.html)
* [eBPF](https://www.brendangregg.com/blog/2015-05-15/ebpf-one-small-step.html)、Hardware Performance Counter




### Profiling

* profilers和monitoring tools的意义：[premature optimization is the root of all evil](http://wiki.c2.com/?PrematureOptimization)
* CPU usage和CPU使用率
  - **CPU Usage**: CPU Usage是指单位时间内，进程使用了多少核心的CPU: 包括该进程用户态和内核态的开销。对于Pod来说，即单位时间内pod内所有进程使用了多少核心的CPU。
  - **CPU使用率**: CPU利用率是指单位时间内: CPU usage/CPU总核心数。

* [时间概念](https://stackoverflow.com/questions/556405/what-do-real-user-and-sys-mean-in-the-output-of-time1)：real/user/system time

  * real time(wall time): 真实时间, user: 用户态耗时, sys: 内核态耗时, user+sys: 实际用时

  * time指令


* Jeff Dean推崇的back-of-the-envelope方法估算系统性能，这是一篇很好的[文章](http://highscalability.com/blog/2011/1/26/google-pro-tip-use-back-of-the-envelope-calculations-to-choo.html)，里面有各种实用数据

  * scalable counter

  * keep per user comment indexes when paging through comments

* 性能优化思路：

  * CPU利用率 与 latency 的平衡
  * 提高CPU利用率再优化latency的思路
    * 暴露其他性能问题：在比较高的CPU使用率下，请求latency对CPU使用会变得比较敏感。 
      - 引入糟糕的代码引入，会导致明显的latency上升，从而被及时发现。 
      - 非预期的请求burst，会导致latency pct99明显上升。 
      - 糟糕的流量调度，也会导致latency pct99明显上升。
    * 提升对基础组件的要求
      * 容器调度、超售
      * 容灾降级、auto scale
      * 流量动态调度
      * 网络和中间件
  * 分析CPU是否是瓶颈
    * nr_throttled、nr_periods
    * [阿里云容器方案](https://www.alibabacloud.com/help/en/elastic-compute-service/latest/enable-the-cpu-burst-feature-for-cgroup-v1)
      - [Linux sched burst feature](https://www.kernel.org/doc/html/latest/scheduler/sched-bwc.html#burst-feature)
      - [lkml: sched burst feature ](https://lkml.org/lkml/2019/11/26/196)
      - [让容器跑的更快：CPU Burst技术实践](https://mp.weixin.qq.com/s?spm=a2c6h.12873639.0.0.cadb37a5JMOx9N&__biz=MzUzNzYxNjAzMg==&mid=2247519934&idx=1&sn=e87d2ab211516965ae3ffb51297df767&chksm=fae68571cd910c67b203d0d95023357a29ef9cd1ff956b3784ac3ebf490edfeb1f1ac6d75f74&scene=21#wechat_redirect)
    * [AWS 虚拟机方案](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances.html)
    * CPU队列长度
      * [bcc工具](https://github.com/iovisor/bcc/blob/master/tools/runqlen.py)
      * [bpftrace工具](https://github.com/iovisor/bpftrace/blob/master/tools/runqlen.bt)
    * CPU调度延迟
      * [bcc](https://github.com/iovisor/bcc/blob/master/tools/runqlat.py)
      * [bpftrace](https://github.com/iovisor/bpftrace/blob/master/tools/runqlat.bt)
    * task非自愿抢占
      * [CFS算法](https://notes.eddyerburgh.me/operating-systems/linux/process-scheduling#fair-scheduling)
      * ./ivcs.bt
      * bpftrace
  * CPU cache与TLB
    * 容器环境下，由于内核是共享的，租户之间很可能通过TLB和CPU cache进行相互影响。
    * [pmc工具: tlbstat](https://github.com/brendangregg/pmc-cloud-tools/blob/master/tlbstat)
      - K_CYCLES: CPU Cycles x 1000
      - K_INSTR: CPU Instructions x 1000
      - IPC: Instructions-Per-Cycle
      - DTLB_WALKS: Data TLB walks (count)
      - ITLB_WALKS: Instruction TLB walks (count)
      - K_DTLBCYC: Cycles at least one Page Miss Handler (PMH) is active with data TLB walks x 1000
      - K_ITLBCYC: Cycles at least one PMH is active with instr. TLB walks x 1000
      - DTLB%: Data TLB active cycles as a ratio of total cycles，即：DTLB miss花费的CPU开销。
      - ITLB%: Instruction TLB active cycles as a ratio of total cycles，即：ITLB miss花费的CPU开销。
    * [pmc工具： pmcarch](https://github.com/brendangregg/pmc-cloud-tools/blob/master/pmcarch)
      - K_CYCLES: CPU Cycles x 1000
      - K_INSTR: CPU Instructions x 1000
      - IPC: Instructions-Per-Cycle
      - BMR%: Branch Misprediction Ratio, as a percentage
      - LLC%: Last Level Cache hit ratio, as a percentage
    * ![71e328e7-e873-4336-b029-740b38218e78](Debugging-and-Profiling/cpu-cache.png)

```c++
#!/usr/bin/env bpftrace

#include <linux/sched.h>

BEGIN
{
        printf("Count involutary context switch... Hit Ctrl-C to end.\n");
}

tracepoint:sched:sched_switch
{
        if (args->prev_state == TASK_RUNNING) { // involutary
                @involutary[args->prev_comm] = count();
        }
}
i:s:1
{
        print(@involutary);
        clear(@involutary);
}
```



* QPS/单核QPS/latency等指标和CPU使用率的关系
  * CPU使用率从40%到60%阶段，Success QPS从2000左右增加到了3500（增加了约75%）
  * CPU利用率与[mesh过载保护](https://my.oschina.net/u/4843764/blog/5559303)
  * 单核QPS随QPS上升而上升，呈抛物线状
    * 基础开销（mesh/go runtime调度, sysmon等）被逐渐均摊，基础开销边际成本变得更低
    * QPS上升，IPC变高； 但高峰期物理机负载高的时候IPC低
  * CPU利用率从60%到80%，latency p99变化很大

#### Profilers

*   **CPU**: [perf](https://perf.wiki.kernel.org/index.php/Main_Page)

* Python
  * cProfile: `python -m cProfile -s tottime grep.py 1000 '^(import|\s*def)[^,]*$' *.py`
  *  [`line_profiler`](https://github.com/pyutils/line_profiler) 可逐行输出，用`@prifile`decorator标注函数, `kernprof -l -v a.py`

```Python
b = [2] * (2 * 10 ** 7)
del b

kernprof -l -v sorts.py
python -m line_profiler sorts.py.lprof
```

**Event Profiling** 

##### perf

[`perf`](https://www.man7.org/linux/man-pages/man1/perf.1.html) 

[perf的介绍与使用](https://www.cnblogs.com/arnoldlu/p/6241297.html)

[perf documentation](https://android.googlesource.com/kernel/msm/+/android-7.1.0_r0.2/tools/perf/Documentation)

```shell
sudo apt-get install linux-tools-$(uname -r) linux-tools-generic -y
```

- `perf list` - List the events that can be traced with perf
- `perf stat COMMAND ARG1 ARG2` - Gets counts of different events related a process or command
  - [odd definition of L1-dcache-load-misses](https://www.spinics.net/lists/linux-perf-users/msg07969.html)
- `perf record COMMAND ARG1 ARG2` - Records the run of a command and saves the statistical data into a file called `perf.data`
- `perf report` - Formats and prints the data collected in `perf.data`

```shell
perf help
(sudo) perf top --call-graph graph
								-t $thread_id

sudo perf record stress -c 1 # record->stat
sudo perf report

perf stat -e cache-misses,cache-references,instructions,cycles,faults,branch-instructions,branch-misses,L1-dcache-stores,L1-dcache-store-misses,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses,LLC-stores,LLC-store-misses,dTLB-loads,dTLB-load-misses,iTLB-loads,iTLB-load-misses -p $pid

perf record -e cache-misses -p $pid
perf report --sort comm,dso,symbol

sudo perf kmem --alloc --caller --slab stat
sudo perf sched script
```



**Survey of C++ profiling techniques: gprof vs valgrind vs perf vs gperftools**

https://stackoverflow.com/questions/375913/how-can-i-profile-c-code-running-on-linux/378024#378024

##### gprof

http://unix.ba/text/runtime-profiling-with-gprof/

http://sam.zoy.org/writings/programming/gprof.html

编译参数 `-Og -pg`，前者是debug mode，后者是动态trace

##### 代码分析

`clock_gettime(CLOCK_THREAD_CPUTIME_ID)` 统计当前线程的CPU时间开销（不包含系统调用的开销）

**内存泄露问题**

* [Valgrind](https://valgrind.org/)

```c++
VALGRIND_LIB=/usr/lib/valgrind valgrind --tool=callgrind --dump-instr=yes --collect-jumps=yes -v --instr-atstart=no ./bin
# 这条命令暂时还没跑通看到 output
```

* `gdb`
* [ps_mem的使用](https://linux.cn/article-8639-1.html)

**Visualization**

* [Flame Graph](http://www.brendangregg.com/flamegraphs.html)
*  [`pycallgraph`](http://pycallgraph.slowchop.com/en/master/) 

#### Resource Monitoring

- **General Monitoring** - Probably the most popular is [`htop`](https://hisham.hm/htop/index.php), which is an improved version of [`top`](https://www.man7.org/linux/man-pages/man1/top.1.html). `htop` presents various statistics for the currently running processes on the system. `htop` has a myriad of options and keybinds, some useful ones  are: `<F6>` to sort processes, `t` to show tree hierarchy and `h` to toggle threads.  See also [`glances`](https://nicolargo.github.io/glances/) for similar implementation with a great UI. For getting aggregate measures across all processes, [`dstat`](http://dag.wiee.rs/home-made/dstat/) is another nifty tool that computes real-time resource metrics for lots of different subsystems like I/O, networking, CPU utilization, context  switches, &c.
  - `dstat -nf`，n表示网络，f表示看详细信息
  - `lscpu`
  -  `cat /proc/cpuinfo` 查cpu信息，其中 flags 表示指令集支持
  -  ` dmidecode | grep "Memory Device$" | wc -l` 查内存条数量
- **I/O operations** - [`iotop`](https://www.man7.org/linux/man-pages/man8/iotop.8.html) displays live I/O usage information and is handy to check if a process is doing heavy I/O disk operations
- **Disk Usage** - [`df`](https://www.man7.org/linux/man-pages/man1/df.1.html) displays metrics per partitions and [`du`](http://man7.org/linux/man-pages/man1/du.1.html) displays disk usage per file for the current directory. In these tools the `-h` flag tells the program to print with human readable format. A more interactive version of `du` is [`ncdu`](https://dev.yorhel.nl/ncdu) which lets you navigate folders and delete files and folders as you navigate.
- **Memory Usage** - [`free`](https://www.man7.org/linux/man-pages/man1/free.1.html) displays the total amount of free and used memory in the system. Memory is also displayed in tools like `htop`.
- **Open Files** - [`lsof`](https://www.man7.org/linux/man-pages/man8/lsof.8.html)  lists file information about files opened by processes. It can be  quite useful for checking which process has opened a specific file.
- **Network Connections and Config** - [`ss`](https://www.man7.org/linux/man-pages/man8/ss.8.html) lets you monitor incoming and outgoing network packets statistics as well as interface statistics. A common use case of `ss` is figuring out what process is using a given port in a machine. For  displaying routing, network devices and interfaces you can use [`ip`](http://man7.org/linux/man-pages/man8/ip.8.html). Note that `netstat` and `ifconfig` have been deprecated in favor of the former tools respectively.
  - ss的[使用技巧](https://www.cnblogs.com/peida/archive/2013/03/11/2953420.html)，查端口占用通常用 `-nlp`，如果出现 (Not all processes could be identified, non-owned process info will not be shown, you would have to be root to see it all.) 是正常情况，意思就是没端口没被占用

- **Network Usage** -  [`nethogs`](https://github.com/raboof/nethogs) and [`iftop`](http://www.ex-parrot.com/pdw/iftop/) are good interactive CLI tools for monitoring network usage.

If you want to test these tools you can also artificially impose loads on the machine using the [`stress`](https://linux.die.net/man/1/stress) command.

```shell
cat /etc/network/interfaces | egrep eth0 -A 1 | egrep address | awk '{print $2}' | egrep '^10'
```

##### Specialized tools

Sometimes, black box benchmarking is all you need to determine what software to use. Tools like [`hyperfine`](https://github.com/sharkdp/hyperfine) let you quickly benchmark command line programs. For instance, in the shell tools and scripting lecture we recommended `fd` over `find`. We can use `hyperfine` to compare them in tasks we run often. E.g. in the example below `fd` was 20x faster than `find` in my machine.

```
$ hyperfine --warmup 3 'fd -e jpg' 'find . -iname "*.jpg"'
Benchmark #1: fd -e jpg
  Time (mean ± σ):      51.4 ms ±   2.9 ms    [User: 121.0 ms, System: 160.5 ms]
  Range (min … max):    44.2 ms …  60.1 ms    56 runs

Benchmark #2: find . -iname "*.jpg"
  Time (mean ± σ):      1.126 s ±  0.101 s    [User: 141.1 ms, System: 956.1 ms]
  Range (min … max):    0.975 s …  1.287 s    10 runs

Summary
  'fd -e jpg' ran
   21.89 ± 2.33 times faster than 'find . -iname "*.jpg"'
```

###### Network Benchmark

* [`wrk`](https://github.com/wg/wrk) - A modern HTTP benchmarking tool capable of generating significant load when run on a single multi-core CPU.
  * Supports Lua scripting for dynamic request generation and response processing.
  * [Snippet: wrk POST with Lua script](snippets/lua-wrk-post.lua)

As it was the case for debugging, browsers also come with a fantastic set of tools for profiling webpage loading, letting you figure out  where time is being spent (loading, rendering, scripting, &c). More info for [Firefox](https://developer.mozilla.org/en-US/docs/Mozilla/Performance/Profiling_with_the_Built-in_Profiler) and [Chrome](https://developers.google.com/web/tools/chrome-devtools/rendering-tools).

##### C++ profiling functions

* print memory

```c++
std::pair<size_t, size_t> MemoryUsage() {
  uint32_t size = 0, resident = 0, share = 0;
  std::ifstream buffer("/proc/self/statm");
  buffer >> size >> resident >> share;
  buffer.close();

  uint32_t page_size_kb = sysconf(_SC_PAGE_SIZE) / 1024;
  return std::make_pair(resident * page_size_kb / 1024,
                        share * page_size_kb / 1024);
}
```



##### [Intel® RDT(Resource Director Technology)](https://www.intel.com/content/www/us/en/architecture-and-technology/resource-director-technology.html)

* 通过硬件实现任务组(tasks group)级的L3 Cache（LLC）和内存带宽（MBM）的监控和隔离限制的技术

##### Intel PCM

* https://github.com/intel/pcm
  * `pcm-memory`
* https://www.intel.com/content/www/us/en/developer/articles/technical/performance-counter-monitor.html



### ML Profiling

![image-20250617210508106](./Debugging-and-Profiling/image-20250617210508106.png)

![image-20250617210421615](./Debugging-and-Profiling/image-20250617210421615.png)

### GPU Profiling

> 参考gpu-profiling-*.py




### Exercises

(Advanced) Read about [reversible debugging](https://undo.io/resources/reverse-debugging-whitepaper/) and get a simple example working using [`rr`](https://rr-project.org/) or [`RevPDB`](https://morepypy.blogspot.com/2016/07/reverse-debugging-for-python.html).    

rr:

```
watch -l XX
reverse-cont
```

[memory-profiler](https://pypi.org/project/memory-profiler/)

[pycallgraph](http://pycallgraph.slowchop.com/en/master/)



**限制进程资源**

taskset --cpu-list 0,2 stress -c 3

[利用cgroup控制内存等资源](https://segmentfault.com/a/1190000008125359)

