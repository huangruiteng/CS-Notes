## Distributed Systems

[toc]

#### Intro

##### 基础架构与人 —— Haiping Zhao

* 基础架构

  * 底层软硬件

  * 不含业务逻辑：抽象化；云化
    * 四大资源：
      * CPU：计算
      * 内存
      * 网络
      * 磁盘：存储


  * 人也是基础架构的一部分


* 不同的协同方式，不同的工程文化

  * 开源社区（Facebook），责 < 权 = 利

  * 中台（Alibaba），责 > 权 = 利

  * 纵横交织（ByteDance），责 = 权 = 利
    * 需要控制合作的cost


* 人和机器的矛盾

  * 编译器

  * 代码共享

  * 微服务

  * 工具和流程


#### AI + 分布式系统

* [大模型时代的计算机系统革新：更大规模、更分布式、更智能化 -- MicroSoft](https://mp.weixin.qq.com/s/7nK3fERGj7a6pcwNMKFdSQ)
  * **创新超大规模计算机系统以支持未来人工智能的发展**
    * 推出了能够跨多个加速器执行集体通信算法的微软集体通信库 MSCCL
    * 以及有助于开发大规模深度神经网络模型的高性能 MoE（Mixture of Experts，混合专家）库 Tutel
    * [推出了 Welder、Grinder 等编译器](http://mp.weixin.qq.com/s?__biz=MzAwMTA3MzM4Nw==&mid=2649494837&idx=1&sn=0fa87e74e292b7281f40fc64e2328bd3&chksm=82c7fcb1b5b075a7b6917970bce6efc9ef901fb8d9401cbe52385390fe491089738529a46f36&scene=21#wechat_redirect)[3]
  * **重构云计算这一重要的 IT 基础平台**
    * 传统云计算领域的研究方向，如虚拟机（VM）、微服务（Micro-services）、计算存储分离、弹性计算等，在人工智能时代下需要被重新定义和发展。虚拟化技术需要在分离式架构的背景下进行重新设计；微服务及其相关云计算模块需要为 AI Agent 和大语言模型构建高效且可靠的服务平台；数据隐私和安全需要成为云计算系统创新的核心要素。所有这些变革创新都要服务于云计算系统的智能化（Cloud + AI）。
    * 以搜索系统为例，我们基于异构计算系统和深度学习方法对搜索系统进行了创新，从 Web Scale 的矢量搜索系统 SPANN[4] 到最新的 Neural index 索引系统 MEVI[5] 的设计，这些创新不仅极大提升了搜索和广告系统的性能，也为未来信息检索系统提供了新的范式
  * **设计前沿的分布式系统，以适应更广泛的分布式智能需求。**
    * “人类的智能不单存在于人类的头脑中，还广泛分布在整个物理世界、社会活动和符号体系中——这就是‘分布式智能’。”美国认知科学家 Roy Pea 在 1993 年发表的一篇论文《Distributed Cognition: Toward a New Foundation for the Study of Learning》中提出了分布式智能（distributed cognition）的概念，为我们提供了一种新的视角来理解人工智能系统与社会以及环境之间的相互作用。
    * 移动端优化
      * [PIT](http://mp.weixin.qq.com/s?__biz=MzAwMTA3MzM4Nw==&mid=2649496775&idx=1&sn=f3775b49e27541b985dd4b65564e3d3b&chksm=82c7f543b5b07c55e821401490fba94588e2aec276eab5b7142567fbd4ac1bd2aff317d04ded&scene=21#wechat_redirect)[6]、MoFQ[7]等多种移动端模型量化、稀疏化以及运行时优化的技术
      * 利用基于查找表（Lookup Table）等全新的计算范式来提升端侧推理效率，包括 LUT-NN[8] 等技术
    * 使学习算法可以更好地从任意信号（Signals）中捕捉智能





#### 分布式基础

##### Intro

* 最终一致性：系统中的所有分散在不同节点的数据，经过一定时间后，最终能够达到符合业务定义的一致的状态

  * 一致性指数据一致性，不是事务一致性（ACID 是事务一致性）


  * 存在条件：多个节点/系统


  * 不一致可能是暂时的，最终要一致
  * [讲最终一致性的知乎文章](https://zhuanlan.zhihu.com/p/25933039)


* [CAP theorem](https://en.wikipedia.org/wiki/CAP_theorem)
  * consistency: Every read receives the most recent write or an error.
  * availability: Every request receives a (non-error) response, without the guarantee that it contains the most recent write.
  * partition tolerance: The system continues to operate despite an arbitrary number of messages being dropped (or delayed) by the network between nodes.

* [PACELC theorem](https://en.wikipedia.org/wiki/PACELC_theorem)

##### MapReduce

**[l01-Introduction and MapReduce](https://github.com/huangrt01/CS-Notes/blob/master/Notes/Distributed-Systems/l01-Introduction%20and%20MapReduce)**

##### 最终一致性解决方案

* 两阶段提交（2PC）
  * 所有下属节点confirm后才发起操作
  * [2PC + WAL](./Software-Engineering.md#walwrite-ahead-log先持久化恢复记录再持久化正式状态)：参与者持久化 prepare，协调者持久化 commit / abort decision，使节点重启后仍能恢复事务状态；WAL 不会消除 2PC 等待协调者的阻塞问题

* 异步确保（无事务消息）
* 异步确保（事务消息）
* [补偿交易 (Compensating Transaction)](https://docs.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)
* 消息重试
* 幂等（接口支持重入）：数据库唯一键挡重入

##### 可靠性与容错模式 (Reliability & Fault Tolerance)

* **重试 (Retry)**：在操作失败后重新尝试，以应对网络抖动、服务瞬时不可用等**暂时性故障 (Transient Failures)**。
* 重试是否有用，取决于“下一次尝试有什么会变化”。外部服务可能恢复时，原请求配合 backoff / jitter 重放有意义；确定性校验持续拒绝同一输入时，原样重放只会增加延迟和成本。
* **先分类，再决定是否改请求**：

| 失败类型 | 下一次尝试 | 原因 |
| --- | --- | --- |
| 网络超时、连接重置、临时 5xx | 保持业务请求不变，增加 backoff / jitter | 期待外部状态恢复；随意改 payload 会改变操作语义 |
| 输出被截断、格式不合法、约束未满足 | 保留原目标，加入最小且针对性的失败反馈 | 外部状态不会自动变化，必须让生成策略发生变化 |
| 鉴权失败、非法配置、确定性前置条件不满足 | fail fast，等待配置或用户修复 | 重试无法消除根因 |

* **Retry budget 属于 policy**：最大尝试次数、deadline、输出或资源上限应由配置层拥有。执行器可以根据错误改写下一次策略，但不应偷偷提高上限、追加次数或换模型，否则会破坏成本边界和可复现性。
* **只有完整结果才能提交**：失败尝试可以进入 trace，但不能安装为正式状态。带副作用的调用还需要 idempotency key、去重或补偿，避免“响应丢失后重试”把同一操作执行两次。
* **风险**：过载时的大量重试会形成 retry storm，并把下游压力放大成 cascading failure。

* **退避 (Backoff)**
  * **目的**：避免立即重试给故障服务带来持续压力，给系统恢复的时间。
  * **策略**：
    * **固定退避 (Fixed Backoff)**：每次重试等待固定时间 (e.g., 1s, 1s, 1s)。
    * **指数退避 (Exponential Backoff)**：等待时间随重试次数指数增长 (e.g., 1s, 2s, 4s, 8s)。
      * 公式：$$WaitTime = Base \times 2^{Attempt}$$
      * 通常会设置最大等待时间 (Max Interval) 和最大重试次数 (Max Retries)。

* **抖动 (Jitter)**
  * **目的**：防止所有客户端在同一时刻重试（即**惊群效应, Thundering Herd**），将流量打散。
  * **Full Jitter**：$$Wait = Random(0, Base \times 2^{Attempt})$$
  * **Equal Jitter**：$$Temp = Base \times 2^{Attempt}; Wait = Temp/2 + Random(0, Temp/2)$$
  * **Decorrelated Jitter**：$$Wait = Random(Base, Wait_{prev} \times 3)$$

* **相关模式**
  * **断路器 (Circuit Breaker)**：当失败率达到阈值时，暂时切断请求，快速失败，避免无意义的重试。
  * **Hedging Requests (对冲请求)**：向多个副本发送请求，使用最快返回的结果（解决长尾延迟）。

#### Kafka

##### Kafka 核心设计原理

* kafka架构
  * distributed high throughput message system (version 0.10), distributed streaming platform
  * 特点
    * 低延迟：O(1)，TB级
    * 高吞吐：单机qps 10w，虚拟机6个节点，单条消息1KB，打满1GB带宽
    * 水平扩展：broker消息分区，支持在线水平扩展
    * 顺序性：partition内部的局部顺序性
    * 多场景：离线/实时，延迟ms级
  * 架构
    * producer：app/web/mysql
      * 内存内部队列，push失败3次抛异常
      * 如果希望不丢数据，可以用flush方法
    * broker：服务器 kafka server
      * 数据存进本地磁盘不用担心内存被打爆
      * producer--push-->broker<--pull--consumer
      * pull的好处是避免consumer消费不过来，缺点是有一定延迟
        * long pulling 长轮训：有数据再返回
        * 不用push方法可以让broker的功能更简单，不需要知道consumer的信息，方便水平扩展
    * consumer：hadoop/spark/flink/other kafka
      * 能处理多少数据拿多少
    * zookeeper：管理broker集群相关的元信息、领导选举
      * 以前producer会连zk，后来直连broker
      * broker和zk有长连接，并且本地缓存元信息
  * Time & Partition & Segment
    * Record
      * Key-Value
      * Timestamp: for streaming Kafka
    * Topic: 逻辑概念，用于发布-订阅
    * Partition：物理上对应文件夹（可以认为是文件），均匀分布在broker间；一个topic对应多个partition
      * 理解为数组，有offset的概念
    * Segment：segment对应文件，partition对应文件夹
  * 机制
    * 写数据：append-only，机械磁盘顺序读写性能还不错，甚至比内存随机读写更快
    * 删数据：文件过大、磁盘满，直接删最老的segment
  * consumer
    * 两种consumer API
      * low level (assign):
        * Input: partition, offset, length
        * 缺点在于当consumer和partition动态变化时，如何给consumers分配partitions
      * high level (subscribe):
        * consumer group顺序消费某个topic
        * offset存于zk或kafka或自定义存储
        * 实现了rebalance机制
  * producer
    * 异步：batch.size, linger.ms, flush()
    * 保证顺序性：Queue与retry机制
      * retry.backoff.ms
      * retries
      * max.in.flight.requests.per.connection 设为1提升顺序性
    * partitioner.class
      * 无key的情形：round-robin，无法保证同user数据进同一个partition
      * 通常用uid做key
      * 能引入cluster信息（比如broker和producer距离）

```java
public int partition(String topic, Object key, byte[] keyBytes, Object value, byte[] valueBytes, Cluster cluster) {
  List partitions = cluster.partitionsForTopic(topic);
  int numPartitions = partitions.size();
  if (keyBytes == null) {
    int nextValue = nextValue(topic);
    List availablePartitions = cluster.availablePartitionsForTopic(topic);
    if (availablePartitions.size() > 0) {
      int part = Utils.toPositive(nextValue) % availablePartitions.size();
      return availablePartitions.get(part).partition();
    } else { // no partitions are available, give a non-available partition
      return Utils.toPositive(nextValue) % numPartitions;
    }
  } else { // hash the keyBytes to choose a partition
    return Utils.toPositive(Utils.murmur2(keyBytes)) % numPartitions;
  }
}
```

* kafka consumer rebalance机制演进
  * 一个partition只分配给一个consumer
    * 简单+保证一个consumer能顺序处理partition的数据
    * 一个consumer可消费多个partition
  * rebalance的完整过程
  * 自治式rebalance
    * zk注册/consumers/[consumer group]/ids/[consumer id] watch
    * /brokers/id也注册watch
    * 每个consumer去watch这个状态，自己做决定
    * 坏处
      * Herd Effect：任何broker/consumer的增减会触发所有consumer的rebalance
      * Split Brain：同一时刻不同consumer从zk看到的状态可能不一样
      * 调整结果不可控（虽然可能有最终一致性）
  * 集中式rebalance
    * coordinator监听topic、partition
    * 接收consumer注册，选取leader
    * leader SyncGroup -> coordinator
    * 其它member SyncGroup获取结果
* kafka高可用原理
  * topic的replication factor：10个partition变成30个partition
  * 数据复制
    * 每个partition有一个broker作为leader
      * producer->leader, follower<-leader

    * in-sync replica (ISR): a broker that has the latest data for a given partition.
      * 只有所有ISR commit了，才认为producer发送成功，允许consumer消费

    * 参数控制：落后时间、落后消息个数
      * Server: 
        * replication.lag.time.max.ms=10000
        * replication.lag.max.messages=4000

      * Topic: min.insync.replicas=1
      * Producer: request.require.acks=1
      * 备份太慢，则从ISR里踢掉，不用担心像同步复制有慢节点问题

    * 领导选举：各自选举、基于controller的选举
      * 目前实现是选新leader从ISR里随机选

  * 处理replicas全部失败
    * 策略1:等ISR中任一replica恢复
      * 降低可用性，极端情况下partition永久不可用 

    * 策略2:等任一replica恢复 （default，默认高可用方案）
      * 可能丢数据

  * 拓展
    * 常用一致性算法（commit策略）：WNR、Quorum、Paxos及其变种

* kafka exactly once
  * consumer exactly once

    * 两阶段提交（0.1之后）
      * 耗时长，不适用低延时场景
      * 需要参与两阶段提交的所有系统皆实现XA接口

    * At lease once + 下游幂等处理
      * 实现简单
      * 要求下游系统提供幂等处理接口
      * auto.commit.interval.ms=5000

    * Offset更新与数据处理放在同一事务中
      * 要求下游处理系统可回滚
      * 需要提供事务功能的系统参与
      * e.g. offset和消息一起存进mysql；读到内存但还未消费的数据持久化到hdfs
      * syncCommit

  * producer exactly once
    * enable.idempotence=true
    * producer生成一个PID
    * broker维护每个partition来自每个PID的当前最大序号，来判断接受/重复/乱序

##### 操作

* consumer 介绍
  * https://docs.confluent.io/platform/current/clients/consumer.html#ak-consumer
  * `auto.offset.reset` = earliest / latest (default) / none
    * https://issues.apache.org/jira/browse/KAFKA-3370
    * 触发的两种场景：1）指定的timestamp过早，数据没了；2）consumer group没有commit过offset，挂了

* Debug lag
  * 数据生成、样本消费

  * lag是否持续、container/application cpu/mem是否正常

  * partition lag情况

  * 多topic是否消费均匀

  * flink资源情况

* consumer lag
  * 用户侧
    * 消费能力不足
      * Topic的单partition入流增加
      * 业务逻辑耗时长
    * consumer在不断重启
    * 处理消息时间长，影响fetch数据
  * Kafka侧
    * Broker压力大
    * Broker磁盘故障
  * [Kafka的Lag计算误区及正确实现](https://blog.51cto.com/u_15127513/2682807)
    * Lag = HW - ConsumerOffset

#### ZooKeeper

```python
ChildrenWatch
```

#### Spark

##### Stage划分

* Stage的边界是Shuffle操作。一个Job中，没有Shuffle的线性处理流程只有一个Stage 0。
* 宽依赖 (Shuffle, 触发新Stage): `groupByKey`, `reduceByKey`, `join`, `repartition`, `orderBy`。
* 窄依赖 (不触发Shuffle): `map`, `filter`, `select`, `read`。

##### Shuffle策略

- Shuffle Hash Join (洗牌哈希连接)
  - 核心思想 ：把两张大表按 key 切割，然后把相同 key 的数据块发送到同一个节点上进行连接。。
- Broadcast Hash Join (广播哈希连接)
  - 核心思想 ：把小表完整地复制分发给所有计算节点，让它和分布在各个节点上的大表数据进行本地连接。
- Shuffle Sort Merge Join (洗牌排序合并连接)
  - 核心思想 ：先把两张表按 key “洗牌”并 排序 ，然后在每个节点上像拉拉链一样，将两条有序的数据流合并起来完成连接。

##### 1 Billion Row Challenge

![image-20250525021552954](./Distributed-Systems/image-20250525021552954.png)



#### Flink 

* streaming依赖kafka的exactly once 保障。用的是water mark机制来确定消费进度
* Per Message VS. MicroBatch
  * MicroBatch
    * Spark StructStreaming MicroBatch
    * 一致性语义：at-least once, exactly once
    * 吞吐高

  * Per Message
    * Flink, SparkStreaming Continuous Mode
    * Partition数据消费节点稳定性强
    * 数据倾斜处理能力强
    * 一致性语义：at-least once(barrier不对齐), exactly once
    * 低延迟
    * 吞吐中高

* Storm数据模型与group type
  * Storm
    * spout代表一个storm拓扑中的数据入口，连接到数据源，将数据转化为一个个tuple，并发射tuple。
  
    * stream是由无限制个tuple组成的序列。tuple为storm的核心数据结构，是包含了一个或多个键值对的列表。

    * bolt可以理解为计算程序中的运算或者函数，bolt的上游是输入流，经过bolt实施运算后，可输出一个或者多个输出流。
      * bolt可以订阅多个由spout或者其他bolt发射的数据流，用以构建复杂的数据流转换网络。
  
  * GroupType主要用于Extractor+Joiner（Spout+Bolt）模式时，上下游之间交互方式；
    - keyby为按照key做hash，然后发给下游Joiner节点，单条数据会跨节点发送；
    - forward是保证spout和bolt在相同container里面执行，不跨节点发送数据；
    - shuffle是按照random(key)方式下发，单条数据会随机下发给下游节点

* FLIP
  * [FLIP-150: Introduce Hybrid Source](https://cwiki.apache.org/confluence/display/FLINK/FLIP-150%3A+Introduce+Hybrid+Source)


##### 《Serving Machine Learning Models》chpt 4

http://kb.sites.apiit.edu.my/files/2018/12/ebook-serving-machine-learning-models.pdf

* 介绍了flink的特点：scalabality、checkpointing、state support、window semantics
* Process Function -> basic building blocks
  * Events (individual records within a stream)
  * State (fault-tolerant, consistent)
  * Timers (event time and processing time)
* Flink provides two ways of implementing low-level joins, key-based joins implemented by **CoProcessFunction**, and partition-based joins implemented by **RichCoFlatMapFunction**
  * Key-based Joins：类似于按模型分组
  * Partition-Based Joins：一个instance能serving所有model
    * 一个任务多个instances执行该任务的不同input data subset



```java
// Partition-Based Joins
public class DataProcessMap extends AbstractRichFunction implements CoFlatMapFunction<byte[], ModelConfig, Double> {
  
  public double map(byte[] rawValue) throws RuntimeException {
    
  }
  
  @Override
  public void flatMap1(byte[] bytes, Collector<double> collector) throws RuntimeException {
    readLock.lock();
    double score = map(bytes);
    readLock.unlock();
    collector.collect(score);
  }
  
  @Override
  public void flatMap2(ModelConfig modelConfig, Collector<double> collector) {
    writeLock.lock();
    this.modelConfig = modelConfig;
    logger.info("Use new model config: " + modelConfig.toString());
    writeLock.unlock();
  }
}

DataStream<byte[]> kafkaInstanceStream = env.addSource(kafka_source);
DataStream<double> myStream = kafkaInstanceStream.connect(configDataStream.broadcast())
                .flatMap(new DataProcessMap(curConfig));


```





```java
// DataStream.class
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.getConfig().setGlobalJobParameters(params);
FlinkKafkaConsumer010<byte[]> kafka_source = Kafka010Utils.customFlinkKafkaConsumer010(
                cluster, topic, groupId, properties, new ByteArraySchema());
kafka_source.setXXX(...);
...
DataStream<byte[]> kafkaInstanceStream = env.addSource(kafka_source);

```



```java
// source function
import my_config.Config
import org.apache.flink.streaming.api.checkpoint.CheckpointedFunction;
import org.apache.flink.streaming.api.functions.source.SourceFunction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConfigSource implements SourceFunction<Config>, CheckpointedFunction {
  private static final Logger logger = LoggerFactory.getLogger(ConfigSource.class);
  private Config config;
  private volatile boolean isRunning = true;
  private transient ListState<Config> checkpointed;
  public ConfigSource(Config config) {
    this.config = config;
  }
  
  @Override
  public void run(SourceContext<Config> sourceContext) {
    while (isRunnning) {
      // this synchronized block ensures that state checkpointing,
      // internal state updates and emission of elements are an atomic operation
      synchronized (sourceContext.getCheckpointLock()) {
				Set<Long> oldList = null;
        if (config.XXX() != null) {
          oldList = new HashSet<>(config.XXX());
        }
        boolean changed = false;
        Set<Long> list = GetXXX();
        if (!list.equals(oldList)) {
          changed = true;
        }
        if (changed) {
          sourceContext.collect(config);
        }
        
      }
      try {
        Thread.sleep(60000);
      } catch (InterruptedException e) {
        logger.error("Sleep interrupted: " + e);
      }
    }
  }
  
  @Override
  public void cancel() {
    isRunning = false;
  }
  
  @Override
  public void snapshotState(FunctionSnapshotContext functionSnapshotContext) throws Exception {
    this.checkpointed.clear();
    this.checkpointed.add(config);
  }
  
  @Override
  public void initializeState(FunctionInitializationContext functionInitializationContext) throws Exception {
    this.checkpointed = functionInitializationContext
      .getOperatorStateStore()
      .getListState(new ListStateDescriptor<>("config", Config.class));

    if (functionInitializationContext.isRestored()) {
      for (Config config: this.checkpointed.get()) {
        logger.info("Old config: " + config.toString());
      }
    }
  }
}
```



##### 踩坑

* Compile error: error: scala.reflect.internal.MissingRequirementError: object java.lang.Object in compiler mirror not found.
  * solution: scala版本2.11，需要使用jdk8
  * Idea scale compiler: https://www.jetbrains.com/help/idea/compile-and-build-scala-projects.html

#### Apache Hadoop YARN: Yet Another Resource Negotiator

[YARN官网](https://hadoop.apache.org/docs/stable/hadoop-yarn/hadoop-yarn-site/YARN.html)

[YARN 在字节跳动的优化与实践](https://mp.weixin.qq.com/s/9A0z0S9IthG6j8pZe6gCnw)

1.Abstract

解决两大问题：1）依赖特定编程模型 2）中心式管理难以scale

设计核心是 separating resource management functions from the programming model，更彻底地将 platform和framework抽象开

2.History

R1,R2: hadoop community

R3: HoD

R4,R5: HoD -> shared clusters

R6,R7: shared clusters

R8,R9,R10: Apache MapReduce的局限性 -> YARN

3.Architecture

* 核心思路

  * RM是中心，也是连接AM和NM的桥梁

  * RM还能找AM要回资源

- ResourceManager，用于管理集群中的用户作业和分配资源。（缩写为RM）
- NodeManager，用于该节点上的用户作业和工作流。（缩写为NM）
  - container launch context (CLC)的概念，启动、监控、local service、auxiliary service
- Container，分布式任务中资源（memory、cpu）分配的最小单位
- ApplicationMaster，用户应用程序驻留的地方，是一个特殊的Container（缩写为AM）
  - AM: late binding, the process spawned is not bound to the request, but to the lease.
    - 它允许YARN在AM启动之前进行资源分配。当AM被授予租约时，可以在后台进行资源预分配。这样可以减少应用程序启动的延迟，并提高资源的利用率。
    - 其次，它允许AM在租约到期之前重新申请资源。如果AM需要更多的资源来扩展应用程序的规模或处理更大的工作负载，它可以在租约到期之前重新向YARN请求资源。这种灵活性使得应用程序可以根据需要进行动态调整，而不需要重新启动整个应用程序。
- 提交任务的流程
  - RM注册
  - 生成AM
  - AM请求同节点上的NM
  - 拉起Container

![1280X1280](Distributed-Systems/yarn.png)

* fault tolerance: RM对AM有责任、AM责任最重

  * YARN only secures its deployment

  * RM单点故障，Work is in progress to add sufficient protocol support for AMs to survive RM restart.

  * 抽象分离的代价：更多fault tolerance工作交给了frameworks来设计


4.YARN in the real-world

compute resource，分布式计算资源池，跑spark、flink任务等

集群一般会配两个RM、成千上万个NM；多个RM之间用zk选主，同一时间只有一个在工作

e.g. 500000 jobs daily

一些concern：

* HDFS NameNode becomes the bottleneck
* YARN have been observed on a few large clusters with massive amounts of small applications, but recent improvements in heartbeat handling have mitigated some of these issues.


One of the most important architectural differences that partially explains these improvements is the removal of the static split between map and reduce slots.

6.Related Work

和MesOs等类似架构对比，YARN特点是multiple application frameworks、per-job intra-framework scheduler、资源管控、lazy binding等

和基于虚机的任务对比，YARN更适合运行时间短、切换更频繁的任务









理想调度算法

ideal scheduler: Multiple Knapsack Problem(MKP) (NP-C Problem)

经典生产调度算法1 - 吞吐型

* [YARN原生调度策略](https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/FairScheduler.html)

* with Quota/Priorities/DRF

  

经典生产调度算法1 - 全局视角
* 每次分配按规则对节点进行sort
* 问题1:吞吐效率问题？(scalable)
* 缓存节点排序结果(多次调度一次排序/ 抽样排序)
* 并发多个 {调度队列, 节点分区}（做hash、吞吐提升明显）
* 问题2:同一request内多个节点间的约束很难表达
  * 比如gang性、打散、集中、碎片最少等

[The evolution of cluster scheduler architectures](https://www.cl.cam.ac.uk/research/srg/netos/camsas/blog/2016-03-09-scheduler-architectures.html)

调度策略：队列

* 单集群内的物理节点被划分为多个 label
* Label 的资源总量在逻辑上被划分为多个队列
* 队列配置min/max值（允许一定的超用、max对用户隐藏）

调度策略：DRF

* 队列和应用都同时声明不止一个维度的资源 (eg. CPU, MEM)
* 在进行排序时, 如果只考虑一个维度, 可能导致其它维度碎片严重
* DRF(Dominant Resource Fairness) 将各个维度上已经使用的资源占其维度上的资源总量的百分比中最大的值作为其主资源的代表, 各个队列、应用直接对主资源代表进行比较, 进而得到排序

=> req定制Node的弱约束、req内强/弱约束



Quota管理

* 固定分组 -> 固定分组+池化quota -> 完全quota

* 可抢占任务 & 不可抢占任务
  * 可抢占任务不占用 Quota，填满空闲资源
  * 不可抢占任务占用 Quota，保证 Quota 内的任务所需资源始终可以得到满足

* Quota化带来资源碎片问题



Fragmentation

* 碎片率取决于 max_task_size/node_size，这也是为什么大家追求集群node数量的原因（YARN最多单集群5w nodes）

* 资源碎片可能导致紧急任务的资源不够，这是池化的一个副作用
* 策略：
  * Binpack 算法尽量堆叠任务，优先将一台机器资源占满 => 高优任务堆叠 + 低优任务逆向堆叠
  * 小分组问题（资源本身就少）：整机资源预留，以保证整机资源高可用；预留时可调度低优任务。



资源隔离：物理隔离

方案一：将物理机分别划入不同的集群 

* 场景：
  * 离线&流式机器隔离 
  * 单集群过大拆分
* 优势：完整独立的故障域 
* 缺点：运维成本，需要搭建独立的RM及配置的监控报警

方案二：将物理机划入同个集群内的不同Label中 

* 场景：
  * 核心作业队列隔离
  * 跨POD物理机隔离
* 优势：共用相同RM
* 缺点：共享RM全局配置, 如单心跳分配container数量



资源隔离：共享物理机隔离

* AMD机器跨numa能力弱，因此划分subnuma

![isolate-resource](Distributed-Systems/isolate-resource.png)







#### Mesos: A Platform for Fine-Grained Resource Sharing in the Data Center

1.Introduction

across framework的shared cluster

two-level scheduling mechanism called resource offers. 

* 不同框架接入Mesos很方便，只需要迁移自己的scheduler

和YARN做对比：

* YARN的AM的“影响调度”的能力比Mesos弱，并不具备完全的"two-level scheduling"能力
* Mesos is an offer-based resource manager, whereas YARN has a request-based approach 感觉YARN在框架间对资源的分配会更灵活一些

3.Architecture

rejection mechanism

fault tolerance

* designed the master to be soft state, so that a new master can completely reconstruct its internal state from information held by the slaves and the framework schedulers.

4.Mesos Behavior

5.Implementation

hadoop port实现的local filesystem访问问题：

Hadoop normally writes map output files to the local filesystem, then serves these to reduce tasks using an HTTP server included in the Task-Tracker. However, the TaskTracker within Mesos runs as an executor, which may be terminated if it is not running tasks. This would make map output files unavailable to reduce tasks. We solved this problem by providing a shared file server on each node in the cluster to serve local files

6.Evaluation

overhead < 4%



Mesos 迁移 Yarn 的思路

* 阶段一：Proxy Solution: Big AM 模式，将 Yarn 调度提到一个 AM Proxy 来实现，好处是能复用原先的大部分逻辑，缺点是和 Yarn 生态有冲突，RM 的调度被“剥夺”，不利于后续资源池化推进
* 阶段二：Yarn 池化方案：AM 不再感知所有机器节点信息并独占机器，而是将资源分配交给 RM
* 阶段三：A Big AM -> An AM per Job





#### Design patterns for container-based distributed systems

https://skyscribe.github.io/post/2019/07/21/from-borg-to-kubernetes/

https://kubernetes.io/

single-container patterns for container management, single-node patterns of closely cooperating containers, and multi-node patterns for distributed algorithms

容器是更通用、更贴近底层的分布式抽象手段，是代码开发到生产环境更便捷的通路

容器之于分布式就是对象之于oop，只有用容器化这一抽象把系统和应用分离开，才能基于此做很多更复杂的优化（混布提升利用率、错峰潮汐、更精细的物理资源划分）

3.Single-container management patterns

从upward和downward两方面思考

* upward
* downward
  * scale up
  * For example, Kubernetes uses a “grace-ful deletion” feature of Docker that warns a container, via the SIGTERM signal, that it is going to be termi-nated, an application-defined amount of time before it is sent the SIGKILL signal.

4.Single-node, multi-container application patterns

4.1 Sidecar pattern

可利用 [cgroups](https://www.kernel.org/doc/Documentation/cgroup-v1/cgroups.txt)

4.2 Ambassador pattern

4.3 Adapter pattern

5.Multi-node application patterns

5.1 Leader election pattern

5.2 Work queue pattern

5.3 Scatter/gather pattern

6.Related Work

* Service-oriented architectures (SOA)


#### Ray: 动态可编程分布式计算框架

1.Ray是一个动态可编程的分布式计算框架，支持分布式训练，主要体现在以下几方面：

* 丰富的本地训练场景（清晰指派local/remote的任务/角色，task无状态，actor有状态）

* 灵活训练规划pipeline（用户可以在Actor里自定义逻辑，包括循环、计时器等）

* 灵活数据源（流批处理融合，支持简单的数据处理chain）

* One-off system：针对RL任务的特化，1）training, serving, simulation一体化，2）dynamic execution。推荐系统不一定需要，可能跟粗排联系更紧密 3）model serving的时候，更强调client and server colocate的情形，不适合我们的精排场景

2.目前工业界主要使用Ray的方式分两种，一是用Ray的上游生态lib，二是用Ray的底层能力深入自研框架

（1）Ray的上游生态：

- 强化学习库(RLLib)
- 超参调优库(Tune):  支持任意ML框架：PyTorch，XGBoost， MXNet， Keras，集成了很多优化器的库和算法， 通过TensorBoard做显示，可以和Ray Serve无缝结合
- Training with RaySGD: 优势在于能和其它Ray lib无缝结合，并且实现了分布式的dataset

（2）Ray的底层能力：大厂结合Ray自研框架的lecture：[蚂蚁金服Ray Forward推广](https://tech.antfin.com/community/activities/698/review)

3.Ray对应于我们系统中的多个层次，它的底层能力对应于资源管理层REAM (包括Flink, Yarn等)，上游生态对应于我们的LagrangeX

4.最值得我们借鉴的地方有哪些？

底层：

- Ray实现了高效的系统间数据传输， "在底层hack了python的内存对象，和Redis内存共享，实现Numpy、Pandas等数据格式序列化/反序列化时候zero-copy，没有损耗"，是否可以引入这一思想减小我们model serving/training过程中序列化/反序列化的开销
- Ray的结构非常优雅，global scheduler调度全部任务，local scheduler调度同一Node内共享内存的worker，object store支持Node之间的通信。

易用性：

Ray是用户友好的分布式计算框架，具体体现在

1）轻量级的API，几乎不提高代码复杂性。只用在函数前加`@ray.remote`，就能通过remote调用，使task在其它ray集群执行。

2）支持ray dashboard，利于debugging and profiling



官方doc：https://docs.ray.io/en/latest/installation.html

开源史海钩沉系列 [1] Ray：分布式计算框架 - 高策的文章 - 知乎 https://zhuanlan.zhihu.com/p/104022670


**读论文**： 《Ray: A Distributed Framework for Emerging AI Applications》, OSDI 18

结合Bulk-synchronous parallel systems和Task-parallel systems这两类系统

无状态和有状态

- In contrast stateful computations are a good fit for implementing parameter servers, performing repeated computation on GPU-backed data, or running third-party simulators that do not expose their state.

Stateful edges

- embed actors in an otherwise stateless task graph
- enable us to maintain lineage.

![img](Distributed-Systems/ray-graph.png)

The system layer consists of three major components: a global control store, a distributed scheduler, and a distributed object store. 

![img](Distributed-Systems/ray-system.png)

- GCS让系统的任何成分都是stateless的 ，支持fault tolerance，makes it easy to scale the distributed object store and scheduler independently
- 调度的分层，有助于scaling，先由local scheduler调度，只有overload的情形，才会给global scheduler

##### code reading

**读源码：**https://www.qtmuniao.com/2019/07/28/ray-source-reading-1/

![img](Distributed-Systems/ray-state.png)

src/ray/common/task/scheduling_resources.cc

- ResourceSet
- ResourceIds
- ResourceIdSet
- SchedulingResources

src/ray/raylet/scheduling_queue.cc

- TaskQueue
- SchedulingQueue

src/ray/raylet/scheduling_policy.cc

##### 应用

* 「LLM-MLSys」—— 分布式Agent



#### [Jeff Dean: Achieving Rapid Response Times in Large Online Services](https://storage.googleapis.com/pub-tools-public-publication-data/pdf/44875.pdf)

* 讨论了分布式服务的通用优化思想，很值得学习！
  * shared environment 提升资源利用率的同时，也带来不可预测的因素（比如network congestion、background activities、bursts of foreground activity、not just your jobs, but everyone else’s jobs, too），影响服务长尾延时，并且会 exacerbated by large fanout systems

Conclusion

* Tolerating variability
  * important for large-scale online services
  * large fanout magnifies importance
  * makes services more responsive
  * saves significant computing resources
* Collection of techniques
  * general good engineering practices
    * prioritized server queues, careful management of background activities
  * cross-request adaptation
    * load balancing, micro-partitioning
  * within-request adaptation
    * backup requests, backup requests w/ cancellation, tainted results

#### RobinHood: Tail Latency Aware Caching — Dynamic Reallocation from Cache-Rich to Cache-Poor, OSDI 2018

https://www.usenix.org/conference/osdi18/presentation/berger

* 常规的长尾延迟优化思路
  * 负载均衡、动态扩缩容、aggregation server
    * State-of-the-art caching systems focus on hit ratio, fairness — not the P99
  * 以上方法无法解决长尾，本质原因是 p99 latency 有以下特点：
    * 后端间不均衡
    * 可能与请求属性、cache hit rate无关
    * 依赖多变的请求结构
  * 本论文的方法与上述方法是 orthogonal 的

* 常规的cache优化思路倾向于优化hit rate ~ latency avg、miss cost ~ retrieval latency，而本篇论文 Track “request blocking count” (RBC) for each backend，这个 metrics 直接描述长尾 latency p99
  * RBC: 先选定 request set S (延迟在 P98.5 和 P99.5 之间的请求)，再 per backend 地统计大小

* RobinHood Controller
  * ingests RBC
  * calculates / enforces cache allocation
  * fault tolerance
    * not on request path
    * RBC servers store only soft state (aggregated RBC from the last one million requests, in a ring buffer)
* 其它思路
  * delay of reallocating cache space
    * 引申至双层cache：热cache的内存只增不减，概率插入；冷cache有淘汰
* Measurement
  * query hit/miss 时的性能都有不小的损失（Section 5.6）

* Discussion
  * Non-convex miss curves
  * Scaling RobinHood to more backend systems and higher request rates
  * Interdependent backends
  * Multiple webservices with shared backends
  * Scenarios where cache repartitioning is not effective
  * Performance goals beyond the P99



#### 支付架构

##### 业务架构

1.线上标准担保交易支付

* Motivation: 信任问题
* 功能：支付、售中退款、打款、售后退款
* 技术细节：
  * 前置收银台
  * 支付核心
    * 和银行通过银联等间接连接、清算记账
    * 担保交易账号
  * 收银核心----pay-decision
* 18～19年备付金上存改革 => 钱从在某些银行开设的备付金账户到了人行ACS账户中，区别在于后者不能产生利息 => 尽量让钱到网商银行、余额宝中

2.线上合并支付

3.线下支付

* 整体和担保交易大同小异：1）少了前置收银台；2）多了协议支付组件；3）和花呗交互
* 内部支付工具（比如花呗、余额宝）的决策能力强

4.信用卡

* 传统的“卡户卡模式“（储蓄卡通过中间户头还信用卡）
  * 扣款和提现和银行都是异步交互的，流程非常复杂
  * 断直连后，通过网联/银联和银行交互，涉及流量计费，交互两次比较蠢
* 断直连背景下，利用银联能力做的卡到卡交互能力，简称卡卡

5.余额宝

* Motivation: 为什么用户要留钱

* History：

  * 直销余额宝：18年前，天弘基金，规模巨大，“系统性金融风险” => 拆分
    * 监管：ACS上存、断直连、24h监管备查
    * 国家基础设施，No "Too Big To Fall"

  * 代销余额宝：与具有完整银行资质的网商银行交互，支持了更多货币基金种类（博时、中欧等，货币基金比债券、信托产品安全很多）
    * 依托代销余额宝产生的各类工具/业务：至尊宝、质押、大额数米支付等
    * 依托瑜伽项目打通的网商银行交互能力: 互通、五个二类户、阳光化链路等
    * 以及这些能力交叉产生的可以更加方便支撑的财富业务：理财子公司、信托、余额升级、余额升级余额宝等

##### 技术架构

1.大规模并发方案

* 发展：业务数据分离->数据库读写分离->垂直拆分->水平拆分
* 合并部署

  * 1.0: 多个微服务系统部署在同一个cloud engine
    * rpc交互被封装为deepclone + local call
    * 防止误调用，引入门面系统
    * 缺点：合并系统的运维成本高；共享jvm，缺少资源隔离手段；jvm内存占用上涨，调优困难；由于java thread的缺陷，rpc超时设置不可用
  * 2.0: docker容器化技术，物理机部署+linux网桥等来改善rpc性能
    * 同物理机 > 服务名 + 合并部署后缀 > 原服务名
    * 这种寻址方式可能导致新服务加入灰度发布时雪崩
    * 2.0性能比1.0略低，运维成本低很多
* IDL/LDC，蓝绿发布
* [oceanbase](https://www.oceanbase.com/)

  * ob对蚂蚁业务的主要定制点在于：大部分支付数据都是写多读少，并且几乎没有删除操作。针对这类业务特点，ob定义了基准数据和增量数据的概念。历史上的大量基准数据存在于持久化设备上，而增量数据存在于内存等快速访问介质中，并通过定时的“合并”操作将内存数据和基准数据持久化。
* Ob 0.5: UpdateServer是瓶颈；sql语法、数据库特性缺失
    * 参考文件：[OceanBase 0.5 描述.pdf]
  * Ob 1.0: paxos, RootService+PartitionService
    * 同城三机房（服务关键库）、三地五中心（跨城事务耗时）
* 分布式事务
  * “幂等”机制达成一致性，比如A系统重试一遍B系统来检查上一次请求是否成功
  * 流程
    * 一阶段：提交/回滚本地事务
    * 二阶段：只要提交成功，调用方不再感知事务状态，完全由xts利用自身的定时任务，保证**最终一致性**，而非强一致性
  * 经典问题事务悬挂，参与者接收到空回滚，解决方案：
    * 30s空回滚控制，指空回滚30s内，事务号不再接受一阶段请求。账务等系统使用这种xts提供的默认机制
    * 空回滚落一条请求记录，后续同事务号再来一阶段的时候，拒绝服务。paycore等系统自己实现了这套控制方法
  * 参考文件：[XTS-支付宝分布式事务学习指南.pdf]



2.高峰期业务优化手段

* 二阶段异步化：高峰期对xts二阶段降级
* 合并支付优化：将拆单工作移动到了xts二阶段进行

#### SRE

##### 方法论

* [运维的核心能力有哪些？](https://www.zhihu.com/question/434646531/answer/2330010074)
  * 站在公司全局角度对资源利用和成本控制的管理
  * 跨应用甚至跨部门的问题排查和梳理，进而带来的架构整理
  * 运维规范的制定

##### Techniques

* [Log Everything All Time](http://highscalability.com/log-everything-all-time)
  * Req id、线上修改log等级
  * 一些logger库优化技巧
  * Map software components to subsystems that are individually controllable, cross application trace levels aren't useful.

##### 运维案例

* [b站崩溃复盘](https://mp.weixin.qq.com/s/nGtC5lBX_Iaj57HIdXq3Qg)
  * lua的gcd实现，动态类型语言，输入"0"

* [That Couldn't Happen To Us... Could It? --- Google SRE](https://catonmat.net/wp-content/uploads/2008/11/thatcouldnthappentous.pdf)
  * machines:admins > 4000:1
  * Example: Powering disks off
    * 机器运维导致数据under replicated
    * But GFS chunk replication ensures no data loss
  * Example: Protecting data with checksums
  * The implementation is important
    * IP checksum protects only the header
    * TCP checksums are only 16 bits
    * If Ethernet frames are modified as they pass through a device, the CRC is recomputed
    * What about the possibility of data corruption while in the network device?
  * Both of our example problems feature interactions between hardware and software design
    * double-bit flips
  * Lessons Learned
    * Devise testing strategies that cut across every type of variability
    * Automation saves a lot of manual effort, but it's a bigger hammer
      * It hurts more when you whack your thumb with it
    * Redundancy prevented data loss and end-user impact in each case
      * Redundancy and transparent fail-over at (or above) every level is essential

* 

### TODO

* 《Streaming System》 https://mp.weixin.qq.com/s/Uivs5oKCTOqtEGPZZooKTg
