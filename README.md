## CS-Notes

### 2021年版Intro

* 我的自学笔记，在学习MLSys和C++，整理算法、操作系统，后续学习分布式系统，终身更新。
* 我不是贵系oi出身的大神，目前在以一个初学者的心态补习计算机知识，学习路径和心得可能更值得大家借鉴。

### 2025年版Intro

* 笔记的 AI 自动化管理，参考 .trae/documents 文件夹中的内容
* 多了太多内容，无从谈起，建议看目录。

### 笔记目录

笔记按主题分层，文件都在 `Notes/` 下（同名子目录存放该笔记的图片与资源）。

- **计算机基础**
  - **操作系统与系统**
    - [APUE](Notes/APUE.md) / [OSTEP](Notes/OSTEP-Operating-Systems-Three-Easy-Pieces.md)
    - [Linux多线程服务端编程-muduo](Notes/Linux多线程服务端编程-muduo.md) / [操作系统](Notes/操作系统.md)
    - [CSAPP](Notes/CSAPP.md) / [CSAPP-Labs](Notes/CSAPP-Labs.md) / [Shell-MIT-6-NULL](Notes/Shell-MIT-6-NULL.md)
    - [Computer-Architecture](Notes/Computer-Architecture.md) / [Assembly](Notes/Assembly.md) / [Compiling](Notes/Compiling.md) / [Metaprogramming](Notes/Metaprogramming.md)
  - **网络与通信**
    - [通信与网络](Notes/通信与网络.md)
    - [CS144-Lab](Notes/Computer-Networking-Lab-CS144-Stanford.md) / [CS144-Lecture](Notes/Computer-Networking-Lecture-CS144-Stanford.md)
- **算法与编程**
  - [Algorithms-Potpourri](Notes/Algorithms-Potpourri.md) / [leetcode题目简评](Notes/leetcode题目简评.md)
  - [code-reading](Notes/code-reading.md)
  - [设计模式-《剑指offer》笔记](Notes/设计模式-《剑指offer》笔记.md)
- **编程语言与工具**
  - [C++](Notes/C++.md) / [Go](Notes/Go.md) / [java](Notes/java.md) / [python](Notes/python.md)
  - [Rust](Notes/Rust.md) / [TypeScript](Notes/TypeScript.md) / [Functional-Programming](Notes/Functional-Programming.md)
  - [regex](Notes/regex.md) / [protobuf等基本工具](Notes/protobuf等基本工具.md)
  - [git](Notes/git.md) / [Editor](Notes/Editor.md) / [Debugging-and-Profiling](Notes/Debugging-and-Profiling.md)
- **数据与分布式**
  - [Database](Notes/Database.md)
  - [Distributed-Systems](Notes/Distributed-Systems.md)
- **AI / 机器学习**
  - **基础与算法**
    - [Machine-Learning](Notes/Machine-Learning.md) / [AI-Algorithms](Notes/AI-Algorithms.md) / [AI-Applied-Algorithms](Notes/AI-Applied-Algorithms.md)
    - [深度学习推荐系统](Notes/深度学习推荐系统.md) / [计算广告](Notes/计算广告.md)
    - [Reinforcement-Learning](Notes/Reinforcement-Learning.md) / [Federated-Learning](Notes/Federated-Learning.md)
  - **大模型与系统**
    - [LLM-MLSys](Notes/LLM-MLSys.md) / [MLSys+RecSys](Notes/MLSys+RecSys.md)
    - [GPU](Notes/GPU.md) / [pytorch](Notes/pytorch.md) / [tensorflow](Notes/tensorflow.md)
    - [AI-Agent-Engineering](Notes/AI-Agent-Engineering.md) / [AI-Agent-Product&PE](Notes/AI-Agent-Product&PE.md)
- **软件工程与开源**
  - [Software-Engineering](Notes/Software-Engineering.md) / [Software-开源项目成功之道](Notes/Software-开源项目成功之道.md)
  - [Web-基础](Notes/Web-基础.md) / [云原生-ToB](Notes/云原生-ToB.md)
  - [Security-Privacy-Cryptography](Notes/Security-Privacy-Cryptography.md)
- **通用与生活**
  - [非技术知识](Notes/非技术知识.md) / [文史哲与生活](Notes/文史哲与生活.md)
  - [Anatomy-大脑与神经科学](Notes/Anatomy-大脑与神经科学.md)
  - [Gourmet](Notes/Gourmet.md) / [Health-COVID-19-Prevention](Notes/Health-COVID-19-Prevention.md) / [game-knowledge](Notes/game-knowledge.md)
  - [面试心得体会与转行相关](Notes/面试心得体会与转行相关.md)

### 笔记心得

* 用「子标题」清晰表达结构
* 在「子标题」压缩信息：提炼正文内容

### 关于本仓库

* This repository uses Github as image host, for the simplicity and reliability of backup.
* 顶层目录中，`Notes/` 放长期笔记，`snippets/` 放可复用脚本与代码片段，`prompts/` 放可复用 prompt 资产。
* 本仓库内容由自制[笔记转化器](https://github.com/huangrt01/CS-Notes)自动生成
  * remaining bug: 包含`$`的行会视为latex行内公式转化为公式图片，但这样会将shell代码转换，需要判断是否在latex代码域内，予以排除
  * solution: clone仓库，用[Typora](https://typora.io/)阅读Note文件夹里的本体文件
* 内推字节AML团队，请联系 huangrt01@163.com

### 社交媒体

* [小红书](https://www.xiaohongshu.com/user/profile/5cb7c5bf00000000160120df): 观想人间的一团云，当前3-4k粉丝
* [知乎咨询](https://www.zhihu.com/people/huang-rui-teng)

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=huangrt01/CS-Notes&type=date&legend=top-left)](https://www.star-history.com/#huangrt01/CS-Notes&type=date&legend=top-left)
