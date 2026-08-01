// 写进程 (e.g., from shell)
// echo "command_to_run" > /tmp/my_fifo

// 读进程 (C++)
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <iostream>

void read_from_fifo(const char* fifo_path) {
    mkfifo(fifo_path, 0666); // 创建FIFO
    int fd = open(fifo_path, O_RDONLY); // 阻塞直到有进程写入
    char buf[1024];
    while (true) {
        ssize_t bytes_read = read(fd, buf, sizeof(buf) - 1); // 阻塞直到读到数据
        if (bytes_read > 0) {
            buf[bytes_read] = '\0';
            std::cout << "Read from FIFO: " << buf;
        }
    }
    close(fd);
}