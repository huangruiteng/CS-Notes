*** 查找大文件

sudo find / \( -path /root/rec -prune \) -o \( -type f -size +100M -exec ls -lh {} \; \) | awk '{ print $9 ": " $5 }'


*** 查找并remove文件

find /root/rec -mindepth 1 -type d -mmin +120 -exec rm -rf {} +

# 注意加号，是为了一次rm命令rm多个文件，而不是循环


*** 多条件查找

# 在多个目录(/path1, /path2)中，查找满足条件A(-name "*A*")或条件B(-name "*B*")的文件，并忽略错误输出
find /path1 /path2 -name "*A*" -o -name "*B*" 2>/dev/null


*** 文件传输

xxd -p myfile > tmp
xxd -r -p tmp > myfile


alias pull='rsync -aPv -e "ssh -p {port}" root@{ip_addr}:{src_dir} {dst_dir} --exclude "ckpts" --exclude "hstu_model" --exclude "dataio" --exclude ".idea" --exclude ".git"'
alias push='rsync -aPv -e "ssh -p {port}" {src_dir} root@{ip_addr}:{dst_dir} --exclude "ckpts" --exclude "hstu_model" --exclude "dataio" --exclude ".idea" --exclude ".git"'


*** sort

sort -V (Version Sort)
核心功能: 自然排序 (Natural Sort)，能正确处理文本中嵌入的版本号。
解决了什么问题: 标准的字典序排序 (`sort`) 会将 `v1.10` 排在 `v1.2` 之前。
`sort -V` 能理解 `10` 是一个比 `2` 大的数字。
示例:
$ ls | sort
version-1.10.txt
version-1.2.txt
version-2.0.txt

$ ls | sort -V
version-1.2.txt
version-2.0.txt
version-1.10.txt

相关常用参数:
-n (Numeric Sort): 按数值大小进行排序。
-r (Reverse): 将排序结果反转。
-u (Unique): 仅输出唯一的行（去除重复行）。
-k (Key): 按指定的列（字段）进行排序。例如 `sort -k 2 -n` 表示按第二列进行数值排序。
-h (Human-readable): 与 -n 结合使用，可以正确排序包含 `K`, `M`, `G` 等单位的数值。

相关命令:
ls -v: `ls` 命令自带的版本排序功能，效果与 `ls | sort -V` 类似。


*** 文件打包与查找

安全地打包文件 (处理带空格等特殊字符的文件名)
`fd -e html -0 | xargs -0 zip output.zip`
- `fd` 是 `find` 的现代替代品。`-e html` 指定扩展名。
- `-0` 和 `xargs -0` 配合，使用 `null` 字符分隔文件名，可以安全处理包含空格或特殊字符的文件名。

查找目录下最近修改的文件 (macOS)
核心思路: `find/fd` -> `stat` -> `sort` -> `cut` -> `tail`
`find . -type f -print0 | xargs -0 stat -f '%m%t%Sm %N' | sort -n | cut -f2- | tail -n 1`
1.  `find . -type f -print0`: 递归查找文件，用 null 字符分隔。`fd . -0 -t f` 效果类似。
2.  `xargs -0 stat -f '%m%t%Sm %N'`: 对每个文件执行 `stat`。
    - `-f '%m%t%Sm %N'`: (macOS格式) 输出 `修改时间戳<Tab>可读时间<空格>文件名`。
    - GNU/Linux 对应格式为: `stat --format '%Y :%y %n'`。
3.  `sort -n`: 按第一列的时间戳进行数值排序。
4.  `cut -f2-`: 删除用于排序的时间戳，只保留可读时间。
5.  `tail -n 1`: 取最后一行，即最近修改的文件。

https://stackoverflow.com/questions/5566310/how-to-recursively-find-and-list-the-latest-modified-files-in-a-directory-with-s

等效写法 (使用 -exec):
`find . -exec stat -f '%m%t%Sm %N' {} + | sort -n | cut -f2- | tail -n 1`
- `-exec ... {} +` 效率较高，它会将多个文件名一次性传递给 `stat`。