### Basic

- unittest.mock

coverage run --source=monotorch -m pytest tests/
coverage html --show-contexts

### unittest

import shutil
import tempfile



class Test(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    @classmethod
    def setUpClass(cls):
        cls.xx = XX()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test1(self):
            new_ckpt_dir = f'{self.temp_dir}/new_saved'
            ...

*** pytest

- @pytest.mark.benchmark

pytest.main(["-x", __file__])


@create_new_process_for_each_test()     —— vllm


### Pytest 命令行示例

`pytest -n auto -v --report-log ut_$(date +%Y%m%d_%H%M%S)_$$.log -s <test_file.py>`

*   `-n auto`: 使用 `pytest-xdist` 插件，根据 CPU 核心数自动并行执行测试。
*   `-v`: (verbose) 提供更详细的输出。
*   `--report-log <filename>`: 将测试报告（包括 setup, call, teardown 阶段）写入指定的日志文件。
    *   `ut_$(date +%Y%m%d_%H%M%S)_$$.log`: 这是一个动态生成文件名的技巧，包含日期、时间和进程ID，确保日志文件名唯一，避免覆盖。
*   `-s`: (disable capturing) 不捕获 `print` 等标准输出，使其直接显示在控制台。
*   `<test_file.py>`: 指定要运行的测试文件。


* pytest-xdist

# PYTEST_XDIST_WORKER: 由 pytest-xdist 在并行测试时设置的环境变量，用于区分不同的工作进程。
# - 格式: "gw0", "gw1", ...
# - 主进程 (master) 中不存在此变量。
# - 用途: 为每个 worker 分配独立资源，如 GPU、数据库等，避免冲突。

import os
import pytest

@pytest.fixture(scope='session')
def worker_id():
    """获取 xdist worker id，主进程则为 'master'"""
    return os.environ.get('PYTEST_XDIST_WORKER', 'master')

@pytest.fixture(scope='session')
def device(worker_id):
    """根据 worker id 分配 GPU device 的示例"""
    if worker_id == 'master':
        # 主进程不分配 GPU
        return 'cpu'
    
    # 从 'gw1' 中解析出 worker 编号 1
    worker_num = int(worker_id.replace('gw', ''))
    
    # 假设有多张卡，轮询分配
    # import torch
    # gpu_id = worker_num % torch.cuda.device_count() 
    # return f'cuda:{gpu_id}'
    return f'cuda:{worker_num}'


*** Decorator

def test_task_decorator(*args, task_filter: Union[str, List[str]] = None, **kwargs):
  def decorator(func: Callable):
    def wrapper(self, *extra_args, **extra_kwargs):
      try:
        for name, t in test_task_store.get_tasks().items():
          if task_filter is None or (isinstance(task_filter, str) and name == task_filter) or (
              isinstance(task_filter, list) and name in task_filter):
            try:
              func(self, *extra_args, task=t, task_name=name, **extra_kwargs, **kwargs)
            except Exception as e:
              logging.error(f"Error occurred while running test for task {name}: {e}", exc_info=True)
      except Exception as e:
        logging.error(f"Error in test decorator: {e}", exc_info=True)

    return wrapper

  return decorator

### parametrized

- absl

from absl.testing import parameterized

class MyOpTest(parameterized.TestCase):
    @classmethod
    def setUpClass(cls):
        ...

    @parameterized.parameters(
        (1,2),
        (1,3),
        (1,10)
    )
    @test_task_decorator()
    def test_loader(self, N, M, task, task_name):
        ...


- pytest

@pytest.mark.parametrize("Z, H, N_CTX, HEAD_DIM", [(1, 2, 1024, 64)])
@pytest.mark.parametrize("causal", [True])