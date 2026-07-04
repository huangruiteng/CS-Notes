### py-spy

py-spy record -o profile.svg --native -- python test.py

100samples/s 采样数除以100是实际运行的时间



### cpu time

end = time.perf_counter()

### fix cpu clock

cpu存在p-state，每个p-state对应一组特定的工作频率和电压

# 安装
sudo apt install cpufrequtils

# 设置最大/最小频率
sudo cpufreq-set -r -g performance
sudo cpufreq-set -r -d 2Ghz
sudo cpufreq-set -r -u 2Ghz

# 查询 Pstate
cpufreq-info
# 查询 Cstate
cat /sys/module/intel_idle/parameters/max_cstate
# 查询 turbo状态
cat /sys/devices/system/cpu/intel_pstate/no_turbo

# 或者
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq

pytorch benchmark https://github.com/pytorch/benchmark/blob/main/torchbenchmark/util/machine_config.py#L293C5-L293C31
check_pstate_frequency_pin



### htop

cat ~/.config/htop/htoprc

# Beware! This file is rewritten by htop when settings are changed in the interface.
# The parser is also very primitive, and not human-friendly.
fields=3 0 48 17 18 38 39 40 2 46 47 49 1
sort_key=46
sort_direction=-1
tree_sort_key=0
tree_sort_direction=1
hide_kernel_threads=1
hide_userland_threads=0
shadow_other_users=0
show_thread_names=0
show_program_path=1
highlight_base_name=0
highlight_megabytes=1
highlight_threads=1
highlight_changes=0
highlight_changes_delay_secs=5
find_comm_in_cmdline=1
strip_exe_from_cmdline=1
show_merged_command=0
tree_view=0
tree_view_always_by_pid=0
header_margin=1
detailed_cpu_time=0
cpu_count_from_one=0
show_cpu_usage=1
show_cpu_frequency=1
show_cpu_temperature=0
degree_fahrenheit=0
update_process_names=0
account_guest_in_cpu_meter=0
color_scheme=0
enable_mouse=1
delay=15
left_meters=CPU Memory Swap LeftCPUs8
left_meter_modes=1 1 1 1
right_meters=Tasks LoadAverage Uptime RightCPUs8
right_meter_modes=2 2 2 1
hide_function_bar=0

### strace

* dtrace
  * Even if what you are trying to debug is a black box binary there are tools that can help you with that. 
   Whenever programs need to perform actions that only the kernel can, they use [System Calls](https://en.wikipedia.org/wiki/System_call).
   There are commands that let you trace the syscalls your program makes. 
   In Linux there’s [`strace`](https://www.man7.org/linux/man-pages/man1/strace.1.html) and macOS and 
   BSD have [`dtrace`](http://dtrace.org/blogs/about/). `dtrace` can be tricky to use because it uses its own `D` language, 
   but there is a wrapper called [`dtruss`](https://www.manpagez.com/man/1/dtruss/) that provides an interface more similar to `strace` 
   (more details [here](https://8thlight.com/blog/colin-jones/2015/11/06/dtrace-even-better-than-strace-for-osx.html)).
  * [strace入门](https://blogs.oracle.com/linux/strace-the-sysadmins-microscope-v2)


关注以下系统调用
- 文件：open/close/read/write/lseek
- 网络：socket/bind/listen/send/recv
- 进程控制：fork/execve/wait
- 内存管理：mmap/munmap/brk


```shell
# On Linux
strace git status 2>&1 >/dev/null | grep index.lock
sudo strace [-e lstat] ls -l > /dev/null

# 多线程 strace，要显示 PPID
ps -efl | grep $task_name # 显示 PPID、PID
strace -p $PID

# 一些 flag
-tt   发生时刻
-T 		持续时间
-s 1024 print输入参数的长度限制
-e write=   -e read=     -e trace=file/desc			-e recvfrom
-f 监控所有子线程   -ff
```

# On macOS
sudo dtruss -t lstat64_extended ls -l > /dev/null

# 与之配合的技术
readlink /proc/22067/fd/3
lsof | grep /tmp/foobar.lock


### 磁盘

df -h