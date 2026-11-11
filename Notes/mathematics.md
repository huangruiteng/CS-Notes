# Mathematics

## 数

### 指数

* $$\lim_{n\rightarrow \infty} (1+1/n)^n = e$$



## 基础运算

### 空集的极值与单位元

* 对空集做 reduce_max 返回 -∞，reduce_min 返回 +∞，这不是随意约定，而是**幺半群（Monoid）单位元**的必然结果
* 数学原理：max 在扩展实数域 $$\overline{\mathbb{R}} = \mathbb{R} \cup \{-\infty, +\infty\}$$ 上构成交换幺半群 $$(\overline{\mathbb{R}}, \max, -\infty)$$，其中 -∞ 是单位元；min 则是 $$(\overline{\mathbb{R}}, \min, +\infty)$$
* 单位元必须满足：$$\max(a, -\infty) = a$$，$$\min(a, +\infty) = a$$，对空集做 reduce 等价于无元素的累积运算，结果只能是单位元
* 同理：空集求和 = 0（加法单位元），空集求积 = 1（乘法单位元）
* 推广：$$\sup \emptyset = -\infty$$，$$\inf \emptyset = +\infty$$（扩展实数域上的上确界/下确界）
* 参考：[Empty set - Wikipedia](https://en.wikipedia.org/wiki/Empty_set#Extended_real_numbers)

### 进制

* 关于10进制有效数字位数可用下面这个公式来估算：
  * $$n \approx log_{10}(2^m) = m \times log_{10}(2) \approx m \times 0.3010$$

### 位运算

* 对于一个数 X 和一个2的幂 P ，$$X \% P = X \& (P - 1)$$





## 概率论与数理统计

> 阅读主线：概率语言 → 常见分布 → 抽样误差 → 统计目标与估计 → 假设检验。因果推断建立在这条主线上，不能用一组新术语替代这些基础。参考：[Hernán & Robins, *Causal Inference: What If*, Ch. 1–3](https://miguelhernan.org/s/hernanrobins_WhatIf_19aug26.pdf)。

### 概率语言：随机变量、条件化与独立性

**随机变量、总体量与样本观测是三个层次。** 随机变量 $Y$ 描述尚未实现的结果及其分布；$Y_i=y_i$ 是第 $i$ 个样本的一次实现；总体均值 $E[Y]$ 是分布的性质，样本均值 $\bar Y$ 是用有限样本计算的统计量。把样本统计量直接当成总体真值，会漏掉抽样误差。

**条件化是在已知一部分信息后更新分布。** 条件概率与条件期望分别写作：

$$
P(Y\in B\mid X=x),\qquad E[Y\mid X=x]
$$

离散 $X$ 下，全概率公式与全期望公式把分组结果还原为总体结果：

$$
P(Y\in B)=\sum_x P(Y\in B\mid X=x)P(X=x)
$$

$$
E[Y]=\sum_x E[Y\mid X=x]P(X=x)
$$

因此“各组均值”和“总体均值”并不是两套互不相关的结论；总体结果还取决于各组占比。这也是理解标准化、加权与辛普森悖论的基础。

**独立与条件独立不同。** $X\perp Y$ 表示知道 $X$ 不改变 $Y$ 的分布；$X\perp Y\mid Z$ 表示固定 $Z$ 后，$X$ 不再提供关于 $Y$ 的额外信息。边缘上相关的变量可能在分层后条件独立，边缘上独立的变量也可能因条件化而相关。因此“控制更多变量”不是机械地越多越好：要先说明变量与数据生成过程的关系。

#### 结果随机性与参数不确定性

以固定方案的成功率为例：

$$
Y\mid\theta\sim\operatorname{Bernoulli}(\theta).
$$

即使已知 θ = 0.8，下一次仍可能失败，这是给定模型下的结果随机性（aleatoric uncertainty）；如果连 θ 是 0.6 还是 0.9 都不清楚，则还存在参数认识不足（epistemic uncertainty）。更多合适的实验可以减少后者，但不会自动消除前者。

给 θ 指定先验，是用分布表达对固定未知成功率的认识，不是说每次试验都重新抽取真实成功率。重复测试固定方案主要更新认识；修改方案、训练模型或改变任务分布，则可能改变成功率本身。两者不能混作同一种数据积累过程。参见 [Beta 共轭模型](#beta-分布与共轭先验)与[元推理中的计算选择](./Reinforcement-Learning.md#元推理与计算选择)。

**共享未知参数，会让条件独立的观测在边缘上相关。** 假设两次试验在给定 θ 后独立，θ 的先验为 Beta(1,1)，则：

$$
P(Y_1=1,Y_2=1)=\mathbb E[\theta^2]=\int_0^1\theta^2\,d\theta=\frac13
\ne P(Y_1=1)P(Y_2=1)=\frac14.
$$

第一次成功后，更相信这个共同的 θ 较大，第二次成功概率从 1/2 更新为 2/3，因此“两次都成功”的概率是 1/2 × 2/3 = 1/3。改变的是认识，不是第一次成功物理上提高了第二次成功率。若每次都独立重抽一个 θ，才会得到另一种模型下的 1/4。这个区别决定了[多步采样例子](./Reinforcement-Learning.md#一步没有收益为何两步可能值得)中各分支怎样加权。

#### 条件期望的塔式法则

**先按细分信息求平均，再按各组概率加权，等于直接按较粗信息求平均。** 假设 $\mathbb E[|Y|]<\infty$。条件期望 $\mathbb E[Y\mid X]$ 本身是随 $X$ 变化的随机变量；对它再求期望，就得到全期望公式：

$$
\mathbb E[\mathbb E[Y\mid X]]
=\sum_x\mathbb E[Y\mid X=x]P(X=x)
=\mathbb E[Y]
$$

这里以离散 $X$ 为例，连续情形改用积分。例如两组人的平均分是 70 和 90，占比分别为 75% 和 25%，总体均分是 $0.75\times70+0.25\times90=75$，不能把两组均分不加权地平均成 80。

**塔式法则允许外层仍保留一部分信息。** 内层知道 $X,Z$，外层只知道 $X$，则：

$$
\boxed{\mathbb E\!\left[\mathbb E[Y\mid X,Z]\mid X\right]=\mathbb E[Y\mid X]}
$$

固定 $X=x$ 后，对还不知道的 $Z$ 按条件分布加权即可证明（离散情形）：

$$
\mathbb E\!\left[\mathbb E[Y\mid X,Z]\mid X=x\right]
=\sum_z\mathbb E[Y\mid X=x,Z=z]P(Z=z\mid X=x)
=\mathbb E[Y\mid X=x]
$$

外层信息要包含在内层信息中；不要求变量独立，也不能对任意两组不嵌套的条件直接消去内层。

#### 鞅与次鞅：条件平均怎样变化

鞅（读 yāng，martingale）可以从公平赌局理解；次鞅（submartingale）允许赌局在平均上对你有利。它们描述一串随时间变化的随机量，不限于金钱，也可以是对候选价值的估计。

令 X_t 为当前值，D_t 为截至当前已知的全部信息。假设 X_t 可由 D_t 确定、期望绝对值有限，且后续信息包含此前信息，则：

$$
\begin{aligned}
\text{鞅：}\quad &\mathbb E[X_{t+1}\mid D_t]=X_t,\\
\text{次鞅：}\quad &\mathbb E[X_{t+1}\mid D_t]\ge X_t.
\end{aligned}
$$

条件期望就是“站在现在，按已知信息对下一步可能结果加权”。定义要求每一步给定已有信息时都成立，仅有总体均值不变或上涨还不够。

例如当前有 100 元，每轮独立抛一次公平硬币：

| 过程 | 正面 / 反面的余额变化 | 下一轮预期余额 | 含义 |
| --- | --- | --- | --- |
| 鞅 | +1 / −1 元 | 100 元 | 平均不赚不亏，但实际会涨跌。 |
| 次鞅 | +2 / −1 元 | 100.5 元 | 平均有利，但仍有一半概率亏 1 元。 |

**鞅是“条件平均不变”，次鞅是“条件平均不降”，都不是每条实际路径的单调性。** 次鞅允许等号，因此鞅也是次鞅；“次”不表示更差或更低。

##### 后验均值的鞅性质

**固定候选的后验均值不会事前平均上涨，是塔式法则的应用。** 在同一概率模型下，固定未知参数 $\theta$，记当前全部证据为 $D_t$，增加一次观察后为 $D_{t+1}$，后验均值为 $\mu_t=\mathbb E[\theta\mid D_t]$。由于新证据包含旧证据：

$$
\mathbb E[\mu_{t+1}\mid D_t]
=\mathbb E\!\left[\mathbb E[\theta\mid D_{t+1}]\mid D_t\right]
=\mathbb E[\theta\mid D_t]
=\mu_t
$$

这也称为后验均值的**鞅性质**：在看到新结果前，对下一次估值的预测就是当前估值，平均按当前模型对新结果的预测概率加权。例如 $\operatorname{Beta}(1,1)$ 的当前均值为 $1/2$；下一次成功、失败各有 $1/2$ 概率，更新后的均值分别为 $2/3$、$1/3$，加权后仍是 $1/2$。**单次更新可以涨也可以跌；“不凭空上涨”说的是事前平均，不是每次估值不许涨。** 信息仍可能通过改变最终选中的候选，提高预期决策收益。

##### 观察后再选择：最大后验均值的次鞅性质

**为什么先观察再选择，预期收益不会降低？** 设有限个固定候选的效用为 $U_i$，均可积，当前估值为 $\mu_i(s)=\mathbb E[U_i\mid s]$，新状态 $s'$ 包含旧信息。给定 $s$，先固定当前赢家 $i^*\in\arg\max_i\mu_i(s)$。无论新观察是什么，新最大值都不低于这个原赢家的**新估值**：

$$
\max_i\mu_i(s')\ge\mu_{i^*}(s')
$$

取条件期望保持大小关系，再用塔式法则：

$$
\begin{aligned}
\mathbb E[\max_i\mu_i(s')\mid s]
&\ge\mathbb E[\mu_{i^*}(s')\mid s]\\
&=\mu_{i^*}(s)\\
&=\max_i\mu_i(s)
\end{aligned}
$$

**何时严格大于？** 两边之差可写成“重新选择相对坚持原赢家的收益”：

$$
\Delta(s)
=\mathbb E[\max_i\mu_i(s')\mid s]-\max_i\mu_i(s)
=\mathbb E[\max_i\mu_i(s')-\mu_{i^*}(s')\mid s].
$$

括号内始终非负，因此：

$$
\Delta(s)>0
\iff P\!\left(\max_i\mu_i(s')>\mu_{i^*}(s')\mid s\right)>0.
$$

即新信息有正概率让其他候选严格超过**原赢家更新后的估值**。如果原赢家始终仍在最优集合中，就取等号；只减少不确定性，或在并列最优者之间换选，都不足以产生严格增益。

例如 A 的价值已知为 0.7；B 等概率为 0.9 或 0.3，当前均值为 0.6。现在选 A 得到 0.7；先查明 B，好时选 B、差时选 A，预期价值为 0.8，毛增益为 0.1。若 B 只能是 0.5 或 0.6，查明后仍选 A，毛增益为 0。B 的均值没有平均上涨，收益来自**按新信息切换选择的机会**。

因此，固定候选的后验均值是鞅；有限个候选的最大后验均值是**次鞅**，即给定当前信息，下一步的条件期望不低于当前值。

由于 max 是凸函数，上述不等式也可由条件 Jensen 不等式结合塔式法则得到。结论依赖一致的概率模型与新旧信息的包含关系，不要求候选独立。它保证的是事前平均，不保证每次观察后的最大估值都上升；这里也未扣除获取信息的成本。加入成本，并允许根据观察结果决定继续或停止，就得到[计算与停止的 Bellman 方程](./Reinforcement-Learning.md#计算与停止把信息获取也看成动作)。

参考：[全期望公式与塔式法则](https://en.wikipedia.org/wiki/Law_of_total_expectation)；[Selecting Computations：信念状态与计算价值](https://aima.cs.berkeley.edu/~russell/papers/uai12-meta.pdf)。

#### 贝叶斯公式：先验、似然与后验

**贝叶斯更新：用新数据对各个参数假设重新加权，再归一化。** $\theta$ 是未知参数（如成功率），$D$ 是已经观察到的数据（如一次成功）。

| 项 | 含义 |
| --- | --- |
| 先验 $p(\theta)$ | 看到这批数据前，对各个参数值的认识 |
| 似然 $p(D\mid\theta)$ | 假设参数为 $\theta$，出现当前数据的概率或密度；衡量数据对该假设的支持 |
| 后验 $p(\theta\mid D)$ | 看到数据后，对各个参数值更新后的认识 |

公式来自同一个联合分布的两种分解：

$$
p(\theta,D)=p(D\mid\theta)p(\theta)=p(\theta\mid D)p(D)
$$

移项即得（分母为正时）：

$$
p(\theta\mid D)
=\frac{p(D\mid\theta)p(\theta)}{p(D)}
\propto p(D\mid\theta)p(\theta)
$$

**比例号省略了归一化分母。** 固定已观察到的 $D$，$p(D)$ 对各个 $\theta$ 都相同；连续参数下由全概率公式得到：

$$
p(D)=\int p(D\mid\vartheta)p(\vartheta)\,d\vartheta
$$

离散参数则改用求和。$p(D)$ 是数据的边际概率或密度；除以它，后验才能积分或求和为 1。似然是在固定数据后比较不同参数的函数，**不等于参数的概率分布**，也不能把条件方向反过来直接当成后验。

例如，只考虑成功率 $\theta=0.8$ 和 $0.2$ 两个假设，先验各为 $1/2$。观察到一次成功后，两者未归一化权重为 $0.8\times0.5=0.4$ 和 $0.2\times0.5=0.1$；总和为 $0.5$，所以后验分别为 $0.8$ 和 $0.2$。这里后验的 $0.8$ 表示“成功率为 0.8 这个假设的概率”，不是下一次成功的预测概率。连续参数也遵循同样的加权逻辑，见下文 [Beta 共轭更新](#beta-分布与共轭先验)。

参考：[Bayes' theorem：条件概率推导与参数形式](https://en.wikipedia.org/wiki/Bayes%27_theorem)。

### 常见分布

#### 正态分布

- 约 68.27% 的数值落在 μ ± 1σ 的范围内。
- 约 95.45% 的数值落在 μ ± 2σ 的范围内。
- 约 99.73% 的数值落在 μ ± 3σ 的范围内。

#### 二项分布

*   **定义**: 描述了在 $n$ 次独立的伯努利试验中，成功次数为 $k$ 的概率。每次试验只有两种结果（成功/失败），且单次成功的概率为 $p$。
*   **概率质量函数 (PMF)**: 随机变量 $X \sim B(n, p)$，在 $n$ 次试验中恰好成功 $k$ 次的概率为：
    $P(X=k) = C(n, k) p^k (1-p)^{n-k} = \frac{n!}{k!(n-k)!} p^k (1-p)^{n-k}$
*   **核心性质**:
    *   **期望 (均值)**: $E[X] = np$
    *   **方差**: $Var(X) = np(1-p)$

#### Beta 分布与共轭先验

##### 定义与归一化

**Beta 是定义在 $[0,1]$ 上的一族分布，可以用来表示对未知成功率的认识。**“Beta 先验具有下面的形式”是在引用这个分布族的定义；先验并不都必须采用 Beta。其概率密度为：

$$
p(\theta)=\frac{\theta^{\alpha-1}(1-\theta)^{\beta-1}}{B(\alpha,\beta)},
\qquad 0<\theta<1,\quad \alpha,\beta>0
$$

先用非负函数描述密度形状，再除以它在整个区间的积分，使总概率等于 1：

$$
B(\alpha,\beta)=\int_0^1 t^{\alpha-1}(1-t)^{\beta-1}\,dt
$$

因此，比例号 $\propto$ 省略的是与 $\theta$ 无关的归一化常数 $1/B(\alpha,\beta)$。$p(\theta)$ 是密度，区间上的积分才是概率。指数写成 $\alpha-1$、$\beta-1$ 是参数化约定：端点附近的幂次大于 −1 时积分有限，条件便写成 $\alpha,\beta>0$；$\alpha=\beta=1$ 时两个指数为零，恰好得到均匀分布。

例如，$\operatorname{Beta}(2,2)$ 的形状与 $\theta(1-\theta)$ 成正比，其积分为 $1/6$，所以密度是 $6\theta(1-\theta)$：中间高、两端低，表示更相信成功率接近中间值。

##### 共轭更新

**为什么常把它用作伯努利／二项模型的先验？因为更新后仍属于 Beta 分布。** 给定固定成功率 $\theta$，独立试验得到 $a$ 次成功、$b$ 次失败，其似然为：

$$
p(D\mid\theta)\propto\theta^a(1-\theta)^b
$$

按[贝叶斯公式](#贝叶斯公式先验似然与后验)，先验乘以似然，再归一化；这里相乘后指数相加：

$$
p(\theta\mid D)\propto
\underbrace{\theta^{\alpha-1}(1-\theta)^{\beta-1}}_{\text{先验}}
\underbrace{\theta^a(1-\theta)^b}_{\text{似然}}
=\theta^{\alpha+a-1}(1-\theta)^{\beta+b-1}
$$

$$
\theta\mid D\sim\operatorname{Beta}(\alpha+a,\beta+b)
$$

先验与后验属于同一个分布族，就叫**共轭**。成功数加到 $\alpha$，失败数加到 $\beta$；参数可以是正实数，不必解释为真实历史次数，尤其不能把小于 1 的参数解释成负次数。

##### 后验状态：均值、不确定性与充分统计量

相同均值不代表相同认识状态：

$$
\operatorname{Beta}(1,1)
\qquad\text{与}\qquad
\operatorname{Beta}(101,101).
$$

两者均值都是 0.5，前者在整个区间均匀分布，后者集中在 0.5 附近。只记录“候选成功率 50%”会丢失不确定性，无法判断继续采样还可能带来多大变化。

给定先验，在成功率固定、试验条件独立且同分布的 Bernoulli 模型中，后验只依赖成功数 a 与失败数 b；这两个计数是充分统计量。它们足以恢复后验、预测下一次结果，不必保存完整结果序列。实际研究系统仍需记录证据来源、候选版本和测试条件，才能检查这些建模假设是否成立；修改过的候选不能不加区分地累计进旧计数。

##### 后验预测：从全概率公式到成功率均值

**未知成功率下，下一次成功的概率，是对所有可能成功率按后验加权平均。** 给定固定 $\theta$，下一次试验与历史数据 $D$ 条件独立，且成功概率为 $\theta$。由全概率公式：

$$
\begin{aligned}
P(Y_{\mathrm{next}}=1\mid D)
&=\int_0^1 P(Y_{\mathrm{next}}=1\mid\theta,D)\,p(\theta\mid D)\,d\theta\\
&=\int_0^1\theta\,p(\theta\mid D)\,d\theta
=\mathbb E[\theta\mid D]
\end{aligned}
$$

采用一般先验 $\operatorname{Beta}(\alpha,\beta)$，其中 $\alpha,\beta>0$。观察到 $a$ 次成功、$b$ 次失败后，先把后验归一化：

$$
Z=\int_0^1 t^{a+\alpha-1}(1-t)^{b+\beta-1}\,dt,
\qquad
p(\theta\mid D)=\frac{\theta^{a+\alpha-1}(1-\theta)^{b+\beta-1}}{Z}
$$

$a,b,\alpha,\beta$ 固定后，$Z$ 是与 $\theta$ 无关的常数。期望按“取值乘以密度，再积分”计算，因此：

$$
\begin{aligned}
\mathbb E[\theta\mid D]
&=\int_0^1\theta\,\frac{\theta^{a+\alpha-1}(1-\theta)^{b+\beta-1}}{Z}\,d\theta\\
&=\frac{1}{Z}\int_0^1\theta^{a+\alpha}(1-\theta)^{b+\beta-1}\,d\theta\\
&=\frac{\int_0^1\theta^{a+\alpha}(1-\theta)^{b+\beta-1}\,d\theta}
{\int_0^1t^{a+\alpha-1}(1-t)^{b+\beta-1}\,dt}
\end{aligned}
$$

**分母来自密度归一化，分子多出的一个 $\theta$ 来自期望定义。** 积分变量 $t$ 只是局部占位符，换名不改变积分值。

把分子积分记为 $J$。为求 $J/Z$，取 $g(\theta)=\theta^{a+\alpha}(1-\theta)^{b+\beta}$；两项指数均为正，它在两端均为零，因此：

$$
\begin{aligned}
0=\int_0^1g'(\theta)\,d\theta
&=(a+\alpha)\int_0^1\theta^{a+\alpha-1}(1-\theta)^{b+\beta}\,d\theta-(b+\beta)J\\
&=(a+\alpha)(Z-J)-(b+\beta)J\\
&=(a+\alpha)Z-(a+b+\alpha+\beta)J
\end{aligned}
$$

第二行把积分中的一个 $(1-\theta)$ 展开为 $1-\theta$，于是该积分等于 $Z-J$。整理可得：

$$
\boxed{P(Y_{\mathrm{next}}=1\mid D)=\mathbb E[\theta\mid D]=\frac{J}{Z}=\frac{a+\alpha}{a+b+\alpha+\beta}}
$$

**均匀先验是 $\alpha=\beta=1$ 的特例。** 此时后验密度与 $\theta^a(1-\theta)^b$ 成正比，上面的推导化为：

$$
P(Y_{\mathrm{next}}=1\mid D)
=\frac{\int_0^1\theta^{a+1}(1-\theta)^b\,d\theta}{\int_0^1t^a(1-t)^b\,dt}
=\frac{a+1}{a+b+2}
$$

“+1、+2”来自 $\operatorname{Beta}(1,1)$ 先验。例如观察到一次成功后，后验为 $\operatorname{Beta}(2,1)$，下一次成功的预测概率为 $2/3$，而直接使用样本均值会得到 100%。这个先验避免了凭一个样本作出极端预测，但先验仍是建模选择，并不天然正确。

应用：Bernoulli bandit 的 **Thompson sampling** 为每个候选维护 Beta 后验，从各后验抽取一个成功率，再选择抽样值最大的候选，以分布表达不确定性并参与决策。

参考：[SciPy：Beta 分布定义](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html)；[Selecting Computations，§2 的 Bernoulli 模型与后验更新](https://aima.cs.berkeley.edu/~russell/papers/uai12-meta.pdf)。

### 抽样、集中与估计误差

这部分依次回答三个问题：取平均为什么会降低波动；怎样把“波动更小”变成有限样本下的概率保证；增加假设后，概率保证能收紧到什么程度。样本均值的方差给出波动尺度，集中不等式给出尾概率，大数定律和中心极限定理则描述渐近行为。

#### 样本均值的方差 (Variance of Sample Mean)

**核心结论**：样本均值 $\bar{Y}$ 的方差是总体方差 $\sigma^2$ 的 $1/N$。即：
$$Var(\bar{Y}) = \frac{\sigma^2}{N}$$

**直观理解**：
*   **平均作用抵消波动**：当你取平均值时，极大的数和极小的数会相互抵消，使得平均值 $\bar{Y}$ 比单个样本 $Y_i$ 更稳定（波动更小）。
*   **大数定律**：样本量 $N$ 越大，平均值越接近真实的总体均值，其波动范围（方差）就越小。如果 $N$ 无穷大，方差趋近于 0，均值就变成了一个确定值。

**推导过程**：
1.  **定义**：假设有 $N$ 个**独立同分布 (i.i.d)** 的随机变量 $Y_1, Y_2, ..., Y_N$，每个变量的方差都是 $\sigma^2$，即 $Var(Y_i) = \sigma^2$。
2.  **样本均值公式**：$\bar{Y} = \frac{1}{N} \sum_{i=1}^{N} Y_i = \frac{Y_1 + Y_2 + ... + Y_N}{N}$
3.  **计算方差**：
    $$
    \begin{aligned}
    Var(\bar{Y}) &= Var(\frac{1}{N} \sum_{i=1}^{N} Y_i) \\
    &= \frac{1}{N^2} Var(\sum_{i=1}^{N} Y_i) \quad \text{(常数提取性质: } Var(kX) = k^2 Var(X) \text{)} \\
    &= \frac{1}{N^2} \sum_{i=1}^{N} Var(Y_i) \quad \text{(独立性: 独立变量和的方差等于方差的和)} \\
    &= \frac{1}{N^2} \sum_{i=1}^{N} \sigma^2 \\
    &= \frac{1}{N^2} \cdot (N \cdot \sigma^2) \\
    &= \frac{\sigma^2}{N}
    \end{aligned}
    $$

上式解释样本均值的方差如何随 $N$ 缩小；大数定律说明 $\bar Y$ 在适当条件下收敛到 $E[Y]$；中心极限定理则说明标准化后的样本均值何时近似正态，是许多置信区间与检验的依据。三者回答的问题不同。

#### 集中不等式：从切比雪夫到霍夫丁

[切比雪夫不等式](https://en.wikipedia.org/wiki/Chebyshev%27s_inequality)和[霍夫丁不等式](https://en.wikipedia.org/wiki/Hoeffding%27s_inequality)都在回答同一个问题：随机变量偏离其期望超过阈值的概率有多大。二者不是简单的上下位关系，而是在不同信息条件下给出的尾概率上界。

| 不等式 | 使用的信息 | 对样本均值的尾界 | 衰减速度 |
| --- | --- | --- | --- |
| 切比雪夫 | 有限方差 | $\sigma^2/(N\epsilon^2)$ | 随阈值呈多项式衰减 |
| 霍夫丁 | 样本独立且取值有界 | $2\exp(-2N\epsilon^2)$，这里假设 $X_i\in[0,1]$ | 随样本量和阈值呈指数衰减 |

两者也有共同的证明思路：都把问题转成对非负随机变量应用 Markov 不等式。切比雪夫控制平方偏差 $(X-E[X])^2$；霍夫丁控制指数矩 $\exp(\{\lambda(X-E[X])\})$，再利用独立性分解乘积、利用有界性控制每一项。因此霍夫丁用了更多结构，也通常能给出更强的高置信度保证。

**切比雪夫不等式。** 对任意具有有限期望 $\mu$ 和有限方差 $\sigma^2$ 的随机变量 $X$，以及任意 $t>0$：

$$
P(|X-\mu|\ge t)\le \frac{\sigma^2}{t^2}
$$

令 $t=k\sigma$，可写为：

$$
P(|X-\mu|\ge k\sigma)\le \frac{1}{k^2},
\qquad
P(|X-\mu|<k\sigma)\ge 1-\frac{1}{k^2}
$$

它不要求总体服从正态分布，也不要求知道分布形状，只要求方差有限。例如：

- $k=2$：至少 $75\%$ 的概率落在 $\mu\pm2\sigma$ 内。
- $k=3$：至少约 $88.9\%$ 的概率落在 $\mu\pm3\sigma$ 内。
- $k=4$：至少 $93.75\%$ 的概率落在 $\mu\pm4\sigma$ 内。

若 $X_1,\ldots,X_N$ 独立同分布，$E[X_i]=\mu$、$Var(X_i)=\sigma^2$，则 $Var(\bar X)=\sigma^2/N$。把切比雪夫应用于样本均值，得到：

$$
P(|\bar X-\mu|\ge\epsilon)
\le \frac{\sigma^2}{N\epsilon^2}
$$

这直接给出弱大数定律：对固定 $\epsilon>0$，右侧随 $N\to\infty$ 趋于 0。但它只按 $1/N$ 衰减，通常比较宽松。

**霍夫丁不等式。** 若 $X_1,\ldots,X_N$ 相互独立，且 $X_i\in[a_i,b_i]$，则：

$$
P\left(\left|\sum_{i=1}^{N}(X_i-E[X_i])\right|\ge t\right)
\le
2\exp\left(-\frac{2t^2}{\sum_{i=1}^{N}(b_i-a_i)^2}\right)
$$

特别地，当 $X_i\in[0,1]$ 时：

$$
P(|\bar X-E[\bar X]|\ge\epsilon)
\le 2e^{-2N\epsilon^2}
$$

这是双侧形式，所以有系数 2；单侧形式没有该系数：

$$
P(E[\bar X]-\bar X\ge\epsilon)\le e^{-2N\epsilon^2}
$$

把允许的失败概率记为 $\delta$，两者给出的置信半径分别是：

$$
r_{\text{Chebyshev}}
=\frac{\sigma}{\sqrt{N\delta}},
\qquad
r_{\text{Hoeffding}}
=\sqrt{\frac{\log(2/\delta)}{2N}}
$$

两者都按 $1/\sqrt N$ 收缩，关键差别在置信度：切比雪夫随 $1/\sqrt\delta$ 增长，霍夫丁只随 $\sqrt{\log(1/\delta)}$ 增长。要求极低失败概率时，这个差距会很大。

在相同的独立有界样本上，两种不等式都能使用。霍夫丁的失败概率随 $N$ 指数下降，因此在高置信度场景通常比切比雪夫紧；但它要求独立和有界，而且没有利用真实方差可能很小的信息。只有有限方差或样本可能重尾时，切比雪夫仍然适用；存在依赖时，切比雪夫仍可用于目标统计量，但必须重新计算包含协方差的方差，不能继续套用 $Var(\bar X)=\sigma^2/N$。同时知道方差和取值范围时，Bernstein 或 empirical Bernstein 往往更合适。

#### 从 Hoeffding 到 UCB 置信上界

对一个奖励独立同分布、取值在 [0,1]、均值为 μ 的臂，先固定样本数 n。单侧 Hoeffding 控制“真实均值比样本均值高出 r”的概率。令其上界等于允许的失败概率 δ：

$$
P(\mu>\bar X_n+r)\le e^{-2nr^2},
\qquad
e^{-2nr^2}=\delta
\quad\Longrightarrow\quad
r=\sqrt{\frac{\ln(1/\delta)}{2n}}.
$$

所以置信上界是“样本均值 + 置信半径”。δ 越小，要求越有把握，半径越大；n 越大，均值估计越精确，半径越小。它控制重复采样下的覆盖错误，不是给固定未知参数 μ 指定贝叶斯后验概率。

UCB1 取随总轮数 t 下降的 δ_t=t⁻⁴（t≥2），于是：

$$
r_n(t)=\sqrt{\frac{\ln(t^4)}{2n}}
=\sqrt{\frac{2\ln t}{n}},
\qquad
P\left(\mu>\bar X_n+r_n(t)\right)\le t^{-4}.
$$

这说明公式中的 2 来自这组置信度选择，并非所有 UCB 都必须使用同一常数。t 是所有臂累计采样次数，n 是当前臂的采样次数；两者不能混用。

**固定样本数的界不等于自适应采样全过程的界。** Bandit 中当前臂的次数 N(t) 由之前的反馈决定，不能直接声称把随机 N(t) 代入后仍有 t⁻⁴ 的错误概率。可以先对所有可能的固定样本数做 union bound；对一个臂、固定总轮数 t：

$$
P\!\left(\exists n\le t:\mu>\bar X_n+r_n(t)\right)
\le\sum_{n=1}^{t}t^{-4}=t^{-3}.
$$

这个事件覆盖了实际选出的 N(t)；再覆盖多个臂、多个轮次还要继续控制并集。原 UCB1 证明分别控制最优臂被低估、次优臂被高估的事件，得到累计遗憾保证；不能把这里的固定 n 概率当成任意时刻都有效的同一置信度。

算法、探索项直觉与遗憾推导见 [UCB1](./Reinforcement-Learning.md#ucb1用置信上界平衡探索与利用)。来源：[Auer、Cesa-Bianchi、Fischer，2002，§2 / Theorem 1 与 §3 证明](https://homes.di.unimi.it/cesa-bianchi/Pubblicazioni/ml-02.pdf)。

### 从目标量到估计结果

先分清目标，再讨论计算方法：

| 层次 | 问题 | 例子 |
| --- | --- | --- |
| estimand（目标量） | 想知道哪个总体量？ | 总体均值、两组平均差、某类任务上的平均增量 |
| identification（可识别性） | 在哪些假设下，目标量能写成观测数据分布的函数？ | 随机抽样、随机分配、无遗漏选择等假设是否足够 |
| estimator（估计量） | 用样本按什么规则计算？ | 样本均值、均值差、回归、加权估计量 |
| estimate（估计值） | 这批数据算出的具体数字是什么？ | 本次实验观测到 `+2.1%` |

样本增加通常能降低 estimator 的随机波动，却不能自动修复目标定义错误、系统性选择偏差或不可识别。形式上，可以把误差分成偏差与方差：

$$
E[(\hat\theta-\theta)^2]
=\operatorname{Bias}(\hat\theta)^2+\operatorname{Var}(\hat\theta)
$$

更多数据主要压低方差；若数据采集和假设使 $\hat\theta$ 系统性偏离 $\theta$，结果会更稳定地错。

### 假设检验 (Hypothesis Testing)

用于判断样本观测结果是否支持某个假设（如 AB Test 中“新策略比旧策略好”），排除随机波动的干扰。

推断还要包含“方案、指标和停止时间怎样选出来”：同一批数据既负责选优又负责证明赢家，普通 P 值和置信区间可能失去原有保证，见 [选优后的统计推断](#选优后的统计推断赢家诅咒多重比较与提前停止)。A/B 中的落地流程见 [实验合同](./Software-Engineering.md#先写实验合同)。

#### 效应量与置信区间

假设检验回答“数据与某个原假设是否相容”，效应量回答“差异有多大”。决策时应同时报告点估计与置信区间，例如均值差 $\hat\Delta$ 及其区间，而不只报告是否跨过显著性阈值。

在给定抽样与分析程序成立时，95% 置信区间的频率学派含义是：重复抽样并用同一程序构造区间，长期约 95% 的区间覆盖真实目标量。它不是在看到数据后声称“参数有 95% 概率位于这个固定区间内”。区间很窄只说明随机误差小；若实验设计有偏，它仍可能精确地覆盖错误方向。

#### Z-score (标准分数)

*   **定义**：描述观测值距离总体均值有多少个标准差。用于衡量数据点在分布中的相对位置。
*   **公式**：$$z = \frac{\bar{x} - \mu}{\sigma / \sqrt{n}}$$
    *   $$\bar{x}$$: 样本均值
    *   $$\mu$$: 总体均值（或原假设下的均值，如 0）
    *   $$\sigma$$: 总体标准差
    *   $$n$$: 样本量
*   **解读**：
    *   $$z > 0$$: 高于均值；$$z < 0$$: 低于均值。
    *   $$|z|$$ 越大，偏离均值越远，发生该事件的概率越低（在 $$H_0$$ 成立时）。

#### P-value (P值)

*   **定义**：在**原假设 ($$H_0$$) 成立**的前提下，观察到当前样本统计量（或更极端情况）的概率。
*   **解读**：
    *   P 值是**反对原假设的证据强度**。P 值越小，拒绝 $$H_0$$ 的理由越充分（结果越显著）。
    *   P 值不是 $P(H_0\mid data)$，也不是“结果由随机性造成的概率”。它是在 $H_0$ 与检验程序成立时，当前统计量或更极端统计量出现的概率。
    *   统计显著不等于效果大或值得上线；样本足够大时，业务上可忽略的差异也可能显著。反之，不显著也不等于证明两组相同，可能只是区间过宽。
    *   通常设定显著性水平 $$\alpha$$ (如 0.05)：
        *   $$P < 0.05$$：**统计显著 (Significant)**，拒绝 $$H_0$$（认为差异真实存在）。
        *   $$P \ge 0.05$$：**不显著 (Not Significant)**，不能拒绝 $$H_0$$（可能是真的没区别，也可能是样本量太小，Power 不足）。
*   **Z-score 与 P-value 的关系** (在正态分布下)：
    *   $$|z| = 1.96 \Rightarrow P = 0.05$$ (双尾)
    *   $$|z| = 2.58 \Rightarrow P = 0.01$$ (双尾)
    *   $$|z| > 1.96$$ 即意味着 $$P < 0.05$$。

#### 单样本检验 (One-Sample Testing)

*   **定义**：检验单个样本的均值 $\bar{X}$ 是否显著不同于一个预设的已知值 $\mu_0$。
*   **统计量 (t-test)**: $t = \frac{\bar{X} - \mu_0}{s / \sqrt{n}}$
*   **关于时间维度 (Time Dimension)**:
    *   **通常情况**：单样本检验是**横截面**的（比较当前样本 vs 标准值）。
    *   **特殊情况 (配对检验)**：当进行“前后对比”（Pre-Post Analysis）时，我们会计算差值 $D_i = X_{after} - X_{before}$。对差值序列 $D$ 做**单样本检验**（检验均值是否为0），本质上就是**配对样本 t 检验 (Paired Sample t-test)**。这是单样本检验处理时间维度最常见的方式。
    *   **注意**：如果是长周期的**时间序列数据**（如股票价格），由于存在自相关性（Autocorrelation），不能直接使用简单的单样本检验，需使用时间序列模型。

#### 双样本检验 (Two-Sample Testing)

*   **Welch's t-test (韦尔奇 t 检验)**
    *   **适用场景**：比较两个独立样本的均值是否相等。**不需要**假设两个总体的方差相等（即具有异方差性），也不要求样本量相等。比 Student's t-test 更通用且稳健。
    *   **统计量**:
        $$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{N_1} + \frac{s_2^2}{N_2}}}$$
        *   $\bar{X}_i, s_i^2, N_i$: 第 $i$ 组的样本均值、样本方差、样本量。
    *   **自由度 (df)**: 计算较复杂（Welch–Satterthwaite equation），通常非整数。

#### 选优后的统计推断：赢家诅咒、多重比较与提前停止

> 参考：[Cawley & Talbot：模型选择中的过拟合与评估选择偏差](https://www.jmlr.org/papers/v11/cawley10a.html)、[Johari 等：Always Valid Inference for A/B Testing](https://arxiv.org/abs/1512.04922v3)；Harness 案例见 [HDA significance gate](https://github.com/Wenwen-D/HarnessDeltaAttribution/blob/9a382fdae83bed7489d368127397d3418ed02677/src/hda/HDA_SKILL.md#step-2--significance-gate)。

**赢家诅咒（winner's curse）**：从很多方案里挑观测收益最高者，也更容易挑中正向噪声。每个方案单独估计无偏，不保证挑出的赢家仍无偏。记第 j 个方案的真实收益为 Δ_j、估计误差为 ε_j：

$$
\widehat{\Delta}_j=\Delta_j+\varepsilon_j,\qquad J=\arg\max_{1\le j\le m}\widehat{\Delta}_j
$$

简化到所有方案真实收益相同、m>1，误差独立同分布、非退化且均值为零时：

$$
\mathbb{E}[\widehat{\Delta}_J-\Delta]=\mathbb{E}[\max_j\varepsilon_j]>0
$$

因此“先在同一集合选优，再对赢家做普通显著性检验”会高估证据强度：普通检验把方案当成事先固定，忽略了先前搜索。只对已选中的方案做 paired bootstrap，也不会自动把搜索与选择过程纳入不确定性。即使没有硬编码答案，反复根据总分调模型、prompt 或 harness，也能过拟合选型集。

| 问题 | 数据驱动的选择 | 需要处理什么 |
| --- | --- | --- |
| 赢家诅咒 / 选择后推断 | 选提升最大的方案，再报其提升和区间 | 赢家效果通常被高估；用独立确认数据估计，或使用明确考虑选择过程的推断方法 |
| 多重比较 | 测多个版本、指标或人群，只报显著项 | 控制整组检验的错误率；预定义检验族，按目标使用 Holm / Bonferroni 等方法；校正 P 值不自动消除赢家点估计的偏差 |
| 反复查看并提前停止（optional stopping） | 每天看普通 P 值，一显著就停 | 停止规则也在利用噪声；固定预先约定的样本量 / 分析时间，或使用适配的序贯检验、always-valid 推断 |

多重比较的直观例子：若 m 个原假设都成立、检验相互独立且每次误报率为 α，则：

$$
P(\text{至少一次误报})=1-(1-\alpha)^m;\qquad m=20,\ \alpha=0.05\Rightarrow 64.2\%
$$

这是“整组至少一次误报”的概率，不是“某个赢家为假的概率”；共享对照组或相关指标下也不能直接套独立公式。

最直接的处理是：**用开发／验证集选择方案，冻结后再用未参与选择的测试集评估。** 冻结应覆盖方案、主要指标、分析和停止规则；划分按独立采样单位处理相关性与泄漏。若继续根据测试反馈修改方案，该集合也进入优化循环，需要新的独立测试，或明确考虑完整选择过程的方法。样本有限时，nested cross-validation 可让外层评估内层的选型流程；不能再根据外层成绩挑方案而仍把它当作未参与选择的证据。

多重比较、选择后估计和序贯监测是不同维度，可能同时存在；调整其中一个不自动解决其余问题。单纯多做几次 bootstrap、降低某次 P 值或随意加宽区间，都不能替代正确的实验设计。工程操作见 [A/B Testing](./Software-Engineering.md#ab-testing)，模型外围代码搜索的实例见 [Harness-Delta Attribution](./AI-Applied-Algorithms.md#harness-delta-attribution涨分后追问靠什么涨的)。

#### 集成检验与元分析 (Ensemble Testing & Meta-Analysis)

用于将多个独立的微小实验结果聚合，解决单次实验样本不足导致统计效力（Power）低下的问题。

*   **符号检验 (Sign Test)**
    *   **原理**：一种非参数检验方法。将每个实验看作一次伯努利试验（Bernoulli Trial）。
    *   **假设**：
        *   $H_0$: 新策略无正向效果，即单个实验正向的概率 $P(Lift > 0) = 0.5$。
        *   $H_1$: 新策略有正向效果，即 $P(Lift > 0) > 0.5$。
    *   **统计量**：$N$ 个实验中正向结果的个数 $k$。服从二项分布 $k \sim B(N, 0.5)$。
    *   **P值计算**：$P(X \ge k) = \sum_{i=k}^{N} \binom{N}{i} 0.5^N$。

*   **固定效应模型 (Fixed Effect Model)**
    *   **原理**：假设所有实验都在测量同一个真实的总体效应值 $\theta$（True Effect Size），观测值的差异仅源于抽样误差。
    *   **逆方差加权 (Inverse-Variance Weighting)**：
        *   为了获得最小方差无偏估计 (MVUE)，权重应与方差成反比。
        *   权重 $w_i = \frac{1}{Var(\hat{\theta}_i)} \approx \frac{1}{\sigma_i^2}$。
    *   **聚合公式**：
        *   全局效应估计：$\hat{\theta}_{global} = \frac{\sum w_i \hat{\theta}_i}{\sum w_i}$
        *   全局标准误：$SE(\hat{\theta}_{global}) = \frac{1}{\sqrt{\sum w_i}}$
        *   全局 Z-score：$Z = \frac{\hat{\theta}_{global}}{SE(\hat{\theta}_{global})}$

### 比率指标的方差估计 (Variance Estimation for Ratios)

#### Delta Method (Delta 方法)

*   **背景**：在 AB 实验中，很多核心指标是比率形式（Ratio Metric），如 $CTR = \frac{\sum Clicks}{\sum Views}$。若定义 $Y$ 为分子（如 Clicks），$X$ 为分母（如 Views），则指标估计量为 $\hat{R} = \frac{\bar{Y}}{\bar{X}}$。
*   **核心思想**：利用泰勒展开（Taylor Expansion）将非线性函数近似为线性函数，从而估算其方差。
*   **方差公式**:
    *   **通用形式** (针对任意随机变量的商 $Y/X$):
        $$Var(\frac{Y}{X}) \approx \frac{1}{\mu_X^2} Var(Y) + \frac{\mu_Y^2}{\mu_X^4} Var(X) - 2 \frac{\mu_Y}{\mu_X^3} Cov(X, Y)$$
    *   **样本均值形式** (常用工程公式):
        $$Var(CTR) \approx \frac{1}{N} \cdot \frac{1}{\mu_x^2} (\sigma_y^2 - 2R\sigma_{xy} + R^2\sigma_x^2)$$
        *   **公式关系**: 这是通用公式在**样本均值**上的具体应用。
        *   **推导逻辑**: 
            1.  将 $Var(\bar{Y}) = \frac{\sigma_y^2}{N}, Var(\bar{X}) = \frac{\sigma_x^2}{N}, Cov(\bar{Y}, \bar{X}) = \frac{\sigma_{xy}}{N}$ 代入通用公式。
            2.  提取公因式 $\frac{1}{N}$ 得到该式。
        *   **符号含义**:
            *   $N$: 样本量 (Sample Size)。
            *   $\sigma_y^2, \sigma_x^2, \sigma_{xy}$: **个体层面 (User-level)** 数据的方差和协方差。
            *   $R$: 总体比率真值 ($\mu_y / \mu_x$)。
*   **应用**：计算 CTR、CVR 等比率指标的置信区间和显著性检验。

### 方差缩减 (Variance Reduction)

#### CUPED (Controlled-experiment Using Pre-Experiment Data)

*   **背景**：在 AB 实验中，指标的方差越大，检测显著性所需的样本量就越大（Sensitivity 越低）。CUPED 是一种利用实验前数据（Pre-experiment Data）来降低指标方差的技术。
*   **核心思想**：利用实验前数据 $X$（Covariate）与实验期间指标 $Y$ 的相关性，移除 $Y$ 中可以被 $X$ 解释的方差部分。
*   **修正公式**：
    $$Y_{cuped} = Y - \theta (X - E[X])$$
    *   $Y$: 实验期间的观测指标（如实验周的人均时长）。
    *   $X$: 实验前的协变量（如实验前一周的人均时长）。$X$ 必须不受实验干预影响（通常取实验前数据）。
    *   $E[X]$: 协变量的总体均值（通常用所有样本的均值估计）。
    *   $\theta$: 调节系数。
*   **最优 $\theta$ 与方差缩减**：
    *   使 $Var(Y_{cuped})$ 最小的 $\theta$ 为：
        $$\theta^* = \frac{Cov(Y, X)}{Var(X)}$$
    *   修正后的方差为：
        $$Var(Y_{cuped}) = Var(Y) (1 - \rho^2)$$
    *   其中 $\rho$ 是 $Y$ 和 $X$ 的相关系数。相关性越高，方差缩减效果越好。
*   **性质**：
    *   **无偏性**：$E[Y_{cuped}] = E[Y]$，即修正后的指标均值期望不变（假设 $E[X]$ 估计准确）。
    *   **独立性**：协变量 $X$ 的选择必须独立于实验干预（Pre-experiment data 天然满足）。

### 聚类 & 相似度

* Silhouette coefficient（轮廓系数）是一种用于评估聚类效果的指标，它综合考虑了聚类的紧密性和分离性，能有效衡量一个样本与其所属聚类以及相邻聚类之间的关系，其具体信息如下：
  * **定义与计算方式**    - 对于样本 $$i$$，设 $$a(i)$$ 为样本 $$i$$ 到其所属聚类 $$C$$ 中其他样本的平均距离，反映了样本在其所属聚类内的紧密程度。计算方式为 $$a(i)=\frac{1}{|C|-1}\sum_{j\in C,j\neq i}d(i,j)$$，其中 $$d(i,j)$$ 是样本 $$i$$ 和 $$j$$ 之间的距离度量（如欧几里得距离），$$|C|$$ 是聚类 $$C$$ 中的样本数量。    - 设 $$b(i)$$ 为样本 $$i$$ 到与其相邻最近聚类 $$C'$$ 中所有样本的平均距离，衡量了样本与其他聚类的分离程度。通过计算样本 $$i$$ 到所有其他聚类的平均距离，并取最小值作为 $$b(i)$$。    - 样本 $$i$$ 的轮廓系数 $$s(i)$$ 计算公式为 $$s(i)=\frac{b(i)-a(i)}{\max\{a(i),b(i)\}}$$，其取值范围在 $$[-1,1]$$ 之间。_
  * _ - **取值意义**    - 当 $$s(i)$$ 接近 1 时，表示样本 $$i$$ 与所属聚类内的样本距离较近，且与相邻聚类的样本距离较远，说明聚类效果较好，样本被合理地划分到了当前聚类中。    - 当 $$s(i)$$ 接近 0 时，表明样本 $$i$$ 处于两个聚类的边界附近，其所属聚类可能不太明确，聚类效果有待提高。    - 当 $$s(i)$$ 接近 -1 时，意味着样本 $$i$$ 可能被错误地划分到了当前聚类，它与相邻聚类的样本更为相似，聚类效果较差。 
  * - **整体评估**：通常会计算数据集中所有样本的轮廓系数，并取平均值作为整个数据集的轮廓系数。该平均值越高，说明聚类的整体质量越好；反之，则表示聚类效果不佳，可能需要调整聚类算法的参数或尝试其他聚类方法。例如，在一个包含 $$n$$ 个样本的数据集上，整体轮廓系数 $$S=\frac{1}{n}\sum_{i = 1}^{n}s(i)$$。 

* [Jaccard相似度](https://zh.wikipedia.org/wiki/%E9%9B%85%E5%8D%A1%E5%B0%94%E6%8C%87%E6%95%B0)：是用于比较[样本](https://zh.wikipedia.org/wiki/样本)集的相似性与[多样性](https://zh.wikipedia.org/wiki/多样性指数)的统计量，雅卡尔系数能够量度有限样本集合的相似度，其定义为两个集合[交集](https://zh.wikipedia.org/wiki/交集)大小与[并集](https://zh.wikipedia.org/wiki/并集)大小之间的比例
  * 文本相似度
#### KL散度
*   **定义**: $D_{KL}(P||Q) = \sum_x P(x) \log \frac{P(x)}{Q(x)}$
*   **解读**: 衡量用分布 Q 近似真实分布 P 时的信息损失。也称相对熵 (Relative Entropy)。
  * 有向的度量
*   **性质**: 非负性 $D_{KL}(P||Q) \ge 0$ (吉布斯不等式)，仅当 P=Q 时取0。不具有对称性，即 $D_{KL}(P||Q) \neq D_{KL}(Q||P)$。


## 信息论 (Information Theory)

### 熵 (Entropy)

信息熵是度量随机变量不确定性的指标。变量熵值越大，不确定性越高，包含信息量越大。

熵没有计入行动与效用。消除同样多的不确定性，对最终选择的帮助可以不同，见[信息量与决策价值](./Reinforcement-Learning.md#信息量与决策价值)。

#### 定义

对于离散随机变量 $X$，取值集合 $\{x_1,x_2,...,x_n\}$，概率分布 $P(X=x_i)=p_i$，信息熵定义为：

$
H(X) = - \sum_{i=1}^{n} p_i \log_b(p_i)
$

* 当 $p_i=0$ 时，约定 $0 \log 0 = 0$
* 对数底 $b$ 取2时单位为比特(bit)，取自然对数时为奈特(nat)

本质是**事件信息量的数学期望**，单个事件信息量为 $-\log(p_i)$，概率越小信息量越大。

#### 核心性质

* **非负性**：$H(X) \ge 0$，仅当变量为确定值时取等号
* **对称性**：熵值仅与概率分布相关，与变量具体取值无关
* **可加性**：独立变量联合熵等于各自熵之和 $H(X,Y)=H(X)+H(Y)$

#### 最大熵 (Maximum Entropy)

**结论**：$n$ 个取值的离散变量，当且仅当服从均匀分布 $p_i=1/n$ 时熵最大，最大值为：$
H_{\text{max}}(X) = \log(n)
$

**证明**（使用KL散度）：
设 $p$ 为任意分布，$u$ 为均匀分布。由 $D_{KL}(p||u) \ge 0$ 可得：

$
\sum p_i \log p_i \ge \sum p_i \log(1/n) \implies -H(X) \ge -\log(n) \implies H(X) \le \log(n)
$

等号仅在 $p=u$ 时成立。

#### 交叉熵 (Cross-Entropy)

*   **定义**: $H(P, Q) = -\sum_x P(x) \log Q(x)$
*   **解读**: 在机器学习中，P 通常为真实标签的 one-hot 分布，Q 为模型预测的概率分布。交叉熵损失函数衡量了模型预测与真实的差异。
*   **关系**: $H(P, Q) = H(P) + D_{KL}(P||Q)$。当真实分布 P (即熵 H(P)) 固定时，最小化交叉熵等价于最小化 KL 散度。

## 博弈论

### 博弈论与机器学习

* Milgrom, Paul R., and Steven Tadelis.How artificial intelligence and machine learning can impact market design. No. w24282. National Bureau of Economic Research, 2018.
* https://cloud.tencent.com/developer/article/1530214



## A Course in Game Theory - Martin J. Osborne and Ariel Rubinstein

![image-20240720183436637](./Mathematics/game-theory-structure-1506147.png)

### Chpt 1: Introduction

* Game Theory

  * The basic assumptions that underlie the theory are that decision-makers pursue well-defined exogenous objectives (they are **rational**) and take into account their knowledge or expectations of other decision-makers’ behavior (they **reason strategically**).
  * 对现实的指导
    * the theory of Nash equilibrium (Chapter 2) has been used to study oligopolistic and politi- cal competition. 
    * The theory of mixed strategy equilibrium (Chapter 3) has been used to explain the distributions of tongue length in bees and tube length in flowers. 
    * The theory of repeated games (Chapter 8) has been used to illuminate social phenomena like threats and promises. 
    * The theory of the core (Chapter 13) reveals a sense in which the outcome of trading under a price system is stable in an economy that contains many agents.

* Games and Solutions

  * Noncooperative and Cooperative Games
    * Noncooperative：Part 1、2、3； Cooperative：Part 4
  * Strategic Games and Extensive Games
    * 1； 2、3
  * Games with Perfect and Imperfect Information
    * 2；3

* Game Theory and the Theory of Competitive Equilibrium

  * competitive reasoning（经济学中的概念）只关注外部环境变量来做决策，不关注其他agent的决策

* Rational Behavior

  * A set A of actions from which the decision-maker makes a choice.
  * A set C of possible consequences of these actions.
  * A consequence function g:A → C that associates a consequence with each action.
    *  if the consequence function is **stochastic** and known to the decision-maker
      * **maximizes the expected value**
    * If not known: 引入状态空间，he is assumed to choose an action a that maximizes the expected value of **u(g(a,ω))**
  * A preference relation (a complete transitive reflexive binary relation) 􏰵 on the set C.
    * utility function

* The Steady State and Deductive Interpretations

  * **The Steady State** treats a game as a model designed to explain some regularity observed in a family of similar situations.
    * Each participant “knows” the equilibrium and tests the optimality of his behavior given this knowledge, which he has acquired from his long experience.
  * **Deductive Interpretations** treats a game in isolation, as **a “one-shot” event**, and attempts to infer the restrictions that rationality imposes on the out- come; it assumes that each player deduces how the other players will behave **simply from principles of rationality**

* Bounded Rationality

  * asymmetry between individuals in their abilities
  * Modeling asymmetries in abilities and in perceptions of a situation by different players is a fascinating challenge for future research

* Terminology and Notation

  *  increasing、nondecreasing function

  * concave

  * arg maxx∈X f (x) the set of maximizers of f

  * Throughout we use N to denote the set of players. We refer to a collection of values of some variable, one for each player, as a profile       (xi)

    * ![image-20240720191434381](./Mathematics/game-theory-xi-1506147.png)

  * A binary relation on set的可能的性质: complete、reflexive、transitive

    * **A preference relation is a complete reflexive transitive binary relation.**

  * A preference relation的性质

    * 连续性：序列收敛

    * quasi-concave

      * ![image-20240720191747144](./Mathematics/game-theory-quasi-concave-1506147.png)

      * 在某条线上的点的连续性
      * https://en.wikipedia.org/wiki/Quasiconvex_function
      * ![image-20240720192146282](./Mathematics/quasi-convex-1506147.png)

  *  Pareto efficient 和 strongly Pareto efficient 
    *  Pareto efficient：没被碾压
    * strongly Pareto efficient ：没人有任何方面对我有优势
  * **A probability measure μ** on a finite (or countable) set X is an additive function that associates a nonnegative real number with every subset of X

### Part I: Strategic Games

* strategic game = game in normal form
  * This model specifies for each player a set of possible actions and a preference ordering over the set of possible action profiles.

### Chpt 2: Nash Equilibrium

* Strategic Games
  * A strategic game is a model of interactive decision-making in which each decision-maker chooses his plan of action **once and for all,** and these **choices are made simultaneously**
  * ![image-20240720225501522](./Mathematics/game-theory-strategic-game-1506147.png)
  * finite/非有限
  * 分析：
    * the range of application of the model is limited by the requirement that we associate with each player a preference relation
    * 限定过于宽松，难以得出重大结论
    * a player can form his expectation of the other players’ behavior
      * A sequence of plays of the game can be modeled by a strategic game **only if there are no strategic links between the plays.**
      * The model of a repeated game discussed in Chapter 8 deals with series of strategic interactions in which such intertemporal links do exist.
  * 拓展：
    * To do so we introduce **a set C of consequences**, a function g:A → C that associates consequences with action profiles, and a profile (􏰵∗i ) of preference rela- tions over C.
    * a function g: A × Ω → C with the interpretation that g(a, ω) is the consequence when the action profile is a ∈ A and the realization of the random variable is ω ∈ Ω
      * 引入之后，**the lottery over C induced by g(a,·) is at least as good** according ...，似乎更严格了
  * payoff function
    * denote：⟨N, (Ai), (ui)⟩
    * 2 player时的矩阵表示：the convention is that the row player is player 1 and the column player is player 2

* Nash Equilibrium
  * ![image-20240721000029501](./Mathematics/game-theory-nash-equil-1506147.png)
  * 分析：
    * This notion captures a steady state of the play of a strategic game in which each player holds the correct expectation about the other players’ behavior and acts rationally.
    * It does not attempt to examine the process by which a steady state is reached.
  * ![image-20240721000209969](./Mathematics/game-theory-nash2-1506147.png)
  * 延伸：一种可能的求解纳什均衡的方式，N个best-response function(如果是单值)

* Examples

  * Example 15.3 (Bach or Stravinsky? (BoS))

    * 元素1在列中最大、元素2在行中最大

  * 囚徒困境

  * 鹰鸽博弈

    * 是一种Symmetric games，但只存在 asymmetric equilibria

  * Matching Pennies

    * Such a game, in which the interests of the players are diametrically opposed, is called **“strictly competitive”**. The game Matching Pennies has no Nash equilibrium.

  * Exercise 18.2 first-price auction

    * 注意lowest index的约束

  * **in a second price auction** the bid vi of any player i is a **weakly dominant action**

    * An equilibrium in which player j obtains the good is that in which b1 < vj, bj > v1, and

      bi = 0 for all players i ∈/ {1,j}.

  *  Example 18.4 (A war of attrition)

  * Example 18.6 (A location game)

    * There is no equilibrium in which all three players become candidates

* Note：

  * Every SNE is weakly Pareto-efficient https://en.wikipedia.org/wiki/Strong_Nash_equilibrium

* Existence of a Nash Equilibrium

  * 表述为 a∗ ∈ B(a∗)
  * Lemma 20.1 (Kakutani’s fixed point theorem角谷静夫不动点定理)
  * ![image-20240721011951283](./Mathematics/game-theory-kakutani-1506147.png)

  * ![image-20240721013351172](./Mathematics/game-theory-nash-existence-1506147.png)
    * 注意不适用于有限actions集合的情况

* Strictly Competitive Games

  * 定义strictly competitive

  * for a strictly competitive game that possesses a Nash equilibrium, a pair of actions is a Nash equilibrium if and only if the action of each player is a maxminimizer

  * for strictly competitive games that possess Nash equilibria all equilibria yield the same payoffs.

  * ![image-20240721020542300](./Mathematics/game-theory-strictly-1506147.png)

    * part c提供一种场景的解法
    * by parts (a) and (c), **the Nash equilibria of a strictly competitive game are interchangeable**: if (x, y) and (x′, y′) are equilibria then so are (x, y′) and (x′, y).
    * Thus in any game (whether or not it is strictly competitive) the payoff that player 1 can guarantee herself is at most the amount that player 2 can hold her down to
      * ![image-20240721022026163](./Mathematics/image-20240721022026163-1506147.png)
      * 需要额外条件来确保存在纳什均衡

    * Part b: this payoff, the equilibrium payoff of player 1, is **the value of the game**
    * strictly competitive game中，增加payoff一定不会让value有损失；减少操作空间只可能让value有损失

* Bayesian Games: Strategic Games with Imperfect Information

  * 定义：Definition 25.1 A Bayesian game
    * We model the players’ uncertainty about each other by introducing a set Ω of possible “states of nature”, each of which is a description of all the players’ relevant characteristics. For convenience we assume that Ω is finite. Each player i has a prior belief about the state of nature given by a probability measure pi on Ω.
    * signal functions
    * 先验信号 ![image-20240721050519922](./Mathematics/image-20240721050519922-1506147.png)
  * 分析：
    * player has imperfect information about the state of nature
  * 用处：
    * a state of nature is a profile of parameters of the players’ preferences (for example, profiles of their valuations of an ob- ject)
    * player is uncertain about what the others know.（section 2.6.3
  * bayesian game的纳什均衡
    * ![image-20240721051935708](./Mathematics/image-20240721051935708-1506147.png)
  * Exercise 28.1 (An exchange game）
    * in any Nash equilibrium the highest prize that either player is willing to exchange is the smallest possible prize.
  * 贝叶斯纳什均衡的习题例子：https://www.cnblogs.com/haohai9309/p/17753112.html
  * A Bayesian game can be used to model not only situations in which each player is uncertain about the other players’ payoffs, as in Exam- ple 27.1, but also situations in which each player is **uncertain about the other players’ knowledge.**
    * we can let Ω = Θ × (×i∈N Xi) be the state space and use the model of a Bayesian game to capture any situation in which players are uncertain not only about each other’s payoffs but also about each other’s beliefs.

### Chpt 3: Mixed, Correlated, and Evolutionary Equilibrium

* Mixed Strategy Nash Equilibrium



### Intro

* Game theory provides a framework based on the construction of rigorous models that describe situations of conflict and cooperation between *rational* decision makers.
* 大家有没有比较推荐的博弈论的书？ - 子不语D的回答 - 知乎
  https://www.zhihu.com/question/446554214/answer/1751901215
* 学习博弈论，从入门、进阶到精通，如何列书单？ - 食其的回答 - 知乎
  https://www.zhihu.com/question/20266302/answer/76445562

## ML Theory

* 神经网络的万能逼近公式
  * ![image-20250408202259016](./Mathematics/image-20250408202259016-1506147.png)（来源LHUC paper)
  * ![image-20251004022110555](./Mathematics/image-20251004022110555-1506147.png)
    * 每条边代表一个参数
  
* 神经网络扰动
  * [Hessian-based Analysis of Large Batch Training and Robustness to Adversaries](https://arxiv.org/pdf/1802.08241) 分析了Hessian特征值和神经网络扰动的关系
    * Q-Bert 计算最大特征值：通过两次反向传播计算Hv，[幂迭代法 Power Iteration](https://en.wikipedia.org/wiki/Power_iteration)
    * [Training Deep and Recurrent Networks with Hessian-Free Optimization](https://www.cs.toronto.edu/~jmartens/docs/HF_book_chapter.pdf) 完整综述
  * 应用：量化分析，Q-Bert
* 2024 诺贝尔物理学奖授予人工神经网络机器学习，为什么会颁给 AI 领域？ - SIY.Z的回答 - 知乎
  https://www.zhihu.com/question/777943030/answer/4508673022
  * RBM 受限玻尔兹曼机
  * sigmoid 函数有了自然的解释：玻尔兹曼分布下隐含层神经元激活的条件概率的激活函数。
* 大模型是不是能够稀疏化? 
  * 从物理和能量密度/信息密度的角度来看, 似乎是可以的. 
  * 但是从范畴论的角度, 特别是预层范畴的角度来看待,Dense的Foundation Model训练是必须要做的, 因为只有在相对Dense的模型结构上才能更好的捕获所有的态射. 

* TOPOS理论 在ML的应用
  * on the diagram of thought https://github.com/diagram-of-thought/diagram-of-thought



## ML Application —— Exercises in Machine Learning

https://arxiv.org/pdf/2206.13446

### Backpropagating计算

https://web.eecs.umich.edu/~justincj/teaching/eecs442/notes/linear-backprop.html

![image-20250331145615951](./Mathematics/image-20250331145615951-1506147.png)




好的，这是一个非常深刻的问题。要从数学上理解 VQ-VAE 中的 "variational"，我们必须先回到它的“父辈”——标准的 VAE（Variational Autoencoder），理解 "variational" 在那里意味着什么，然后再看 VQ-VAE 是如何继承、修改和“绕过”这个概念的。

### 解构 VQ-VAE：一个关于变分贝叶斯方法应用的特例

#### Part 1: 标准 VAE 中的 "Variational" 是什么？

一个标准的生成模型的目标是学习数据的真实分布 `p(x)`。我们通常引入一个隐变量 `z` 来实现这一点，假设数据 `x` 是由 `z` 生成的。我们希望最大化数据的边际似然 `p(x)`：

`p(x) = ∫ p(x|z) p(z) dz`

- `p(z)` 是先验分布，通常我们假设它是一个简单的分布，比如标准正态分布 `N(0, I)`。
- `p(x|z)` 是由解码器（Decoder）建模的似然，表示给定一个隐变量 `z`，生成数据 `x` 的概率。

这个积分通常是**无法直接计算的 (intractable)**，因为它需要在整个隐空间上进行积分。

**Variational Inference (变分推断) 的登场**:
既然无法直接优化 `p(x)`，我们就需要一个近似的方法。变分推断的核心思想是：我们引入一个**近似的后验分布 `q(z|x)`** 来模拟真实的、但无法计算的后验分布 `p(z|x)`。

- `p(z|x)`: 真实的后验。给定一个数据点 `x`，它对应的隐变量 `z` 的真实分布是怎样的？这个我们算不出来，因为它依赖于 `p(x)`。
- `q_φ(z|x)`: 近似的后验。我们用一个简单的、可参数化的分布（例如高斯分布）来近似它。编码器（Encoder）的工作就是学习这个分布的参数 `φ`（例如，给定 `x`，输出对应的高斯分布的均值 `μ` 和方差 `σ²`）。

我们的目标是让 `q_φ(z|x)` 尽可能地接近 `p(z|x)`。衡量两个分布之间距离的工具是 **KL 散度**。我们希望最小化 `KL(q_φ(z|x) || p(z|x))`。

经过一系列数学推导（这是变分推断的核心），可以证明，最小化这个 KL 散度等价于**最大化证据下界 (Evidence Lower Bound, ELBO)**：

`log p(x) ≥ L_ELBO = E_{z~q_φ(z|x)}[log p_θ(x|z)] - KL(q_φ(z|x) || p(z))`

这个 ELBO 就是 VAE 的损失函数（取负号后最小化）：
1.  **`E_{z~q_φ(z|x)}[log p_θ(x|z)]`**: **重构项 (Reconstruction Term)**。从编码器得到的分布 `q_φ` 中采样一个 `z`，然后让解码器 `p_θ` 尽力去重构出原始的 `x`。
    * 理解`p_θ` ：模型的参数化
2.  **`KL(q_φ(z|x) || p(z))`**: **正则化项 (Regularization Term)**。它是一个 KL 散度，惩罚近似后验 `q_φ` 与先验 `p(z)` 之间的差异。这迫使编码器产生的隐空间结构化，使其接近于一个标准正态分布，从而使得我们可以在生成新样本时方便地从 `N(0, I)` 中采样。

**小结**：标准 VAE 的 "Variational" 来自于**变分推断**，即使用一个参数化的分布 `q_φ(z|x)` 去近似真实的后验 `p(z|x)`，并通过最大化 ELBO 来同时优化模型的重构能力和隐空间的结构。

#### Part 2: VQ-VAE 如何“打破”了这个框架？

VQ-VAE 的核心创新是引入了一个**离散的**隐空间，通过一个码本（Codebook）`E = {e_1, e_2, ..., e_K}` 来实现。

其过程如下：
1.  编码器 `Encoder(x)` 输出一个连续的向量 `z_e(x)`。
2.  通过**最近邻查找**，找到码本 `E` 中与 `z_e(x)` 最接近的码本向量 `e_k`。
3.  将这个被**量化 (Quantized)** 的向量 `e_k` 送入解码器 `Decoder(e_k)` 来重构 `x`。

这里的关键在于第二步的“最近邻查找”：`k = argmin_j ||z_e(x) - e_j||²`。这个 `argmin` 操作是**不可微分的**。

这导致了标准 VAE 框架的两个关键部分失效了：
1.  **无法重参数化采样**: 我们不能再从一个连续的分布 `q_φ(z|x)` 中平滑地采样。选择是“硬性”的，要么是 `e_1`，要么是 `e_2`，没有中间状态。
2.  **KL 散度项消失**: 标准的 `KL(q_φ(z|x) || p(z))` 公式是为连续分布（如高斯分布）设计的，现在隐空间是离散的，这个公式不再适用。

那么，如果 VAE 的核心数学工具 ELBO 看起来被打破了，为什么它还叫 VQ-**VAE** 呢？

#### Part 3: 数学上，VQ-VAE 的 "Variational" 在哪里？

这是最精妙的部分。VQ-VAE 的作者在论文中给出了一个数学解释，将它重新纳入了变分推断的框架，但形式非常特殊。

> 感觉不难想到，只要把数学意义对上即可

1.  **后验分布 `q(z|x)` 的新定义**:
    在 VQ-VAE 中，后验分布 `q(z|x)` 变成了一个**确定性的离散分布**。对于给定的 `x`，编码和量化过程会唯一确定一个码本向量 `e_k`。所以，后验分布可以看作是一个 one-hot 分布：
    `q(z=e_k | x) = 1`  (如果 `e_k` 是 `z_e(x)` 的最近邻)
    `q(z=e_j | x) = 0`  (对于所有 `j ≠ k`)

2.  **先验分布 `p(z)` 的新定义**:
    先验分布 `p(z)` 不再是高斯分布，而是在 `K` 个码本向量上的一个**均匀离散分布**。也就是说，我们先验地认为任何一个码本向量被选中的概率都是相等的：
    `p(z=e_j) = 1/K`  (对于所有 `j = 1, ..., K`)

3.  **KL 散度项的坍缩**:
    现在我们来计算这个新的离散框架下的 KL 散度 `KL(q(z|x) || p(z))`：
    `KL = Σ_{j=1 to K} q(z=e_j | x) * log( q(z=e_j | x) / p(z=e_j) )`

    由于 `q(z|x)` 是一个 one-hot 分布，这个求和中只有一项（当 `j=k` 时）不为零：
    `KL = 1 * log( 1 / (1/K) ) = log(K)`

**结论：KL 散度项变成了一个常数 `log(K)`！**

在模型优化中，一个常数项的梯度为零，对参数更新没有任何贡献。因此，在 VQ-VAE 的最终损失函数中，**这个 KL 散度项被直接忽略了**。

#### Part 4: VQ-VAE 的实际损失函数

既然 KL 正则项在数学上“消失”了，那模型如何学习呢？VQ-VAE 设计了新的损失函数来替代 ELBO 的功能：

最大化`L = - log p(x | z_q(x)) + ||sg[z_e(x)] - e_k||² + β * ||z_e(x) - sg[e_k]||²`

1.  **`log p(x | z_q(x))`**: **重构损失**。本质是decoder，这和 VAE 中的重构项目的一样。
    * 比如 `C * ||x - x_hat||²`
2.  **`||sg[z_e(x)] - e_k||²`**: **码本损失 (Codebook Loss)**。`sg` 是 `stop_gradient` 算子。这个损失项用于更新码本向量 `e_k`，让它向编码器的输出 `z_e(x)` 靠拢。
3.  **`β * ||z_e(x) - sg[e_k]||²`**: **承诺损失 (Commitment Loss)**。这个损失项用于更新编码器。它鼓励编码器的输出 `z_e(x)` “承诺”于它所映射到的那个码本向量 `e_k`，防止编码器的输出空间无限增长而码本更新跟不上。**这可以被看作是 VAE 中 KL 散度项的替代品，起到了正则化编码器的作用。**
    * β = 0.25，比较鲁棒

同时，为了解决 `argmin` 不可导的问题，VQ-VAE 使用了**直通估计器 (Straight-Through Estimator, STE)**，在反向传播时，直接将解码器输入端 `e_k` 的梯度复制给编码器输出端 `z_e(x)`，从而让编码器可以被训练。

#### 关于 Diagonal Covariance

对角协方差 (Diagonal Covariance) : 这同样是一个为了 简化计算 而做出的关键假设。我们假设，给定数据 x ，其对应的隐变量 z 的各个维度是条件独立的。
- 数学意义 : q_φ(z|x) 的协方差矩阵是一个对角矩阵，非对角线元素为 0。这意味着 z 的联合概率密度可以分解为各个维度边缘概率密度的乘积： q(z_1, z_2, ...|x) = q(z_1|x) * q(z_2|x) * ... 。
- 实践意义 :
  - 编码器输出简化 : 编码器只需要为 z 的 d 个维度输出 d 个均值和 d 个方差，总共 2d 个数值，而不需要输出一个包含 d*(d+1)/2 个独立数值的完整协方差矩阵。
  - KL 散度可解析计算 : 这是最重要的一个好处。当 q_φ(z|x) 和 p(z) 都是对角协方差的高斯分布时，它们之间的 KL 散度有一个 解析解 (closed-form solution) ，可以直接用公式计算出来，而无需进行复杂的蒙特卡洛采样估计。
     - $$KL( N(μ, σ²) || N(0, I) ) = 0.5 * Σ (σ² + μ² - 1 - log(σ²))$$
     - 这个公式可以直接嵌入到损失函数中，并且是完全可微分的。如果没有这个解析解，VAE 的训练将变得极其困难。

#### 关于 Gaussian Reparametrisation Trick

这个技巧的核心思想是： **将随机性与模型的参数分离开**，从而打通梯度路径，可以通过构造源源不断的随机数据，去学习模型参数

我们不直接从 z ~ N(μ_φ(x), σ²_φ(x)) 中采样，而是通过以下方式构造 z ：

* 从一个 固定的、与模型参数无关的 标准正态分布中采样一个随机噪声 ε 。即 ε ~ N(0, I) 。

* 通过一个确定性的函数来生成 z ： z = μ_φ(x) + σ_φ(x) * ε



#### 总结

- **数学上的理解**: VQ-VAE 中的 "variational" 是一种**概念上的继承**。它在理论上可以被解释为一个特殊的 VAE，其后验是一个确定性的离散分布，先验是一个均匀的离散分布。在这种特殊情况下，ELBO 中的 KL 散度项坍缩成一个常数，因此在最终的优化目标中被省略。
- **实践上的理解**: VQ-VAE **用一个码本和承诺损失取代了标准 VAE 中的 KL 散度正则化**。它不再强制隐空间服从高斯分布，而是强制编码器的输出被“绑定”到一个共享的、离散的码本上，通过这种方式来正则化隐空间。

所以，称其为 "Variational" 是为了表明它与 VAE 的师承关系和作为生成模型的共同目标，尽管它为了引入离散隐空间，在数学实现上走了另一条巧妙的道路。
        





## 线性代数

*  $$E_{S}=E_CE_U$$    -> $$e_s^x={E_U}^Te_c^x$$
* 最小二乘法：
  * 考虑线性方程组 $$Ax = b$$，当该方程组无解（即 $$b$$ 不在 $$A$$ 的列空间中）时，我们希望找到一个 $$\hat{x}$$ 使得 $$\|Ax - b\|^2$$ 最小。
  * 此时，$$\hat{x}=(A^TA)^{-1}A^Tb$$，$$A\hat{x}=A(A^TA)^{-1}A^Tb$$
  * 即 $$A\hat{x}$$ 是 $$b$$ 在 $$A$$ 的列空间上的投影，$$A\hat{x}$$ 与 $$b$$ 的误差在所有可能的 $$Ax$$ 中是最小的。 

* $$E_U^T E_U=\left(U_1,U_2,U_3, ... U_u\right)\left(\begin{array}{c}{U_1}^T\\{U_2}^T\\{U_3}^T\\...\\{U_u}^T\end{array}\right) = \sum_{i=1}^uU_i{U_i}^T$$

### SVD、矩阵分解

#### Theory

* 求解SVD

  * $$A = U\Sigma V^T \Rightarrow A^T = V\Sigma U^T \Rightarrow A^T A = V\Sigma U^T U\Sigma V^T = V\Sigma^2 V^T$$
  * $$A^{-1}=(U \Sigma V^T)^{-1} = (V^T)^{-1} \Sigma^{-1} U^{-1} = V \Sigma^{-1} U^T$$

* [SVD分解(一)：自编码器与人工智能](https://spaces.ac.cn/archives/4208) —— 苏剑林

  * **不带激活函数的三层自编码器，跟传统的SVD分解是等价的。**

    * 我们降维，并不是纯粹地为了减少储存量或者减少计算量，而是**“智能”的初步体现**

  * SVD

    * (m+n)k < mn

  * 自编码器

    * 无视激活函数，只看线性结构。自编码器是希望训练一个f(x)=x的恒等函数，但是中间层节点做了压缩
    * ![image-20241229231515019](./Mathematics/image-20241229231515019-1506147.png)

  * 压缩即智能

    * 通过压缩后进行重建，能够挖掘数据的共性，即我们所说的规律，然后得到更泛化的结果

    * ![image-20241229231727074](./Mathematics/image-20241229231727074-1506147.png)

    * 我们通过SVD分解，原始的目的可能是压缩、降维，但复原后反而衍生出了更丰富、词汇量更多的结果。

    * ```
      将结巴分词的词表中所有频数不小于100的二字词选出来，然后以第一字为行，第二字为列，频数为值（没有这个词就默认记为0），得到一个矩阵。对这个矩阵做SVD分解，得到两个矩阵，然后把这两个矩阵乘起来（复原），把复原后的矩阵当作新的频数，然后对比原始矩阵，看看多出了哪些频数较高的词语。
      ```

  * 激活函数在这里的物理意义

    * 是对无关紧要元素的一种舍弃（截断），这种操作，我们在很久之前的统计就已经用到了（扔掉负数、扔掉小统计结果等）。
    * 当然，在神经网络中，激活函数有更深刻的意义，但在浅层的网络（矩阵分解）中，它给我们的直观感受，就是截断罢了。

* SVD的聚类含义

  * https://spaces.ac.cn/archives/4216
  * 转化为三个矩阵相乘
  * ![image-20241229233643160](./Mathematics/image-20241229233643160-1506147.png)

* word2vec是SVD

  * https://spaces.ac.cn/archives/4233

  * 词向量Embedding层 = one hot的全连接层

  * 在做情感分类问题时，如果有了词向量，想要得到句向量，最简单的一个方案就是直接对句子中的词语的词向量求和或者求平均，这约能达到85%的准确率。

    * FastText，多引入了ngram特征，来缓解词序问题，但总的来说，依旧是把特征向量求平均来得到句向量
    * 本质上是 **词袋模型**

  * word embedding和SVD的联系

    * distributed representation，即分布式表示，N维embedding
      * 设想开一个窗口（前后若干个词加上当前词，作为一个窗口），然后统计当前词的前后若干个词的分布情况，就用这个分布情况来表示当前词，而这个分布也可以用相应的NN维的向量来表示
    * SVD将distributed representation降维到k维
    * Word2Vec的一个CBOW （continuous bag-of-words）方案是，将前后若干个词的词向量求和，然后接一个NN维的全连接层，并做一个softmax来预测当前词的概率

  * word2vec和svd的区别

    * 1、Word2Vec的这种方案，可以看作是通过前后词来预测当前词，而自编码器或者SVD则是通过前后词来预测前后词；

      2、Word2Vec最后接的是softmax来预测概率，也就是说实现了一个非线性变换，而自编码器或者SVD并没有。



#### Application

* [矩阵分解在协同过滤推荐算法中的应用 ](https://www.cnblogs.com/pinard/p/6351319.html)
  * SVD，计算量大
    * 稀疏SVD
      * 平均值补全
      * 随机投影或Lanczos迭代

  * FunkSVD
    * ![image-20241229023812815](./Mathematics/image-20241229023812815-1506147.png)

  * BiasSVD
    * 考虑 评分系统平均分μ,第i个用户的用户偏置项,第j个物品的物品偏置项
  * SVD++算法在BiasSVD算法上进一步做了增强，这里它增加考虑用户的隐式反馈
    * ![image-20241229024446412](./Mathematics/image-20241229024446412-1506147.png)

* 文档矩阵、主题模型
  *  Aij表示第 i 个文档中第 j 个词的出现情况
     * 词频/ TF-IDF

### 特征值

* 特征值求解
  * [幂迭代法 Power Iteration](https://en.wikipedia.org/wiki/Power_iteration) 求解最大特征值
  * QR算法

#### 谱范数、次可乘性 --> 误差传播

* 矩阵的谱范数 (Spectral Norm)
  * 对于一个矩阵 $$A \in \mathbb{R}^{m \times n}$$，其 谱范数 （也称为2-范数，$$||A||_2$$）被定义为：
  * $$||A||_2 = \sup_{x \neq 0} \frac{||Ax||_2}{||x||_2}$$
  * 最大“拉伸”比例
* 谱范数也等于矩阵 $$A$$ 的 最大奇异值 (Largest Singular Value) ，记为 $$\sigma_{max}(A)$$。
  $$||A||_2 = \sigma_{max}(A) = \sqrt{\lambda_{max}(A^T A)}$$
  其中，$$\lambda_{max}(A^T A)$$ 表示矩阵 $$A^T A$$ 的最大特征值。
* 范数的次可乘性 (Submultiplicativity)
  * 如果对于任意两个可相乘的矩阵 $$A$$ 和 $$B$$，都满足不等式$$||AB|| \leq ||A|| \cdot ||B||$$

* 证明 :
  * 利用谱范数的定义（$$||Az||_2 \leq ||A||_2 \cdot ||z||_2$$）：$$||A(Bx)||_2 \leq ||A||_2 \cdot ||Bx||_2$$
  * ----> $$||AB||_2 \leq ||A||_2 \cdot ||B||_2$$

#### 层条件数 (Condition Number)  -> 误差扰动

* **定义**: 矩阵 $J$ 的条件数 $\kappa(J) = ||J||_2 \cdot ||J^{-1}||_2 = \frac{\sigma_{max}(J)}{\sigma_{min}(J)}$。它衡量了矩阵对输入扰动的敏感度，即最大拉伸与最大压缩的比率。

* **分析**:

  * $\kappa(J_l) \approx 1$ 表示该层是“良态的 (well-conditioned)”，对不同方向的误差分量处理方式相似。
  * $\kappa(J_l) \gg 1$ 表示该层是“病态的 (ill-conditioned)”，变换是高度“各向异性 (anisotropic)”的。它会沿某些方向（最大奇异向量方向）急剧放大误差，同时沿另一些方向（最小奇异向量方向）急剧缩小误差。
  * 在深度网络中，多个病态层的累积效应会导致训练极其不稳定，部分梯度爆炸而另一部分梯度消失同时发生。

* 证明：

  *  $$||J||_2 = \sigma {max}(J)$$。
    * $$||J|| 2^2 = \sup {x \neq 0} \frac{(Jx)^T(Jx)}{x^T x} = \sup {x \neq 0} \frac{x^T J^T J x}{x^T x}$$
    * 这个表达式 $$\frac{x^T (J^T J) x}{x^T x}$$ 是矩阵 $$J^T J$$ 的 瑞利商 (Rayleigh Quotient) 。根据瑞利商的性质，其最大值等于该矩阵的最大特征值。令 $$\lambda_{max}(J^T J)$$ 为矩阵 $$J^T J$$ 的最大特征值。$$||J||_2^2 = \lambda {max}(J^T J)$$
    * 根据奇异值的定义，矩阵 $$J$$ 的奇异值 $$\sigma_i(J)$$ 是矩阵 $$J^T J$$ 的特征值的平方根。因此，$$J$$ 的最大奇异值 $$\sigma_{max}(J)$$ 等于 $$\sqrt{\lambda_{max}(J^T J)}$$。

  * 证明 $$||J^{-1}||_2 = \frac{1}{\sigma {min}(J)}$$。 
    * 利用奇异值分解



### matrix vector derivatives for machine learning

> matrix vector derivatives for machine learning.pdf

### Cholesky decomposition

https://en.wikipedia.org/wiki/Cholesky_decomposition

* 分解 a [Hermitian](https://en.wikipedia.org/wiki/Hermitian_matrix) [positive-definite matrix](https://en.wikipedia.org/wiki/Positive-definite_matrix) A
* e.g.
  * 解方程：提升数值计算稳定性
  * non linear optimization
    * GPTQ

## 最优化、凸优化

> todo 《Optimization in Theory and Practice》

### 算法

* hill climbing https://en.wikipedia.org/wiki/Hill_climbing
  * 多元函数，每次只改变一个输入
  * 容易陷入local maxima

### 应用

#### 飞行器精准制导

【NASA公开课：凸优化如何实现飞行器精准制导 | Behçet Açıkmeşe讲座【中英双语】-哔哩哔哩】 [NASA公开课：凸优化如何实现飞行器精准制导 | Behçet Açıkmeşe讲座【中英双语】_哔哩哔哩_bilibili](https://b23.tv/aMLplAp)



## 数学分析

### 一些定义

* 完备的度量空间是泛函分析中的重要概念，其核心性质是**所有柯西序列都收敛到该空间中的某个点**。
  * 核心在于确保 “所有潜在的极限点都存在于空间内”

### 压缩映射原理

![image-20250402221637163](./Mathematics/image-20250402221637163-1506147.png)

* [压缩映射与皮卡迭代的简单比较](https://www.bilibili.com/video/BV1pjAte2EwV )



## 微分方程 ODE

### 基础技巧

* [用特征线方法与傅里叶变换求解偏微分方程](https://www.bilibili.com/video/BV16JFTeVEGj)
* 皮卡迭代
  * ![image-20250402222144436](./Mathematics/image-20250402222144436-1506147.png)

### 应用

* [玻色爱因斯坦凝聚与Boltzmann-Nordheim方程](https://www.bilibili.com/video/BV1YwNHeSEbp)
  * 利用测试函数，求弱解

## 抽象代数

* **环（ring）**，是抽象代数的基本结构，指非空集合 $$ R $$ 配以加法与乘法两种二元运算，满足：   
  * $$ (R, +) $$ 是阿贝尔群（加法交换、有逆元等）；   
  * 乘法结合律 $$ (ab)c = a(bc) $$；   
  * 乘法对加法的左右分配律 $$ a(b + c) = ab + ac $$、$$ (a + b)c = ac + bc $$。  
  * 环在数学与工程领域应用广泛，为众多数学分支及实际应用提供了统一的代数框架，是理解和解决复杂问题的重要工具：
    * 在密码学中，其结构用于设计加密算法；
    * 代数几何里，环帮助刻画空间与函数性质；
    * 编码理论中，借助环的特性构造高效编码，提升数据传输可靠性与效率。

## 泛函分析

[Hanner不等式与Lp空间的一致凸性](https://www.bilibili.com/video/BV18VZcYKEsz)

* Lp空间

![image-20250405000218965](./Mathematics/image-20250405000218965-1506147.png)

* 一致凸空间
  * ![image-20250405000623658](./Mathematics/image-20250405000623658-1506147.png)

* Lp空间的一致凸性

![image-20250405000829187](./Mathematics/image-20250405000829187-1506147.png)



![image-20250405000910294](./Mathematics/image-20250405000910294-1506147.png)

## 数字信号处理

### DFT

![image-20250605195600286](./Mathematics/image-20250605195600286-1506147.png)







## 数学在工科的应用

* [为什么这么多年直到马斯克出来才想到做可复用火箭？](https://www.zhihu.com/question/597238433/answer/3080541702)
  * ![image-20241110022322621](./Mathematics/image-20241110022322621-1506147.png)
