## Algorithms-Potpourri

* [格林公式在面积并问题中的应用](https://trinkle23897.github.io/posts/calc-circle-area-union) --- by n+e

* [Three Optimization Tips for C](https://www.slideshare.net/andreialexandrescu1/three-optimization-tips-for-c-15708507)

  * You can't improve what you can't measure

  * Reduce strength

  * Minimize array writes


```c++
uint32_t digits10(uint64_t v) {
  if (v < P01) return 1;
  if (v < P02) return 2;
  if (v < P03) return 3;
  if (v < P12) {
    if (v < P08) {
      if (v < P06) {
        if (v < P04) return 4;
        return 5 + (v < P05);
      }
      return 7 + (v >= P07);
    }
    if (v < P10) {
      return 9 + (v >= P09);
    }
    return 11 + (v >= P11);
  }
  return 12 + digits10(v/P12);
}

unsigned u64ToAsciiTable(uint64_t value, char* dst) {
  static const char digits[201] =
    "0001020304050607080910111213141516171819"
    "2021222324252627282930313233343536373839"
    "4041424344454647484950515253545556575859"
    "6061626364656667686970717273747576777879"
    "8081828384858687888990919293949596979899"
  uint32_t const length = digits10(value);
  uint32_t next = length - 1;
  while (value >= 100) {
    auto const i = (value % 100) * 2;
    value /= 100;
    dst[next] = digits[i + 1];
    dst[next - 1] = digits[i];
    next -= 2;
  }
  if (value < 10) {
    dst[next] = '0' + uint32_t(value);
  } else {
    auto i = uint32_t(value) * 2;
    dst[next] = digits[i + 1];
    dst[next - 1] = digits[i];
  }
  return length;
}
```

### 计算复杂性：P 与 NP

P 与 NP 问的是：**凡是拿到候选答案后容易验证的问题，是否也都容易找到答案？** 它讨论输入规模增长时的计算量，不是计算机够不够快。截至 2026-11-21，问题仍未解决。[Clay Mathematics Institute：P vs NP](https://www.claymath.org/millennium/p-vs-np/)

#### 从“检查清单”到“找出清单”

给一组正整数和目标值 T，问是否能选出若干个数，使总和恰好等于 T。这是**子集和问题**：

- 拿到候选清单，加一遍就能检查。例如从 3、8、14、21 中选出 3、8、14，总和为 25。
- 从头找清单，朴素方法要尝试各种组合；n 个数共有 2 的 n 次方个子集。但“枚举很慢”不证明不存在更聪明的算法。

严格地说，P、NP 都是**判定问题**的集合，输出为“是 / 否”，例如“是否存在这样的清单”，而不是直接输出清单。

| 类别 | 含义 | 易混点 |
| --- | --- | --- |
| P | 存在确定性算法，在输入长度的多项式时间内判定答案 | P 的 P 是 Polynomial（多项式） |
| NP | 对“是”的实例，存在长度为输入规模多项式的证书，可在多项式时间内核验 | NP 是 Nondeterministic Polynomial time，不是“非多项式”或“所有难题” |
| NP 完全 | 属于 NP，且所有 NP 问题都能在多项式时间内归约到它 | 只要其中一个有多项式时间算法，就能证明 P＝NP；SAT、子集和是典型例子 |

能快速求解，自然可以快速核验，所以已知：

$$
P\subseteq NP
$$

未知的是这个包含关系是否严格。NP 只要求“是”的实例有短证书；没有找到解，不等于已经快速证明无解。[Stephen Cook：官方问题说明，定义与 NP 完全性](https://www.claymath.org/wp-content/uploads/2022/02/MPPc.pdf#page=84)

#### “快”是增长速度，不是秒数

设 n 是**输入编码的总长度**，包括数字占多少位。多项式时间允许平方、立方以及任意固定次数的增长；指数增长则可能在规模稍大时迅速失控。

但多项式也可能是：

$$
T(n)=n^{1000}
$$

它在理论上属于多项式时间，现实中仍可能无法使用；巨大常数也一样。因此证明 P＝NP，不保证立刻得到实用算法。反过来，P≠NP 也只意味着 NP 中存在最坏情况下无法用多项式时间解决的问题，不意味着所有实例都难，更不等于已经证明必须花指数时间。[Scott Aaronson：P ?= NP，§1.2.1–1.2.2、§5.1](https://www.scottaaronson.com/papers/pnp-kindle.pdf)

子集和的动态规划常写成 O(nT)，这里 n 表示数的个数。它对目标值 T 的**数值**是多项式，却未必对 T 的**位数**是多项式，所以属于伪多项式算法，不能据此证明 P＝NP。

#### 如果 P＝NP，究竟改变什么

所有 NP 判定问题都会有多项式时间算法，相应的短证书也能在多项式时间内找出。例如对 SAT（布尔可满足性），逐个尝试把变量固定为真或假，每次询问剩下的公式是否仍有解，就能重建一份满足赋值。许多具有合适编码和界限的排程、路线与离散优化问题会因此获得理论上的高效算法；若算法足够实用，影响会非常大。[Cook：判定到搜索的归约，印刷页 93](https://www.claymath.org/wp-content/uploads/2022/02/MPPc.pdf#page=90)

这仍不等于所有计算都变简单。某些任务要统计解的数量、生成巨大输出、维持高精度或模拟长时间演化；不能不加论证，就把它们都归入 NP 的“找一个短证书”问题。量子计算还有自身的复杂性问题，P 与 NP 的定义以经典计算为背景。[Aaronson：§2.2.1、§2.2.6、§5.5](https://www.scottaaronson.com/papers/pnp-kindle.pdf)

#### 为什么不能由此推出“我们几乎必在模拟中”

待核验的说法把两步连在了一起：

> “若 P = NP，海量组合优化与状态搜索的算力开销骤降”，高级文明便能以“极低的硬件代价”运行大量祖先模拟；当“虚拟宇宙”的数量远多于“物理母宇宙”，我们身处虚拟世界的几率就“趋近于100%”。

这段延伸没有提供出处，不能视为博斯特罗姆的原话或既有数学结论。它至少漏了三层前提：

1. **理论可解不等于硬件代价极低。** 多项式次数、常数、内存、精度、输出量、持续运行时间和能耗都还在。P≠NP 也没有直接证明量子多体演化、真实蛋白质折叠和社会预测必然都需要天文算力；它们涉及不同的问题定义与精度要求。
2. **模拟可行不等于大量模拟真的存在。** 还需假设文明能发展到相应阶段、模拟能产生意识，而且文明有意愿和资源运行足够多的模拟。博斯特罗姆的论证本身也不要求逐粒子精确模拟整个宇宙；他在 FAQ §6 明确讨论按观察需求保留细节的简化模拟。
3. **计数对象应是可比较的观察者或观察经历，而非宇宙个数。** 只有在选定参照类、接受相应典型性假设，并且模拟观察者占绝大多数时，数量优势才支持高概率判断；这不是 P＝NP 单独给出的结论。

博斯特罗姆的原始论证是三种可能**至少一种成立**：人类几乎不能进入后人类阶段；进入该阶段的文明几乎不运行大量祖先模拟；或者我们几乎肯定身处模拟。他并未据此断言第三种已经成立，也不愿给出貌似精确的概率。[作者 FAQ：§1–2、§6](https://simulation-argument.com/faq/)

更稳妥的表述是：**如果 P＝NP 且有实用算法，某些搜索与优化任务可能大幅提速；这或许降低某些模拟的部分成本，但既不能证明高保真意识模拟廉价可行，也不能确定我们身处模拟的概率。**

### 数据

在GPU里针对单精度和双精度就需要各自独立的计算单元, 一般在GPU里支持单精度运算的单精度ALU(算术逻辑单元)称之为FP32 core, 而把用作双精度运算的双精度ALU称之为DP unit或者FP64 core. 

- FP64: 用8个字节来表达一个数字, 1位符号, 11位指数, 52位小数，**有效位数为16位**. 常用于科学计算, 例如: 计算化学, 分子建模, 流体动力学
- FP32: 用4个字节来表达一个数字, 1位符号, 8位指数, 23位小数，**有效位数为7位**. 常用于多媒体和图形处理计算、深度学习、人工智能等领域
- FP16: 用2个字节来表达一个数字, 1位符号, 5位指数, 10位小数，**有效位数为3位**. 常用于精度更低的机器学习等



### 数据结构

#### Hash Table

* Open Hashing (Closed Addressing) v.s. Close Hashing (Open Addressing)
  * https://programming.guide/hash-tables-open-vs-closed-addressing.html
  * Open Hashing 的缺点：
    * 读放大
    * load key 有额外一次 memory read
    * rehash 时整个结构要重建
* [Hopscotch hashing](https://en.wikipedia.org/wiki/Hopscotch_hashing)
* Cuckoo Hashing: https://web.stanford.edu/class/archive/cs/cs166/cs166.1146/lectures/13/Small13.pdf
* GeoHash
* Key的均衡性
  * [MurmurHash](https://github.com/aappleby/smhasher/blob/master/src/MurmurHash3.cpp)
* HashTable实现中可用的设计：
  * per dim合并
    * 记录available indices提升分配速度
  
  * map只存indices，提升rehash速度
  

##### Hash Collision

https://preshing.com/20110504/hash-collision-probabilities/

* 存在冲突的概率：$$\frac{k^2}{2N}$$

![image-20251028140434370](./Algorithms-Potpourri/image-20251028140434370.png)

* 冲突次数的期望：近似为 $$\frac{k^2}{N}$$
  * 冲突率：近似为 $$\frac{k}{N}$$
  * 证明：1）利用二项分布；2）假设每个位置最多冲突一次




#### LRU cache

* [linked-list based LRU cache](https://krishankantsinghal.medium.com/my-first-blog-on-medium-583159139237)
  * hashmap的value存双向链表节点的指针
* array-list based LRU cache
  * hashmap的value存array-list的index
    * Array-list的value存pre-index + post-index + entry
  * e.g. Persia
* Python 3 工程实现（哨兵双向链表 LRU、惰性删除堆与 `bisect` 版本化快照查表）见 [python.md - 算法与有状态编码原语](./python.md#算法与有状态编码原语python-3)

#### Radix Tree

[radix tree (Linux 内核实现)](https://lwn.net/Articles/175432/)：压缩前缀树，维护 kv 查找

前缀树的结构：

* 一棵子树的所有子节点都有相同前缀的 key 值

* 只有叶子节点有对应的 value 值

* key的最大长度固定

当 key 有以下特性的时候压缩前缀树比 hashmap 更具优势：

* 当存储的 key 值本身就有很好的 hash 特性，但是又非常稀疏时。比如说网段，地址空间，可以不用设计复杂 hash 函数。每次插入查找没有hash 计算的开销。
* 大量的 key 有着相同的前缀时，相比于 hashmap 每个节点都要存储完整的 key 值，更具有空间复杂度优势。

应用：[Trie](https://en.wikipedia.org/wiki/Trie)

#### Pairing Heap

https://en.wikipedia.org/wiki/Pairing_heap

实现简单、均摊复杂度优越，用于实现优先队列

定义：一个配对堆要么是一个空堆，要么由一个根元素与一个可能为空的配对堆子树列表所组成。所有子树的根元素都大于该堆的根元素。

```python
type PairingTree[Elem] = Heap(elem: Elem, subheaps: List[PairingTree[Elem]])
type PairingHeap[Elem] = Empty | PairingTree[Elem]
```

操作：

* 合并：一个空堆与另一个堆合并将会返回另一个堆；否则将会返回一个新堆，其将两个堆的根元素中较小的元素当作新堆的根元素，并将较大的元素所在的堆合并到新堆的子堆中。

```C++
function merge(heap1, heap2: PairingHeap[Elem]) -> PairingHeap[Elem]
  if heap1 is Empty
    return heap2
  elsif heap2 is Empty
    return heap1
  elsif heap1.elem < heap2.elem
    return Heap(heap1.elem, heap2 :: heap1.subheaps)
  else
    return Heap(heap2.elem, heap1 :: heap2.subheaps)
```

* 插入：将一个仅有该元素的新堆与需要被插入的堆合并。

```c++
function insert(elem: Elem, heap: PairingHeap[Elem]) -> PairingHeap[Elem]
  return merge(Heap(elem, []), heap)
```

* 删除最小：根元素即为最小元素。删除根元素，然后合并子树，合并方法为从左到右两两合并，然后再从左向右顺序合并。

```c++
function delete-min(heap: PairingHeap[Elem]) -> PairingHeap[Elem]
  if heap is Empty
    error
  else
    merge-pairs(heap.subheaps)
    return elem: Elem
function merge-pairs(list: List[PairingTree[Elem]]) -> PairingHeap[Elem]
  if length(list) == 0
    return Empty
  elsif length(list) == 1
    return list[0]
  else
    return merge(merge(list[0], list[1]), merge-pairs(list[2..]))
```

#### BloomFilter

https://en.wikipedia.org/wiki/Bloom_filter



### 数据处理

#### TopK

* std是对topK的近似

```python
 def get_topk_amax(tensor, percentile):
      tensor = tf.abs(tensor)
      tensor = tf.reshape(tensor, [-1])
      tensor_size = tf.cast(tf.size(tensor), tf.float32)
      k = tf.math.maximum(1, tf.cast(tf.math.ceil(tensor_size * (1-percentile)), tf.int32))
      topk, _ = tf.math.top_k(tensor, k=k)
      target_amax = topk[-1]
      return target_amax

  def get_std_amax(tensor, std_scale):
      return tf.abs(tf.reduce_mean(tensor)) + std_scale * tf.math.reduce_std(tensor)      

  def get_max_amax(tensor):
      return tf.reduce_max(tf.abs(tensor))
```





### 图算法

* Dijkstras's 算法：图的最短路径
  * 分层cluster的思想，超越dijkstras https://www.quantamagazine.org/new-method-is-the-fastest-way-to-find-the-best-routes-20250806/

* 社区发现 Louvain算法 https://zhuanlan.zhihu.com/p/558706129
