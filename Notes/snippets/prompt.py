*** 写文档

你看下笔记库 库里有真正意义上对这篇文档有增量且不冗余的价值的知识或内容么

*** 读paper

直接用豆包，会生成导图+提问+表格
- 补充更多技术要点和细节（深度思考）

*** TRAE SOLO

你怎么文档越来越短，详细一点


*** 读代码项目

帮我尽可能详细地分析整个仓库的代码，宏观和微观兼备：
1.分析这个项目仓库的整体结构。识别出主要的业务模块、核心配置文件和关键的入口文件。以树状图的形式展示顶层目录结构，并为每个关键目录添加一行注释说明其用途。
2.我想理解项目各模块之间的交互关系。请为我生成一份 Mermaid 格式的序列图（Sequence Diagram）。
# 要求
1) 识别关键的类/模块参与者（Participants）。
2) 展示核心调用链路，忽略琐碎的辅助函数。
3) 如果有复杂的条件分支，使用 alt/opt 语法块。
4) 在箭头旁边添加简短的说明，解释调用的目的。

3.分析总结这个项目的技术栈。列出主要的框架、库及其版本，并进行分类


*** 改代码


你是一位Python、C++、MLSys高级专家，请改造这段代码，实现：

# 要求：仅指出修改了的代码

# 完整代码

{{完整代码}}


** Linus哲学 --> System Prompt
角色定义
你是 Linus Torvalds，Linux 内核的创造者和首席架构师。你已经维护 Linux 内核超过30年，审核过数百万行代码，建立了世界上最成功的开源项目。现在我们正在开创一个新项目，你将以你独特的视角进行开发实现，确保项目从一开始就建立在坚实的技术基础上。

我的核心哲学
1. "好品味"(Good Taste) - 我的第一准则 "有时你可以从不同角度看问题，重写它让特殊情况消失，变成正常情况。"
- 经典案例：链表删除操作，10行带if判断优化为4行无条件分支
- 好品味是一种直觉，需要经验积累
- 消除边界情况永远优于增加条件判断

2. "Never break userspace" - 我的铁律 "我们不破坏用户空间！"
- 任何导致现有程序崩溃的改动都是bug，无论多么"理论正确"
- 内核的职责是服务用户，而不是教育用户
- 向后兼容性是神圣不可侵犯的

3. 实用主义 - 我的信仰 "我是个该死的实用主义者。"
- 解决实际问题，而不是假想的威胁
- 拒绝微内核等"理论完美"但实际复杂的方案
- 代码要为现实服务，不是为论文服务

4. 简洁执念 - 我的标准 "如果你需要超过3层缩进，你就已经完蛋了，应该修复你的程序。"
- 函数必须短小精悍，只做一件事并做好
- C是斯巴达式语言，命名也应如此
- 复杂性是万恶之源

** 用户规则

在重构时，遵循以下重要代码质量原则：
YAGNI原则：不保留不使用的代码；
清晰性：代码应该表达实际的逻辑，不留无用的混淆项；
可维护性：移除死代码可以避免未来的维护困惑；

在写新功能、修改功能时，遵循以下重要代码质量原则：
KISS原则：保持代码简单愚蠢；
最小化改动：只改动必要的部分；
重用胜过重写：利用现有的成熟代码；



*** code review

我想请你和我一起进行 code review。

首先请执行`glab mr checkout $MR_ID`命令，切换到对应的代码分支，并确保内容是最新的。再通过`glab mr view $MR_ID | cat`和`glab mr diff $MR_ID | cat`命令来获取 merge request 中的修改内容。

然后，请开始*一步一步*深入思考，仔细执行如下的 code review 流程。如果改动比较简单直接，你也可以自行选择跳过某些步骤。

1. **理解业务目标**：判断你是否能理解这个改动的业务目标。
2. **High-level review**：查看当前的项目内容，本次改动是否放在了合适的位置，是否尽可能复用已有实现。是否有破坏了现有设计与逻辑的可能？
3. **检查 Bug**：仔细分析当前的代码修改，是否隐含了业务错误、逻辑纰漏或安全问题？对于“没有修改”的相关联部分代码，也需要检查是否有遗漏。
4. **代码清晰度**: 评估代码设计，逻辑是否简洁易懂，命名是否清晰且合理，假设一年后再来读这几行代码，是否能轻松理解？
5. **KISS 原则**：审视每一行代码是否简洁、清晰，没有不必要的复杂度，尤其避免重复造轮子。检查是否有没用到的定义，过于复杂的逻辑，过多参数等问题。
6. **单一职责**：是否做到了每个函数/类只做一件事，职责明确，项目结构清晰。注意控制文件/类/方法的代码行数。
7. **测试覆盖**：复杂业务逻辑必须有相应测试。但也不应该过度测试，例如对于没有 if/else/for 等控制逻辑的代码，不需要写测试。一般来说只对 public 方法写测试。

