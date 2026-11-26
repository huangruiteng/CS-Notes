# Python

> 相关：[Algorithms-Potpourri.md](./Algorithms-Potpourri.md)、[leetcode题目简评.md](./leetcode题目简评.md)、[TypeScript.md](./TypeScript.md)。

## 阅读地图

1. 「[算法与有状态编码原语（Python 3）](#算法与有状态编码原语python-3)」整理纯手写场景的容器复杂度、边界陷阱、`bisect` 二分不变量、`heapq` 惰性删除堆与哨兵双向链表骨架。
2. 「[语言机制与对象模型](#语言机制与对象模型)」覆盖 GIL、GC、作用域（LEGB）、基础数据、关键词、函数/装饰器、上下文管理器、`class`、`abc` 与 `typing` 类型收窄。
3. 「[容器、函数式与数据处理](#容器函数式与数据处理)」汇总字符串、正则、迭代器、`collections`、`dataclasses`、`functools`、`itertools`、时间、数值与序列化工具。
4. 「[并发、异步与系统交互](#并发异步与系统交互)」包含 `asyncio`、线程池/进程池、子进程、超时控制与系统文件操作。
5. 「[异常、测试、调试与代码风格](#异常测试调试与代码风格)」沉淀异常处理、`logging`、`pdb`、单元测试与静态检查约定。
6. 「[环境搭建与工程工具](#环境搭建与工程工具)」记录环境配置、打包工具、CLI 参数解析、`fastapi` 与常用开发生态。

## 算法与有状态编码原语（Python 3）

### 容器复杂度与高频边界陷阱

| 结构 | 典型操作与摊还复杂度 | 语义与顺序保证 |
| --- | --- | --- |
| `list` | 尾插/尾删 $O(1)$，随机索引 $O(1)$，头插删/切片 $O(n)$ | 动态数组；连续内存，适合栈与索引数组 |
| `collections.deque` | 两端 `append`/`appendleft`/`pop`/`popleft` $O(1)$，中间索引 $O(n)$ | 块状双端链表；支持 `maxlen` 固定滑窗 |
| `dict` / `set` | 查找/插入/删除均摊 $O(1)$ | Python 3.7+ `dict` 严格保持首次插入顺序；`set` 无序 |
| `dict` 顺序技巧 | `next(iter(d))` 取最早键 $O(1)$；`d.popitem()` 弹出最新键（LIFO） | `dict.popitem()` 无 `last=` 参数；需两端移动或弹出最老键用 `OrderedDict` |
| `collections.OrderedDict` | `move_to_end(k, last=True)` 与 `popitem(last=False)` 均 $O(1)$ | 内建哈希+双向链表，适合标准 LRU |
| `heapq` | `heappush` / `heappop` $O(\log n)$，`heapify` $O(n)$，`pq[0]` $O(1)$ | 原地维护在 `list` 上的**最小堆**；无原生 `decrease-key` |

高频手写边界陷阱：

1. **嵌套可变对象共享引用 & 默认可变参数**：二维网格必须用 `[[0] * m for _ in range(n)]`；`[[0] * m] * n` 会让所有行指向同一列表。函数默认容器参数统一写 `items: list[int] | None = None`，内部初始化 `items = [] if items is None else items`。
2. **负数整除与取模（向 $-\infty$ 取整）**：Python 中 `-3 // 5 == -1`、`-3 % 5 == 2`，适合滑动桶或环形下标（如 `x // w` 直接按宽 $w$ 分桶）；若需要 C/Java 风格的向零截断，改用 `int(a / b)`。
3. **`defaultdict` 的读穿副作用**：`if k in d:` 只读不插入；`d[k]` 在键缺失时会立刻写入默认值并改变 `len(d)`，判断存在性前先用 `in`。
4. **嵌套函数修改外层标量**：闭包内重绑定外层的 `int` / `bool`（如计数器或状态标志）必须声明 `nonlocal count`；原地修改 `list` / `dict` 内容则不需要。
5. **合法 `None` 值与缺失/删除标记混用**：当容器允许存 `None` 时，不能用 `None` 兼任“键不存在”或“墓碑删除”，应定义私有哨兵 `_MISSING = object()` 或 `_TOMBSTONE = object()`，并用 `is` 比较。
6. **深递归与 `@lru_cache(None)` 参数限制**：树/图/记忆化深递归前加 `sys.setrecursionlimit(200_000)`；记忆化入参必须可哈希（`tuple` 而非 `list`），且大状态注意调用 `cache_clear()` 控内存。

### 排序键与二分查找不变量（bisect）

- **复合键排序**：`items.sort(key=lambda x: (x.priority, -x.ts, x.id))`；当比较规则非单个标量投影时（例如拼接最大数），用 `functools.cmp_to_key(cmp)`，约定返回负数表示 `a` 排在 `b` 前、`0` 表示相等、正数表示 `b` 排在 `a` 前。

`bisect` 在升序列表中查找保持有序的**插入下标**，每次比较中点，缩小一半搜索范围。遇到重复值时，`left` 插在已有相同值前面，`right` 插在它们后面。下面用 `|` 标出插入位置，下标从 0 开始。

```python
import bisect

a = [1, 3, 3, 3, 7]
bisect.bisect_left(a, 3)   # 1，对应 [1 | 3, 3, 3, 7]
bisect.bisect_right(a, 3)  # 4，对应 [1, 3, 3, 3 | 7]
bisect.bisect_left(a, 4)   # 4，目标不存在时仍返回插入位置
bisect.insort_left(a, 4)   # 实际插入，a 变成 [1, 3, 3, 3, 4, 7]
```

`bisect` 是 `bisect_right` 的别名。查位置为 $O(\log n)$，`insort_left/right` 还要移动列表元素，整体插入为 $O(n)$。 [Python 官方文档](https://docs.python.org/zh-cn/3/library/bisect.html)

- **`bisect` 四类查询映射表**（前提：`a` 非严格单调递增，索引区间 `[0, len(a))`）：

| 查询目标 | 表达式 | 越界（无解）判定 | 典型场景 |
| --- | --- | --- | --- |
| 第一个 `>= x` | `i = bisect.bisect_left(a, x)` | `i == len(a)` | 下界定位、插入位置 |
| 第一个 `> x` | `i = bisect.bisect_right(a, x)` | `i == len(a)` | 严格上界 |
| 最后一个 `< x` | `i = bisect.bisect_left(a, x) - 1` | `i < 0` | 严格前驱 |
| 最后一个 `<= x` | `i = bisect.bisect_right(a, x) - 1` | `i < 0` | 时间戳快照 / 版本回溯查找 |

- **元组数组的 `bisect` 坑点**：若 `records` 存 `[(ts, val), ...]`，切勿直接写 `bisect_right(records, (ts,))`，因为元组比较 `(5, "a") > (5,)` 会让 `bisect_right` 停在 `ts=5` 之前！Python 3.10+ 直接传 `key`：

```python
import bisect

# records 按 ts 非严格递增；右侧插入点减 1，定位最后一个时间戳 <= ts 的版本
idx = bisect.bisect_right(records, ts, key=lambda r: r[0]) - 1
result = records[idx][1] if idx >= 0 else None
```

- **单调谓词二分模板（`first_true`）**：固定闭区间 `[lo, hi]`，用独立 `ans` 记录当前最优合法点，循环条件恒为 `lo <= hi`，彻底消灭开闭区间偏移错误：

```python
def first_true(lo: int, hi: int, pred) -> int | None:
    """在单调区间 [lo, hi] 内找最小的使 pred(mid) 为 True 的整数；全为 False 返回 None。"""
    ans = None
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if pred(mid):
            ans = mid
            hi = mid - 1  # 不变量：ans 记录已见最小合法解，继续向左收缩
        else:
            lo = mid + 1
    return ans
```

### 优先队列、Tie-Breaker 与惰性删除堆（heapq）

Python 标准库 `heapq` 只有最小堆且不支持原地修改元素优先级。在需要动态改权、按分数淘汰或中途取消任务时，通用解法是 **「真值表 `active` + 单调自增 `seq` + 惰性删除堆」**：

1. **防不可比对象崩溃**：堆内元组一律写成 `(priority, seq, item_id)`（最大堆存 `(-score, seq, item_id)`）。只要 `seq` 全局严格递增，元组比较永远在第 2 位分出胜负，绝不会去比较自定义对象或 `dict` 而抛出 `TypeError`，同时顺带保证同优先级下的确定性 FIFO（或 `-seq` 实现 LIFO）。
2. **惰性删除与真值表**：`active[item_id] = (score, seq)` 保存当前唯一权威状态；更新或删除只改 `active` 并（更新时）向 `pq` 追加新元组，`len(active)` 才是真实队列大小。
3. **仅在堆顶清理过期记录**：`peek` 与 `pop` 前循环弹出满足 `item_id not in active or active[item_id] != (score, seq)` 的陈旧堆顶；当陈旧节点过多（如 `len(pq) > 4 * len(active) + 64`）时，用 `O(n)` 的 `heapq.heapify` 重建以有界化内存。

```python
import heapq

class LazyMaxHeap:
    def __init__(self) -> None:
        self._pq: list[tuple[int, int, str]] = []
        self._active: dict[str, tuple[int, int]] = {}
        self._seq = 0

    def upsert(self, item_id: str, score: int) -> None:
        self._seq += 1
        self._active[item_id] = (score, self._seq)
        heapq.heappush(self._pq, (-score, self._seq, item_id))
        if len(self._pq) > 4 * len(self._active) + 64:
            self._pq = [(-s, q, k) for k, (s, q) in self._active.items()]
            heapq.heapify(self._pq)

    def remove(self, item_id: str) -> bool:
        return self._active.pop(item_id, None) is not None

    def _clean(self) -> None:
        while self._pq:
            neg_s, seq, item_id = self._pq[0]
            if self._active.get(item_id) == (-neg_s, seq):
                return
            heapq.heappop(self._pq)

    def pop(self) -> tuple[str, int] | None:
        self._clean()
        if not self._pq:
            return None
        neg_s, _, item_id = heapq.heappop(self._pq)
        self._active.pop(item_id)
        return item_id, -neg_s
```

### 哨兵双向链表与复合索引骨架

当结构需要 **按任意键 $O(1)$ 删除 + 按时间/位置有序迭代 + 局部重排**（如 LRU、带固定保护节点的窗口缓存，参见 [Algorithms-Potpourri.md - LRU cache](./Algorithms-Potpourri.md#lru-cache)）时，使用**头尾双哨兵（Dummy Head / Dummy Tail）**可以彻底消灭 `head is None` 与单节点边界特判：

- **不变量**：`head.next` 指向最老节点，`tail.prev` 指向最新节点；空表时 `head.next is tail and tail.prev is head`；被摘除节点的 `prev` 与 `next` 置 `None`，防止旧引用悬空或误操作。
- **扩展性**：所有位置操作只依赖两个 4 行原子原语 `_remove(node)` 与 `_insert_before(pos, node)`。

```python
class _Node:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key=None, val=None) -> None:
        self.key, self.val = key, val
        self.prev: _Node | None = None
        self.next: _Node | None = None

class SentinelList:
    def __init__(self) -> None:
        self.head, self.tail = _Node(), _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, node: _Node) -> None:
        assert node.prev is not None and node.next is not None
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None

    def _append_newest(self, node: _Node) -> None:
        prev_last = self.tail.prev
        assert prev_last is not None
        prev_last.next = node
        node.prev = prev_last
        node.next = self.tail
        self.tail.prev = node
```

## 语言机制与对象模型

### GIL

#### GIL 决定谁能执行，锁保护共享操作

在常规启用 GIL 的 CPython 中，同一个解释器内一次只有一条持有 Global Interpreter Lock（GIL）的线程执行 Python 字节码。大部分纯 Python CPU 密集型计算很难直接靠多线程加速。阻塞 I/O 期间、部分 C 扩展执行期间可以释放 GIL，其他线程仍有机会运行。

CPython 3.2 将按 tick 检查的旧间隔（check interval）换成以秒计的时间间隔。设计目标包括让竞争中的线程切换更可预期，减少锁争用及相关系统调用。`sys.setswitchinterval()` 设置的是理想间隔，实际时机还受长操作与 OS 调度影响。 [Python 3.2 的线程改动](https://docs.python.org/3/whatsnew/3.2.html#multi-threading) · [切换间隔](https://docs.python.org/3.14/library/sys.html#sys.setswitchinterval) · [GIL 旧笔记来源](https://zhuanlan.zhihu.com/p/20953544) · [Grok the GIL](https://opensource.com/article/17/4/grok-gil) · [Python Wiki](https://wiki.python.org/moin/GlobalInterpreterLock)

一个线程读到 `key` 不在缓存里，到它算出并写入之间，另一个线程也可能读到同样的旧状态。即便对应的一次字典访问在某个构建里是安全的，「检查、计算、写回」仍是三步。若同一 key 只允许初始化一次，可以用同一把 `threading.Lock` 包住整个流程，或由一个线程经队列统一管理这份状态。锁要保护的是这条业务约束。

free-threaded CPython 是可禁用 GIL 的构建。Python 3.14 文档说明 `dict`、`list` 等内置类型当前使用内部锁保护部分并发访问，业务上的复合操作仍需显式同步。某些未声明兼容的 C 扩展可能在导入时重新启用 GIL，当前进程可用 `sys._is_gil_enabled()` 检查。 [CPython 3.14 Free-threading HOWTO](https://docs.python.org/3.14/howto/free-threading-python.html)

### GC 垃圾回收

* 基础的基于refcount
* 循环垃圾回收机制
  * 触发不定期
  * 依赖上次gc以来新分配的变量数量
  * 变量年龄组、阈值设置
    * There are **3 generations of thresholds** to help amortize the expensive costs of running garbage collection on every object. The later generations are less frequently run.
* 循环依赖：即使del也无法触发gc
  * Python-gc.py
  * gc.collect()

#### 变量作用域：LEGB

Python 使用 词法作用域 （lexical scoping），也称为静态作用域。这意味着变量的作用域是在代码编写时由其在代码中的位置决定的，而不是在运行时。Python 的作用域规则通常被称为 LEGB 规则 ：

- L (Local) ：局部作用域。这是函数内部定义的变量。当函数被调用时，会创建一个新的局部作用域。函数执行完毕后，这个作用域通常会被销毁，其中的变量也就不再存在（除非有闭包等情况）。
- E (Enclosing function locals) ：嵌套函数（闭包）的父函数的作用域。如果一个函数嵌套在另一个函数内部，内部函数可以访问外部（但非全局）函数的变量。
- G (Global) ：全局作用域。在模块级别定义的变量。在一个模块的任何地方都可以访问全局变量。
- B (Built-in) ：内置作用域。Python 预定义的名称，如 len() , print() , str 等。
当 Python 查找一个变量时，它会按照 L -> E -> G -> B 的顺序搜索。

### 基础数据

* int类型的大小是无限的
  * python动态调整位数
  * 只要内存能存的下即可

```python
bool(int(str(3))) -> True
bool(int(str(0))) -> False
```

* str类型和unicode类型：
  * 在 Python 2 中，`u'abc'` 是 `unicode` 类型，而 `str` 是字节字符串。
    * `instance(u'abc', str)` 返回 `False`，因为它们是不同的类型。
  * 在 Python 3 中，所有字符串都是 Unicode，因此这种区分不再存在。

### 关键词

#### for else

* https://book.pythontips.com/en/latest/for_-_else.html

```python
for item in container:
    if search_something(item):
        # Found it!
        process(item)
        break
else:
    # Didn't find anything..
    not_found_in_container()
```

#### match ... case ... (Python 3.10+)

```python
def prepare_embedding_documents(*documents: Optional[Union[str, List[str], Dict[Union[int, str], Any]]]):
    if not documents:
      return
    assert isinstance(documents, (list, tuple))
    results = []
    for document in documents:
      match document:
        case str(doc):
          results.append(doc)
        case list() | set() | list() as docs if all(isinstance(doc, str) for doc in docs if doc):
          results.append(list(docs))
        case dict() as doc_dict if all(isinstance(v, str) for k, v in doc_dict.items() if v):
          results.append([f'{key}:{doc_dict[key]}' for key in sorted(doc_dict)])
        case _:
          raise ValueError(f"document {document} error!")
    return results
```

#### with

* [with 的用法和原理](https://www.cnblogs.com/sddai/p/14411906.html)
  * 使用with后不管with中的代码出现什么错误，都会进行对当前对象进行清理工作。
  * 在with语句结束后，as的对象仍然可见

#### Ellipsis

```python
def example_function(param=...):
    if param is Ellipsis:
        print("Parameter not provided.")
```

### 函数

* callable

```python
def call_with_retry(fn: Callable,
                    check_fn: Union[Callable, None] = None,
                    retry_limit: int = 5,
                    retry_interval: int = 60):
    retry = 0
    while True:
        try:
            res = fn()
            if check_fn:
                check_fn(res)
            return res
        except Exception as e:
            logging.warning(f'Function `{fn.__name__}` encountered exception: {repr(e)}.')
            retry += 1
            if retry >= retry_limit > 0:
                break
            logging.warning(f'Retrying {retry} out of {retry_limit} times in {retry_interval} secs.')
            time.sleep(retry_interval)
    return None
```

* @修饰器

```python
#funA 作为装饰器函数
def funA(fn):
    #...
    fn() # 执行传入的fn参数
    #...
    return '...'
@funA
def funB():
    #...

---> funB = funA(funB)

# 装饰器嵌套参数函数
def funA(fn):
    def say(*args,**kwargs):
        fn(*args,**kwargs)
    return say
@funA
def funB(arc):
    print("A: ",arc)
@funA
def other_funB(name,arc):
    print(name,arc)
funB("a")
other_funB("B: ","b")
```

* 函数名之前加类名
* function signature

```py
def multiply(x: int, y: int) -> int:
    return x*y
```

### 函数修饰decorator

* @func 作为类或者函数的修饰符
  * 当解释器读到@修饰符之后，会先解析@后的内容，直接就把@下一行的函数**或者类**作为@后边的函数的参数，然后将返回值赋值给下一行修饰的函数对象
  * @func 修饰类，常用于 register

```
@model_registry.register('model_type')
```

* `@functools.wraps(func)` : https://stackoverflow.com/questions/308999/what-does-functools-wraps-do
  * 主要作用是继承一些函数信息
  * kwargs要自己拿

```python
@functools.wraps(func)
def wrapper(*args, **kwargs):
	arg1 = kwargs.get('arg1')
  nonlocal arg1
  ...
  return func(*args, **kwargs)
```

* 修饰类的例子：自动生成函数

```python
@auto_pop_field("private_value_")
class ABC
...

def auto_pop_field(field_name):

  def decorator(cls):

    def pop_field(self):
      field_value = getattr(self, field_name)
      setattr(self, field_name, None)
      return field_value

    setattr(cls, f"pop_{field_name}", pop_field)
    return cls

  return decorator
```

### context manager

* [context manager](https://www.geeksforgeeks.org/context-manager-in-python/): [use decorator](https://www.geeksforgeeks.org/context-manager-using-contextmanager-decorator/)

```python
from contextlib import contextmanager

@contextmanager
def ContextManager():

    # Before yield as the enter method
    print("Enter method called")
    yield

    # After yield as the exit method
    print("Exit method called")

with ContextManager() as manager:
    print('with statement block')
```

```python
@contextlib.contextmanager
def reset_to_default_py_env():
  """Resets some env variables into default python env.
  Useful when calling some other system code that requires python 2.
  """
  old_value = None
  var = "PYTHONPATH"
  if var in os.environ:
    old_value = os.environ[var]
  os.environ[var] = (
      "/usr/local/lib/python2.7/site-packages")
  try:
    yield
  finally:
    if old_value is not None:
      os.environ[var] = old_value
    else:
      del os.environ[var]
```

### class



* [@staticmethod v.s. @classmethod](https://stackoverflow.com/questions/136097/difference-between-staticmethod-and-classmethod#:~:text=%40staticmethod)

* @property
  * [Property function](https://www.tutorialsteacher.com/python/property-function)
* `vars()` 函数返回对象的 `__dict__` 属性


```python
class Student(object):

    @property         
    def birth(self):           # 读写属性
        return self._birth

    @birth.setter
    def birth(self, value):
        self._birth = value

    @property
    def age(self):            # 只读属性
        return 2015 - self._birth
      
class person:
    def __init__(self):
        self.__name=''
    def __post_init__(self):
      	...
    def setname(self, name):
        print('setname() called')
        self.__name=name
    def getname(self):
        print('getname() called')
        return self.__name
    name=property(getname, setname)
```

* [一文让你彻底搞懂Python中\__ str\__和\__repr\__?](https://segmentfault.com/a/1190000022266368)
* 坑
  * python2需要用 class A(object):才能用descriptors. `@property` is descriptor
    * https://stackoverflow.com/questions/9163940/property-getter-setter-have-no-effect-in-python-2





#### metaclass

* 用处
  * 控制类的创建行为：通过定义`metaclass`中的特定方法，您可以控制类的创建过程。例如，您可以在类定义中添加或修改属性，检查类的结构，或者在类被创建之前执行某些操作。
  * 修改类的属性和方法：通过在元类中重写特定的方法，您可以修改类的属性和方法。这使得您可以对类进行自定义操作，例如自动添加特定的属性，修改方法的行为或添加装饰器。
* 例子
  * kwargs可记录状态

```python
class MyMeta(type):
    def __new__(cls, name, bases, attrs):
        attrs['custom_attr'] = 'Custom Attribute'
        return super().__new__(cls, name, bases, attrs)
    
    def __call__(cls, *args, **kwargs):
        print("Creating an instance of", cls.__name__)
        instance = super().__call__(*args, **kwargs)
        return instance

class MyClass(metaclass=MyMeta):
    pass

obj = MyClass()
print(obj.custom_attr)  # 输出: 'Custom Attribute'
```

### abc

* https://python-course.eu/oop/the-abc-of-abstract-base-classes.php

```python
from abc import ABC, abstractmethod
 
class AbstractClassExample(ABC):
    
    @abstractmethod
    def do_something(self):
        # print("Some implementation!")
        pass
        
class AnotherSubclass(AbstractClassExample):

    def do_something(self):
        super().do_something()
        print("The enrichment from AnotherSubclass")
        
x = AnotherSubclass()
x.do_something()
```

### typing 类型注解

* `TypeGuard[T]`（3.10+，[PEP 647](https://peps.python.org/pep-0647/)）标注自定义类型守卫函数：`if f(x):` 的 True 分支里，类型检查器把参数 `x` 收窄为 `T`。

```python
from typing import Any, TypeGuard

def work_lane_contract_is_due_monitor_attempt(
    contract: dict[str, Any] | None,
) -> TypeGuard[dict[str, Any]]:
    return bool(
        isinstance(contract, dict)
        and contract.get("monitor_kind") == WORK_LANE_TODO_MONITOR_DUE_KIND
    )

if work_lane_contract_is_due_monitor_attempt(contract):
    contract["must_attempt_work"]  # contract 已从 dict[str, Any] | None 收窄为 dict[str, Any]
```

要点：

- `TypeGuard` 只提供静态标注，运行时仍返回普通 `bool`；实际校验由函数体负责。收窄只发生在调用点的 True 分支，False 分支不收紧，`else` 里仍是原类型（`dict | None`）。
- 只对第一个位置参数（方法的 `self` / `cls` 之后那个）生效，不能指定收窄哪个参数。
- `T` 不必是入参类型的子类型，允许「不健全」的收窄，正确性完全由实现负责；`T` 也只应写 True 真正能证明的性质。
- `isinstance(contract, dict)` 只在函数体内收窄局部变量；`TypeGuard` 的作用是把这条结论传给调用方。类型检查器不解析函数体里的业务判断，所以要显式签名。
- 入参值类型是 `Any` 时，收窄只去掉 `None` / 非 dict 分支，字段值仍是不受检的 `Any`；`TypeGuard` 不替代 schema 校验。
- 3.13+ 的 `TypeIs[T]`（[PEP 742](https://peps.python.org/pep-0742/)）更严格：要求 `T` 与入参类型相容，且 False 分支也会排除 `T`。除「收窄到不相关类型 / 只覆盖部分实例」外，优先用 `TypeIs`。

参考：[typing.TypeGuard](https://docs.python.org/3/library/typing.html#typing.TypeGuard)；3.10 以下用 `typing_extensions.TypeGuard`。TS 的对应机制见 [TypeScript.md - 用户定义类型谓词](./TypeScript.md#用户定义类型谓词--const-type-parameter从白名单到精确类型)。

### 新特性

#### Python 3.13

* 高天解读：https://www.bilibili.com/video/BV1dm2yYrEnn
  * free threading/no GIL
    * 单线程变慢、实验版本
  * JIT
  * new interactive interpreter (REPL)
    * 定义函数很方便，自动缩进、上箭头
  * pdb体验增强
    * q.append(2)

### future

https://python-future.org/quickstart.html: python2到python3的迁移

```python
from __future__ import absolute_import, division, print_function
```

### 坑

* the interactive Python is the only place (I'm aware of) to not have `__file__`.

## 容器、函数式与数据处理

### 基础算法

* sorted
  * key是函数
  * 可以用 `functools.cmp_to_key` 构造复杂的比较函数（原注 `cmp2key` 为笔误）

```python
duplicates = sorted(duplicates.items(), key=lambda item: len(item[1]), reverse=True)
```

* list保序去重：
  * `list(dict.fromkeys(my_list))`

### 字符串

#### 格式化

```python
a=1
f'{a:011d}'
```

* 011d是格式规范，它由冒号和格式选项组成。
  - `0`是填充字符，表示使用0来填充字段。
  - `11`是字段宽度，表示该字段的总宽度为11个字符。
  - `d`表示将变量视为十进制整数进行格式化。

#### 转义

* 括号两遍

```python
cmd = """
	set -e
  function cleanup {{
      rm {};
  }}
  trap cleanup EXIT SIGKILL
  mkdir -p {}; cd {}; rm -f {};
""".format(...)
```

### fstring

https://www.datacamp.com/tutorial/f-string-formatting-in-python

```python
person = {"name": "John", "age": 19}
## 双引号套单引号
print(f"{person['name']} is {person['age']} years old.")
```

### 正则表达式

教程：https://www.runoob.com/regexp/regexp-tutorial.html

python正则：https://www.runoob.com/python3/python3-reg-expressions.html

```python
import re
tmp = re.sub("pattern", "", line.strip('\n'))
matchObj = re.match(r'', line.strip('\n'), re.M|re.I)
```

### 迭代器iterator

```python
# next取下一个元素
next((value for value in values if type(value) == Tensor), None)
```

```python
dict_A = {'a': 1, 'b': 2, 'c': 3}
dict_B = {'a': 4, 'b': 5, 'c': 6}
dict_C = {'a': 3, 'b': 4, 'c': 2}

common_keys = set(dict_A.keys()) & set(dict_B.keys()) & set(dict_C.keys())

filtered_dict_A = dict(filter(lambda item: item[0] in common_keys and dict_B[item[0]] > dict_C[item[0]], dict_A.items()))
```

#### 列表推导

```python
new_concepts = [
          k for k, v in concepts.items() if k not in set(
              [item for sub_list in grouped_concepts for item in sub_list])
      ]
```

### collections

collections.defaultdict(list)、collections.defaultdict(set)

* defaultdict相比普通dict的区别在于：使用索引时，如果未查找到，会自动插入默认值
* dict 可以用 tuple 作 key

```python
d = defaultdict(lambda: 0)
d[key1, key2] = val
if (key, key2) in d:
  ...
for k in d.iteritems():  # Python 2 旧写法；Python 3 已移除 iteritems()，统一用 d.items()
  v = d[k]
  ...
for k,v in d.items(): # python3.6+
  ...
```



#### [浅拷贝与深拷贝](https://zhuanlan.zhihu.com/p/25221086)，[copy.py](https://docs.python.org/3/library/copy.html)

核心思想：

* 赋值是将一个对象的地址赋值给一个变量，让变量指向该地址（ 旧瓶装旧酒 ）。
* 修改不可变对象（str、tuple）需要开辟新的空间
* 修改可变对象（list等）不需要开辟新的空间

=> 所以说改 list 会牵连复制的对象，而改 str 等不会互相影响

```python
import copy
copy.deepcopy(dict)
```



* locals()在3.13之前也是返回的局部变量的浅拷贝



#### queue

```python
# queue.py
task_done()
join()
put(data)
get()

queue的利用：新线程prefetch内容塞进queue里，可以拿到遍历queue的更快的生成器（yield结尾）
```

#### namedtuple

https://realpython.com/python-namedtuple/

#### Counter

```python
my_counter.most_common(10)
xxx.values()
```

[collections.counter](https://docs.python.org/3/library/collections.html#collections.Counter)

```python
class Example(collections.namedtuple('Example', ['aid', 'bid', 'cid', 'did']))

	@classmethod
	def from_abcd(cls, a, b, c, d):
    return cls(a, b, c, d)
```



#### 其它

* 运行文件乱码问题，在文件开头加 `# coding=utf-8`

### dataclasses

```python
import dataclasses

@dataclasses.dataclass
class InventoryItem:
    """Class for keeping track of an item in inventory."""
    name: str
    unit_price: float
    quantity_on_hand: int = 0
    name_set: set = dataclasses.field(default_factory=set)

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand
```

### functools

```python
from functools import reduce
nparam = reduce(lambda x, y: int(x) * int(y), shape, 1)
```

```python
from functools import singledispatch

@singledispatch
def do_sth():
  raise NotImplementedError("Not implemented do_sth")

@do_sth.register(Type1)
def _(input: Type1, ...):
  ...

@do_sth.register(Type2)
def _(input: Type2, ...):
  ...
```

```python
from functools import lru_cache
@lru_cache
def get_info():
  file = os.path.join(os.path.dirname(__file__), FILE)
  with open(file, 'rb') as stream:
    return load(stream)
```

### itertools

* 算法工具

```python
import itertools

names = ["Alice", "Bob", "Charlie", "David"]

combinations = list(itertools.combinations(names, 2))
print(combinations)

# 存在人和公司，则只查找人和公司们的关系
c2p_tuples = list(itertools.product(company_names, people_names))
# 只有公司，则查找公司之间的遍历关系
c2c_tuples = list(itertools.combinations(company_names, 2))
# 只有人，则查找人之间的遍历关系
p2p_tuples = list(itertools.combinations(people_names, 2))
```

### random

```python
import random
index = [i for i in range(X_train.shape[0])]
random.choice(a)    随机取一个
random.sample(a, n) 随机取n个
random.shuffle(index)
random.randint(0,n)

# 保证同一shuffle顺序
randnum = random.randint(0,100)
random.seed(randnum)
random.shuffle(train_x)
random.seed(randnum)
random.shuffle(train_y)
```

### Math 数学相关

#### 解方程

```python
from scipy.optimize import fsolve
import math
import numpy as np

def equation(m):
    return ((1-m)**19) * (1 + 19*m) - 0.995

# 初始猜测值
initial_guess = 0.01

# 使用fsolve函数求解方程
solution = fsolve(equation, initial_guess)

print(solution, equation(solution))

print(math.sqrt(solution))
```

* hybrd方法：https://math.stackexchange.com/questions/3642041/what-is-the-function-fsolve-in-python-doing-mathematically
  * HYBRD is a modification of the Powell hybrid method. Two of its main characteristics involve **the choice of the correction as a convex combination of the Newton and scaled gradient directions**, and the updating of the Jacobian by the rank-1 method of Broyden. The choice of the correction guarantees (under reasonable conditions) **global convergence for starting points far from the solution** and a fast rate of convergence. The Jacobian is approximated by forward differences at the starting point, but forward differences are not used again until the rank-1 method fails to produce satisfactory progress.



#### 正态分布

```python
from scipy.stats import norm

# 计算累积分布概率为0.95对应的分位数
percentile = 0.95
value = norm.ppf(percentile)

print(value)
```

```python
import math
import numpy as np
from scipy.stats import norm
from matplotlib import pyplot as plt

def icdf(loc=0, scale=1):
  xs = np.array([i / 1000 for i in range(1000)])
  ys1 = norm.ppf(xs, loc=loc, scale=scale)
  ys2 = np.log(xs / (1.0 - xs)) / 1.702
  return xs, ys1, ys2

x, y1, y2 = icdf()
plt.plot(x, y1)
plt.plot(x, y2)
plt.show()
```

### datetime

```python
import datetime as dt
dt.datetime.now()
dt.timedelta(hours=1)
dt.timedelta(days=1)

# max datetime (普通调用其timestamp方法可能溢出)
dt.datetime.max.replace(tzinfo=datetime.timezone.utc).timestamp()

# parse timestamp
object = dt.datetime.fromtimestamp(timestamp)

# timezone
import pytz
a = dt.datetime(2022,1,1,tzinfo=pytz.timezone('UTC'))
b = a.tzinfo.localize(
            dt.datetime.combine(object2.date(), dt.time.min)
        )
assert(a == b)

# local timezone
from tzlocal import get_localzone # $ pip install tzlocal
local_tz = get_localzone() 

# datetime format
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
str1 = obj1.strftime(DATETIME_FORMAT)
str2 = '20001231000000'
obj2 = dt.datetime.strptime(dt, '%Y%m%d%H%M%S').strftime(DATETIME_FORMAT)
```

### json

* HTML处理

```
json.loads(json.dumps({"content": row['raw_description']},
                           ensure_ascii=False))['content']
```

* `json.dumps(..., ensure_ascii=False)`

### base64

```python
encoded_string = base64.b64encode(raw_data)
image = encoded_string.decode("utf-8")

base64.b64decode(image)
```

### struct

https://docs.python.org/3/library/struct.html

```shell
id_size = fd.read(8)
# id_size = struct.pack('>Q', len(proto))[::-1]
id_size = struct.unpack('<Q', id_size)[0]
```

### sqlite

文件型数据库

### pydantic

* 做数据格式校验

```python
from pydantic import BaseModel, conint, EmailStr
from typing import List, Optional

# 定义数据模型
class User(BaseModel):
    id: conint(gt=0)  # 整数，必须大于0
    name: str
    email: EmailStr  # 有效的电子邮件地址
    age: Optional[int] = None  # 可选的整数
    tags: List[str] = []  # 字符串列表，默认值为空列表
    data: list[dict[str, Any]]

# 创建一个用户实例
user = User(id=1, name="Alice", email="alice@example.com", age=30, tags=["developer", "python"])

# 输出用户信息
print(user)

# 访问字段
print(user.name)
print(user.email)
```

## 并发、异步与系统交互

### asyncio

```python
import asyncio

# 定义一个异步函数
async def hello_world():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

# 获取事件循环
loop = asyncio.get_event_loop()
# 运行异步函数直到完成
loop.run_until_complete(hello_world())
# 关闭事件循环
loop.close()
```

```python
import asyncio

async def hello_world():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

async def main():
    # 创建多个异步任务
    tasks = [hello_world() for _ in range(3)]
    # 并发运行任务
    await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

```python
import asyncio

class AsyncContextManager:
    async def __aenter__(self):
        print("Entering async context")
        await asyncio.sleep(1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Exiting async context")
        await asyncio.sleep(1)

async def main():
    async with AsyncContextManager() as manager:
        print("Inside async context")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

```python
import asyncio

# 定义一个异步生成器
async def async_generator():
    for i in range(3):
        await asyncio.sleep(1)
        yield i

async def main():
    async for item in async_generator():
        print(item)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

```python
import asyncio
import aiohttp

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        url = "http://example.com"
        result = await fetch(session, url)
        print(result)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

### 多线程编程 - concurrent

* from concurrent.futures import ThreadPoolExecutor, Future
  * 也可以用wait接口

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 定义一个示例函数
def task(n):
    time.sleep(n)
    return f"Task {n} completed"

# 使用 ThreadPoolExecutor 来并行执行任务
def main():
    tasks = [1, 2, 3, 4, 5]  # 每个任务的延迟时间
    results = []

    # 创建线程池
    with ThreadPoolExecutor(max_workers=3) as executor:
        # 提交任务并获取 Future 对象
        futures = {executor.submit(task, n): n for n in tasks}

        # 处理任务完成的顺序
        for future in as_completed(futures):
            result = future.result()  # 获取结果
            results.append(result)
            print(result)

    print("All tasks completed.")
    print(results)

# 运行主程序
if __name__ == "__main__":
    main()
```



* https://chriskiehl.com/article/parallelism-in-one-line
  * 巧用 Pool 实现多线程并行

* 定时执行

```python
class PeriodicRunner(object):
    def __init__(self, name, cond, callback, interval=5, daemon=True):
        self._mutex = threading.Lock()
        self._name = name
        self._cond = cond
        self._callback = callback
        self._interval = interval
        self._running = True
        if not callable(cond) or not callable(callback):
            self._running = False
            return
        self._thread = threading.Thread(target=self.run, name=name, args=(), daemon=daemon)
        self._thread.start()

    def is_alive(self):
        return self._thread.is_alive()

    def run(self):
        try:
            while True:
                with self._mutex:
                    if not self._running:
                        return
                if self._cond():
                    self._callback()
                time.sleep(self._interval)
        except Exception as e:
            logging.info('PeriodicRunner[{}] caught exception[{}]'.format(self._name, repr(e)))
        finally:
            logging.info('PeriodicRunner[{}] exit!'.format(self._name))

    def stop(self):
        logging.info('PeriodicRunner[{}] stop!'.format(self._name))
        with self._mutex:
            self._running = False
        self._thread.join()
```

### multiprocessing

* 关于spawn：https://superfastpython.com/multiprocessing-start-method/

```python
import multiprocessing as mp
mp.set_start_method('spawn')
queue = mp.Queue(num_parallel*2)
producer_proc = mp.Process(name="Producer-0", target=producer, args=(args, queue, sys.stdin.fileno()), daemon=True)

p = mp.Process(...)
# p.setDaemon(True),守护进程，如果主进程结束，则强行让p结束
p.start()
while True:
  if not p.is_alive():
    if p.exitcode != 0:
      raise RuntimeError(...)
    else:
      break
  time.sleep(0.1)

# p.join()

```

#### CUDA 初始化与 fork 的坑

在 GPU 程序里，`multiprocessing` 最危险的模式是：主进程已经触发 CUDA runtime / driver 初始化之后，再用默认 `fork` 启动子进程。`fork` 会复制父进程的用户态内存，但不会把 CUDA driver 内部线程、锁、上下文、句柄等状态完整变成一个可安全继续使用的新运行时。表现可能是：

- 子进程报 `Cannot re-initialize CUDA in forked subprocess`；
- 子进程卡死、随机失败，或在 H2D / D2H / profiler trace 上出现很难解释的异常；
- 父进程里看似只是创建 `Queue` / `Manager` / 后台 writer，实际已经隐式 fork 了子进程。

更稳的写法是显式拿一个非 `fork` 的 multiprocessing context，并让相关 primitives 都从同一个 context 创建：

```python
import multiprocessing as mp

mp_ctx = mp.get_context("forkserver")
manager = mp_ctx.Manager()

finished = manager.Value("finished", False)
disk_write_queue = mp_ctx.Queue(maxsize=max_queue_size)
disk_write_process = mp_ctx.Process(
    target=periodic_disk_write,
    name="disk_write_process",
    args=(finished,),
    daemon=True,
)
disk_write_process.start()
```

`forkserver` 是 Python `multiprocessing` 的一种 start method。第一次使用时，Python 会启动一个专门的 fork server 进程；后续新子进程不是从业务主进程直接 `fork`，而是由这个 server 进程来 `fork`。由于 fork server 通常更早、更干净，没有承载主进程里复杂的线程池、CUDA runtime、网络连接和全局锁状态，所以子进程继承到的脏状态更少。

可以简单理解三种 start method 的取舍：

- `fork`：最快，直接复制当前主进程；但会继承主进程的线程、锁、CUDA runtime 等复杂状态，GPU / 多线程场景风险最高。
- `spawn`：最干净，像重新启动一个 Python 解释器再 import 入口模块；安全但启动慢，对可序列化和模块导入要求更严格。
- `forkserver`：折中方案，由干净 server 负责 fork；通常比 `spawn` 快，比默认 `fork` 更适合 CUDA / 多线程 / 复杂 runtime。

这里的关键不是 `Manager` 本身，而是把 `Manager` / `Queue` / `Process` 都绑定到 `forkserver` context。`forkserver` 会通过一个相对干净的 server process 去 fork 子进程，避免直接从已经初始化 CUDA 的主进程 fork。相比 `spawn`，它通常启动成本低一些；相比默认 `fork`，它更适合 CUDA / 多线程 / 复杂 runtime 场景。

但它不是魔法，仍有几个边界：

- 必须尽量在 CUDA 初始化之前创建 / 启动 `forkserver` 相关子进程；如果 forkserver 自己已经导入或初始化了 CUDA，收益会打折。
- 不要混用 `mp.Queue()` 和 `mp_ctx.Process()`；跨 context 的锁、队列、manager proxy 可能引入新问题。
- 子进程 target、参数和被引用对象仍要满足可序列化 / 可导入约束，尤其是 `spawn` / `forkserver` 都不能依赖 fork 继承全部父进程状态。
- 如果子进程需要使用 CUDA，最稳原则是让它在自己的进程生命周期内初始化 CUDA，而不是继承父进程的 CUDA 状态。

经验规则：GPU 程序中一旦有后台进程、DataLoader worker、异步 writer、profile helper，就显式声明 start method / context；不要把默认 `fork` 留给运行时猜。

### subprocess

```python
import subprocess


def runCommand(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res = p.stdout.read()
    return res.strip("\n")
```

```python
def get_version():
    try:
        result = subprocess.check_output(['python3', '/path/script.py', \
                                '--operation', 'get_version'], \
                                env=py3_env, universal_newlines=True, stderr=subprocess.STDOUT)
        return result.split('\n')[-1]
    except subprocess.CalledProcessError as e:
        logging.exception('get_version error: {}'
                            .format(e.output))
    except IOError:
        logging.exception('Error: script not found')
    except Exception as e:
        logging.exception("Error: {}".format(str(e)))
    return
```

### func_timeout

* 超时控制

### schedule

https://stackoverflow.com/questions/15088037/python-script-to-do-something-at-the-same-time-every-day

```python
pip install schedule

import schedule
import time

class Scheduler:
  def job(self, t):
    logging.info(t)
    print(t)
  def func(self):
    t = 'Done'
    schedule.every().minutes.at(":17").do(self.job, t)
    while True:
        schedule.run_pending()
        time.sleep(1) # wait one second

nohup python2.7 MyScheduledProgram.py &
```

### 文件操作

* w+：读写
* w：写
* a：追加写入
* 文件指针变换：
  * file.seek(0)
  * file.seek(0, 2) 移动到最后

### shutil

```python
if os.path.exists(curr_path):
	shutil.rmtree(curr_path)
```

### os, sys

```python
import sys
import os
for arg in reversed(sys.argv[1:]):
    print(arg)

# 当前路径插入系统路径最高优先级，有效解决部分import问题
sys.path.insert(0,os.getcwd())
```

```python
os.path.join(dir,file)
os.makedirs
```

```python
os.getenv('ABC', 'abc') # 注意返回值是str
```

```shell
os.system
```



* popen
  * Check cmd的写法：`"grep \"failed:\"`

### sys

```python
from xxx import main
sys.exit(main())
```

### imp

[What does the first argument of the imp.load_source method do?](https://stackoverflow.com/questions/31773310/what-does-the-first-argument-of-the-imp-load-source-method-do)

```python
import imp
var_file = imp.load_source('var', file_path)
object = var_file.inside_object()

import var
object = var.inside_object()
```

### psutil

```python
proc = psutil.Process(pid)
children = proc.children(recursive=True)
```

## 异常、测试、调试与代码风格

### 异常处理

#### atexit

* 程序退出捕获signo

```python
import atexit
import sys
import signal

sig_no = None

def sig_handler(signo, frame):
  global sig_no
  sig_no = signo
  sys.exit(signo)

signal.signal(signal.SIGHUP, sig_handler)
signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

@atexit.register
def exit_hook():
```

#### traceback

```python
def handle_exception():
    exc_type, exc_value, exc_traceback_obj = sys.exc_info()
    error_message = traceback.format_exc()
    logging.log_every_n_seconds(logging.ERROR, f"exc_type: {exc_type}, error_message: {error_message}", 60)
    traceback.print_tb(exc_traceback_obj, limit=10)
```

### exception

* IOError (python2)
  * FileNotFoundError (python3)



* 系统基础异常

```python
try:
  ...
except Exception as e:
  ...
except (SystemExit, KeyboardInterrupt, GeneratorExit) as e:
  ...
```

### warnings

```python
import warnings
warnings.simplefilter("ignore")  # 屏蔽 ES 的一些Warnings
```

### logging

* 基础调用
  * `logging.log_every_n_seconds(logging.ERROR, f"", 60)`

### pdb

https://docs.python.org/zh-cn/3/library/pdb.html

```python
import pdb

pdb.set_trace()
```

```python
p dir(var)
```

* 也可breakpoint()直接进入pdb

### 测试

#### absl testing

```python
from absl.testing import parameterized

class AdditionExample(parameterized.TestCase):
  @parameterized.parameters(
    (1, 2, 3),
    (4, 5, 9),
    (1, 1, 3))
  def testAddition(self, op1, op2, result):
    self.assertEqual(result, op1 + op2)
```



#### unittest

```python
import unittest

class MyTestCase(unittest.TestCase):
  def testFunction(self):
    a= 1
    b= 2
    self.assertEqual(a, b)

if __name__ == '__main__':
	unittest.main()
```

```python
# mock sth
import contextlib
self._exit_stack = contextlib.ExitStack()
# context_manager: contextlib.AbstractContextManager
self._exit_stack.enter_context(context_manager)

mock_sleep = self._exit_stack.enter_context(mock.patch('time.sleep'))
mock_sleep.return_value = True
```
#### nosetests

```shell
# sudo pip install nose
nosetests -v autodiff_test.py --pdb --nocapture

--nocapture # print output
```

#### 小技巧

* 替换函数

```python
def sleep_func(self):
    time.sleep(1)
MyClass.sleep_func.__code__ = sleep_func.__code__
```

### 代码风格
format

* Autopep8

```
pip install autopep8
python -m autopep8 -i -r $folder
```

* Flake8
  * `pip install yapf`
  * VSCode setting.json 添加以下字段，文件页面
  * `~/.style.yapf` 文件

```json
"python.linting.flake8Enabled": true,
"python.formatting.provider": "yapf",
"python.linting.flake8Args": ["--max-line-length=120"],
"python.linting.pylintEnabled": false
```

```
[style]
based_on_style = google
indent_width = 2
```

* 静态static检查
  * mypy
  * .mypy.ini

```
[mypy]
ignore_missing_imports = True
```

## 环境搭建与工程工具

### 环境搭建

#### Docker

```shell
docker pull hub.xxx:yyy

docker container run -itd \
--network=host \
--security-opt seccomp=unconfined \
--mount type=bind,source=$(pwd),target=$(pwd) \
--mount type=bind,source=$HOME/.ssh,target=$HOME/.ssh \
--mount type=bind,source=/opt/tiger,target=/opt/tiger \
--mount type=bind,source=$HOME/.cache/bazel,target=$HOME/.cache/bazel \
--mount type=bind,source=/usr/local/bin/doas,target=/usr/local/bin/doas \
--mount type=bind,source=$HOME/tmp,target=/tmp \
--name $(whoami)_myproj_dev \
hub.xxx:yyy /bin/bash

docker exec -it $(whoami)_myproj_dev /bin/bash

pip3 install --upgrade pip

apt update --allow-insecure-repositories --allow-unauthenticated
apt install build-essential
```



#### 安装 Python3

* ./configure --prefix=$HOME/python3.10

```shell
sudo apt install libffi-dev # setuptools error
sudo apt install build-essential gcc
sudo apt install libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev libtk8.6 libgdm-dev libdb4o-cil-dev libpcap-dev

wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tar.xz
sudo tar -xvf Python-3.8.3.tar.xz
cd Python-3.8.3
./configure
make
make install
```

#### pyenv管理多版本

* 不一定work，有坑

````shell
brew update
brew install pyenv

# ~/.zshrc
eval "$(pyenv init --path)"

pyenv install 3.10
pyenv global 3.10
python --version
````

### 在线编辑器

https://onecompiler.com/

### virtualenv

```
virtualenv .myenv --python=python3.8
source .myenv/bin/activate
deactivate
```

[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)

```shell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple virtualenvwrapper

# 加入 zshrc
export WORKON_HOME=~/Envs
mkdir -p $WORKON_HOME
source /usr/local/bin/virtualenvwrapper.sh
# or
source ~/.local/bin/virtualenvwrapper.sh

mkvirtualenv env1
ls $WORKON_HOME
lssitepackages
workon env1

echo 'pip install sphinx' >> $WORKON_HOME/postmkvirtualenv
mkvirtualenv env3
```

* 坑
  * `Error while finding module specification for 'virtualenvwrapper.hook_loader' (ImportError: No module named 'virtualenvwrapper')
    virtualenvwrapper.sh: There was a problem running the initialization hooks`
    * 查看PATH，找错了python

### conda

```shell
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
conda create -n py37 -c anaconda python=3.7
conda activate py37
pip3 install --upgrade pip
pip3 install -r requirements.txt
conda deactivate
```

### pip

* whl格式本质上是一个压缩包，里面包含了py文件，以及经过编译的pyd文件

### setuptools

```python
from setuptools import find_packages
from setuptools import setup

PACKAGE_NAME = 'myproj'

setup(
  name=PACKAGE_NAME,
  version='1.0.8',
  description='',
  author=,
  author_email=,
  # Contained modules and scripts.
  packages=find_packages(),
  install_requires=[
    'cityhash==0.4.7',
    'hnswlib==0.8.0',
    'markdown_to_json==2.1.1',
    'jinja2==3.1.4',
    ...
  ],
  # Add in any packaged data.
  include_package_data=True,
  package_data={'': ['*.so', '*.txt', '*.cer']},
  zip_safe=False,
  ext_modules=[],
  # PyPI package information.
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python :: 3.8',
    'Topic :: Scientific/Engineering :: Mathematics',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Libraries',
  ],
  license='Apache 2.0',
  keywords='myproj'
)

# python setup.py sdist bdist_wheel

```

### 项目组织和module

* \__init__.py
  * 自 Python 3.3 起，`__init__.py` 文件不再是创建包的必要条件，包可以是“命名空间包”。但是，保留 `__init__.py` 仍然是一个良好的实践，特别是在大型项目中。

* [__all\_](https://zhuanlan.zhihu.com/p/54274339)_
   * 控制 from xxx import 的行为，定义公共接口
   * 为 lint 等代码检查工具提供辅助

#### Hydra: 基于yaml管理复杂项目

https://hydra.cc/docs/intro/

### argparse

```python
import argparse
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_xxx', type=int, default=10, help='number of xxx')
    args = parser.parse_args()

# 设计模式：可以直接把args传入程序中的各种类作为self._args成员

# subparser
subparsers = parser.add_subparsers(help='sub-command help')
#添加子命令 add
parser_a = subparsers.add_parser('add', help='add help')
parser_a.add_argument('-x', type=int, help='x value')
parser_a.add_argument('-y', type=int, help='y value')
#设置默认函数
parser_a.set_defaults(func=add)
#添加子命令 sub
parser_s = subparsers.add_parser('sub', help='sub help')
parser_s.add_argument('-x', type=int, help='x value')
parser_s.add_argument('-y', type=int, help='y value')
#设置默认函数
parser_s.set_defaults(func=sub)

args = parser.parse_args()
args.func(args)

$python subc.py add -x 1 -y 2
x + y =  3
$python subc.py sub -x 1 -y 2
x - y =  -1
```

### absl

* absl.app

```python
import absl.app
import absl.flags

FLAGS = absl.flags.FLAGS

absl.flags.DEFINE_string('name', 'world', 'The name to greet')


def main(argv):
    print(f'Hello, {FLAGS.name}!')


if __name__ == '__main__':
    absl.app.run(main)
```

### dotenv

* https://stackoverflow.com/questions/44761958/using-pip3-module-importlib-bootstrap-has-no-attribute-sourcefileloader

```shell
pip3 install python-dotenv
```

### ipython

重启kernel，释放GPU内存
```python
import IPython
app = IPython.Application.instance()
app.kernel.do_shutdown(True)
```



```python
counters = [Counter.remote() for _ in range(10)]  # 创建10个Counter实例
```



[Using the Python zip() Function for Parallel Iteration](https://realpython.com/python-zip-function/)

* python2返回list，python3返回iterator
	* python2耗内存，可以用`iterator.izip(*iterables)`
* 支持sorted函数和sort方法
```python
list(zip(numbers, letters))

try:
    from itertools import izip as zip
except ImportError:
    pass

pairs = [(1, 'a'), (2, 'b'), (3, 'c'), (4, 'd')]
numbers, letters = zip(*pairs)
```



```python
#!/usr/bin/env python
def fib0(): return 0
def fib1(): return 1

s = """def fib{}(): return fib{}() + fib{}()"""

if __name__ == '__main__':

    for n in range(2, 10):
       exec(s.format(n, n-1, n-2))
    from functools import lru_cache
    for n in range(10):
           exec("fib{} = lru_cache(1)(fib{})".format(n, n))
    print(eval("fib9()"))
```

### cython

[Cython加密打包python package](https://cloud.tencent.com/developer/article/1661136)

### jinja2

```python
from jinja2 import Templatei

# 定义模板字符串
template_string = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <ul>
        {% for item in items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>
</body>
</html>
"""

# 创建模板对象
template = Template(template_string)

# 数据
data = {
    'title': 'My Page',
    'heading': 'Welcome to My Page',
    'items': ['Item 1', 'Item 2', 'Item 3']
}

# 渲染模板
output = template.render(data)

# 输出结果
print(output)
```

### mpl_toolkits

```python
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.gca(projection='3d')

ax.scatter(w_array, b_array, loss_array)
ax.set_xlabel('w', size=16)
ax.set_ylabel('b', size=16)
ax.tick_params(labelsize=12)

plt.show()
```

### fastapi

```python
from fastapi.routing import APIRouter, APIRoute
```

#### SSE能力 (Server-Sent Events)

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI()


async def event_generator(request: Request):
    """
    生成事件的异步函数，用于持续推送数据给客户端，直到客户端断开连接。
    """
    while True:
        if await request.is_disconnected():
            break

        # 这里模拟获取实时股票价格数据，实际应用中应该从数据源获取真实数据
        stock_price = {
            "symbol": "AAPL",
            "price": round(random.uniform(100, 200), 2)
        }

        yield f"data:{json.dumps(stock_price)}\n\n"

        await asyncio.sleep(5)


@app.get("/events/")
async def sse_events(request: Request):
    """
    处理SSE请求的路由函数，返回一个StreamingResponse，通过事件生成器持续推送数据。
    """
    return StreamingResponse(event_generator(request), media_type="text/event-stream")
```

```python
@app.post('/rec/...')
async def stream_search(request: ...Request):
  side_info = {}
  side_info['state'] = '...'
  q = request.query
  start = time.perf_counter()

  async def stream():
    loop = asyncio.get_event_loop()
    task = loop.create_task(
        asyncio.to_thread(task_internal, ...))
    sent_keys = set()
    old_state = ""
    while True:
      need_yield = False
      new_keys = set(
          [k for k, v in side_info.items() if v and k not in sent_keys])
      if len(new_keys) > 0:
        sent_keys = sent_keys | new_keys
        need_yield = True
      if side_info['state'] != old_state:
        old_state = side_info['state']
        need_yield = True
      if need_yield:
        yield f"{json.dumps({'side_info': side_info}, ensure_ascii=False)} \n"
      if search_task.done():
        break
      await asyncio.sleep(1)
    answer_prompt = await task
    if task.exception() is not None:
      print(f"task_internal error: {task.exception()}")
    side_info['state'] = '生成答案'
    print("time elapsed before answering: ", time.perf_counter() - start, "s")
    answer_stream = LLMService().stream_chat(prompt=answer_prompt)
    prefix = []
    for delta in answer_stream:
      prefix.append(delta)
      # print('delta:', delta, end='', flush=True)
      prefix_str = ''.join(prefix)
      answer = f"{json.dumps({'answer': prefix_str.strip(), 'side_info': side_info}, ensure_ascii=False)} \n"
      yield answer

  return StreamingResponse(stream(), media_type="text/event-stream")
```

### streamlit - WebApp

* Streamlit 的脚本是自上而下执行的，每次用户交互（如点击按钮）都会重新运行整个脚本。这意味着你不需要显式地创建循环，而是通过状态管理和条件判断来实现对话的连续性。

### 网络

* python传文件

```
tar -cvf file.tar file
python -m SimpleHTTPServer 99**
# python3 -m http.server 99**
wget **.**.**.**:99**/tf_model.tar
tar -xvf file.tar
```
