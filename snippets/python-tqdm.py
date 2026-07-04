import logging
import sys
import time
from tqdm import tqdm

# 1. 自定义日志处理器，将所有日志消息通过 tqdm.write() 输出
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            # 使用 tqdm.write() 而不是 print()，以确保与进度条兼容
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

# 2. 配置根日志记录器
log = logging.getLogger()
log.setLevel(logging.INFO)
if log.hasHandlers():
    log.handlers.clear()
log.addHandler(TqdmLoggingHandler())


# 3. 模拟一个包含日志输出的任务
def run_long_task():
    """一个模拟的长时间运行任务。"""
    item_list = range(10)
    
    # 4. 创建 tqdm 实例
    #    tqdm 会自动检测输出是否为终端（TTY）。
    #    - 如果是终端，显示动态进度条。
    #    - 如果重定向到文件，它会自动禁用动画，只进行简单的行输出。
    with tqdm(total=len(item_list), desc="Processing items", file=sys.stdout, disable=None) as pbar:
        for i in item_list:
            time.sleep(0.5)

            # 5. 在循环内部使用 logging 记录日志
            if (i + 1) % 4 == 0:
                log.info(f"--- Checkpoint: Reached item {i+1} ---")

            pbar.set_description(f"Processing item {i+1}/{len(item_list)}")
            pbar.update(1)

if __name__ == "__main__":
    log.info("Task starting...")
    run_long_task()
    log.info("Task finished.")
    
    print("\n--- HOW TO TEST ---")
    print("1. Run directly in terminal: `python your_script_name.py`")
    print("   (You will see a dynamic progress bar with clean log messages)")
    print("2. Redirect to a file: `python your_script_name.py > log.txt`")
    print("   (Open log.txt to see clean, line-by-line output without control characters)")