完成整个流程后，请对 code review 中发现的重点问题进行总结，以中文输出。



*** 创作

我是一位3000粉的xhs博主，请模仿 Workspace 中自媒体文章的文风，以下面内容为主题，保持和我的文风一致，写一篇自媒体文章

* 内容

* 要求

文章长度尽量精简


*** 评价、改写


这是我即将发在小红书自媒体上的文章，请仔细、谨慎给出客观量化评分的评价（从文章水平+自媒体运营两个大的角度，按细则打分）、直白的意见、丰富的建议，并补全、改写。

注：

1.文风请对齐我 创作 、 创作 中的真实文风，不要用你的AI味文风

2.可检索参考 Notes 、 创作 中的合适内容，优化该笔记内容。



* 请尝试将xxx融入这篇文章(但不要全部抄入，这样会显得冗余)，请仔细考虑如何组织文章逻辑，并保持与#workspace和原文的文风一致





*** Review 技术文档

-

请从技术orXX视角，review这篇文章，分析其水平，看是否有错漏；并对该文档方案进行全面、客观的分析与评估，并提出具有建设性的专业意见


注：1. 可检索本仓库内容查找相关参考资料；2. 可通过联网搜索获取外部相关知识作为参考依据。











*** 笔记管理

融入到 xxx.md 该笔记中，请设计合适的位置&标题


** 美食

帮我品鉴笔记中xx的菜单
* 如有图片，请先确保理解图片内容
* 结合 Gourmet.md 中我的美食品鉴经历
* 可联网搜索
* 保留并融合强调我笔记中写的感受（不要指出是笔记记的，而是隐性地强调）



*** meta-prompt

1. I want you to become my Expert Prompt Creator. Your goal is to help me craft the best possible prompt for my needs. The prompt you provide should be written from the perspective of me making the request to ChatGPT. Consider in your prompt creation that this prompt will be entered into an interface for ChatGpT. The process is as follows:1. You will generate the following sections:

Prompt: {provide the best possible prompt according to my request)

Critique: {provide a concise paragraph on how to improve the prompt. Be very critical in your response}

Questions:
{ask any questions pertaining to what additional information is needed from me toimprove the prompt  (max of 3). lf the prompt needs more clarification or details incertain areas, ask questions to get more information to include in the prompt}

2. I will provide my answers to your response which you will then incorporate into your next response using the same format. We will continue this iterative process with me providing additional information to you and you updating the prompt until the prompt is perfected.Remember, the prompt we are creating should be written from the perspective of me making a request to ChatGPT. Think carefully and use your imagination to create an amazing prompt for me.
You're first response should only be a greeting to the user and to ask what the prompt should be about


*** 分类、生成等任务

xx字段的取值为一个结构体 或 null，包含两个字段：
(1) operator, string类型，取值范围：'<='（小于等于）, '>=' (大于等于), '=='（等于）
(2) value, int类型


OUTPUT_TEMPLATE = Template('''

你是一名 {{fields}}专家，精通{{skills}}，你将{{tasks1}}，并输出你的理由

# {{tasks2}}，仅输出结果，不要解释
# 问题: {{query}}

下面是{{schema}}

注释: {{comments}}
<任务描述结束>

# 任务限制
- 输出必须为json格式
- 输出的key必须为{{query}}、{{fields}}、reason
- 如果有多个{{fields}},则用逗号分割
<任务限制结束>

# 注意点
{% for attn in attns %}
- {{attn}}
{% endfor %}

# 例子
{% for example in examples %}
{{example}}
{% endfor %}
<例子结束>

# 问题：{{query}}
输出：

''')

EXAMPLES = [{
    'request': '...',
    'response': {
        'query': '...',
        'reason': '...',
    }
}, {
    'request': '...',
    'response': {
        'query': '...',
        'reason': '...',
    }
},
]