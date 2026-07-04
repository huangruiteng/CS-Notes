# JSON Classification Template

适用场景：分类、字段抽取、结构化 JSON 输出。

```jinja
你是一名 {{fields}} 专家，精通 {{skills}}，你将 {{tasks1}}，并输出你的理由。

# {{tasks2}}，仅输出结果，不要解释
# 问题: {{query}}

下面是 {{schema}}

注释: {{comments}}
<任务描述结束>

# 任务限制
- 输出必须为 JSON 格式。
- 输出的 key 必须为 {{query}}、{{fields}}、reason。
- 如果有多个 {{fields}}，则用逗号分割。
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
```

示例数据结构：

```python
EXAMPLES = [
    {
        "request": "...",
        "response": {
            "query": "...",
            "reason": "...",
        },
    },
    {
        "request": "...",
        "response": {
            "query": "...",
            "reason": "...",
        },
    },
]
```
