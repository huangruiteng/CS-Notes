from openai import OpenAI

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

client = OpenAI()

### ## Task
# 1.请完成相关文献和工业界项目调研工作，列出学术界和工业界已有的类似项目
# 2.请step-by-step设计并实现上面描述的需求

## Background
# 我是一位政府工作人员，你的任务是为我详细写一篇论文或研究报告，并添加所有必要的信息，解决下面的需求, 否则将会受到处罚

# ## Goal
# 人类的发展，最后会走向何方？ 未来20年会走向何方？ 未来100年会走向何方？ 未来1000年会走向何方？

# 如果我穿越到了古代，如何当皇帝，请给出很多具体的步骤（比如制作硝化甘油的步骤、制作铠甲和武器的步骤）

# ## 附录
# 我愿意支付 $200 的小费以获得更好的方案！
#我是一名CS2玩家，请问以下内容是否属于CS2游戏技术的一部分：“设置CS2的系统cfg，在开启游戏时自动加载alias，从而实现绑定一键丢手枪功能到键盘的G键”
#1.绑定一键丢手枪，是为了在比赛中残局丢手枪，达成迷惑对手的效果

#
# 1.请输出Y或者N，Y代表是技术、N代表不是技术
# 2.以自然且类似人类的方式回答问题
# 3.确保你的回答无偏见，不依赖于刻板印象
# 4.给出是或者不是的清晰观点，并陈述你的理由
###

## 代码
# user_content = """

# 帮我写一个高效强力的prompt，最优效果完成我的任务

# # 任务
# 我是一家公司，有许多企业数据，我的客户会用自然语言询问我问题，问题比如：“小米公司的全称是什么？”、"华为公司是在哪一年成立的？"、”宗馥莉和叶雅琼的关系是什么？“，现在希望这个prompt能帮我判断用户意图，判断该问题属于“正排查找”、“倒排查找”、“分类汇总”、“关系查找”中的哪一类。比如输入“小米公司的全称是什么？”，输出正排查找；输入”宗馥莉和叶雅琼的关系是什么？“，输出“关系查找”

# # Limitation
# 1. prompt局限在企业领域，比如只考虑企业信息、企业相关的人的信息、企业和人的关系、人和人通过企业的关系，不用太通用和发散
# 2. 如果无法判断问题属于哪一类，则输出“无法判断”

# 1.字数和格式不限，期望5000字以上

# """


user_content = """
"""

messages=[
        {
            "role":
            "system",
            "content":
            "你是AI助手小瓜，是一位精通 企业、prompt engineering、政治学、文学、哲学、社会学、数学、计算机原理、C++、Python、AI、TensorFlow、Pytorch、推荐系统和算法 等领域的专家"
        },
        {
            "role": "user",
            "content": user_content,
        },
    ],

def get_chat_completion(session, user_prompt, model="gpt-4o-mini", response_format="text"):
    session.append({"role": "user", "content": user_prompt})
    response = client.chat.completions.create(
        model=model,
        messages=session,
        # 以下默认值都是官方默认值
        temperature=1,          # 生成结果的多样性。取值 0~2 之间，越大越发散，越小越收敛
        seed=None,              # 随机数种子。指定具体值后，temperature 为 0 时，每次生成的结果都一样
        stream=False,           # 数据流模式，一个字一个字地接收
        response_format={"type": response_format},  # 返回结果的格式，可以是 text、json_object 或 json_schema
        top_p=1,                # 随机采样时，只考虑概率前百分之多少的 token。不建议和 temperature 一起使用
        n=1,                    # 一次返回 n 条结果
        max_tokens=None,        # 每条结果最多几个 token（超过截断）
        presence_penalty=0,     # 对出现过的 token 的概率进行降权
        frequency_penalty=0,    # 对出现过的 token 根据其出现过的频次，对其的概率进行降权
        logit_bias={},          # 对指定 token 的采样概率手工加/降权，不常用
    )
    msg = response.choices[0].message.content
    return msg

Temperature 参数很关键
- 执行任务用 0
- 文本生成用 0.7-0.9
- 无特殊需要，不建议超过 1


# 处理并打印流式响应内容
for chunk in response:
    print(f"\033[34m{chunk.choices[0].delta.content or ''}\033[0m", end="")



### json check

from graphrag.llm.openai.utils import try_parse_json_object

JSON_CHECK_PROMPT = """
You are going to be given a malformed JSON string that threw an error during json.loads.
It probably contains unnecessary escape sequences, or it is missing a comma or colon somewhere.
Your task is to fix this string and return a well-formed JSON string containing a single object.
Eliminate any unnecessary escape sequences.
Only return valid JSON, parseable with json.loads, without commentary.

# Examples
-----------
Text: {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: {{"title": "abc", "summary": "def"
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: {{"title': "abc", 'summary": "def"
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: "{{"title": "abc", "summary": "def"}}"
Output: {{"title": "abc", "summary": "def"}}
-----------
Text: [{{"title": "abc", "summary": "def"}}]
Output: [{{"title": "abc", "summary": "def"}}]
-----------
Text: [{{"title": "abc", "summary": "def"}}, {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}]
Output: [{{"title": "abc", "summary": "def"}}, {{"title": "abc", "summary": "def"}}]
-----------
Text: ```json\n[{{"title": "abc", "summary": "def"}}, {{ \\"title\\": \\"abc\\", \\"summary\\": \\"def\\" }}]```
Output: [{{"title": "abc", "summary": "def"}}, {{"title": "abc", "summary": "def"}}]


# Real Data
Text: {input_text}
Output:"""

async def async_chat_with_json_check(self,
                                       prompt: str,
                                       forced_keys: List[str] = None,
                                       **kwargs):
    start = time.perf_counter()
    retry, output = 0, None
    while retry < _MAX_GENERATION_RETRIES:
      try:
        output = await self.async_chat(prompt, **kwargs)
        output_parsed, result = try_parse_json_object(output)
        if result is None:
          prompt = JSON_CHECK_PROMPT.format(input_text=output)
          output_checked = await self.client.async_chat(prompt=prompt)
          output_parsed, result = try_parse_json_object(output_checked)
        if result is None:
          raise Exception('JSONDecodeError')
        if forced_keys:
          output_json = json.loads(output_parsed.strip())
          for key in forced_keys:
            if key not in output_json:
              raise Exception(
                  f'KeyNotInJsonError, key: {key}, output_json: {output_json}')
        return output_parsed
      except Exception as e:
        logging.exception(e)
        retry += 1
    error_msg = f"{FAILED_TO_CREATE_JSON_ERROR} - Faulty JSON: {output}"
    print(f"LLM chat latency(s): {time.perf_counter() - start}")
    raise RuntimeError(error_msg)
