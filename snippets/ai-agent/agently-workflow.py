!pip install openai langgraph Agently==3.3.4.5 mermaid-python nest_asyncio

- https://github.com/Maplemx/Agently
- https://agently.cn/guides/workflow/index.html
- Mermaid在线渲染网站：[mermaid.live](https://mermaid.live/)
- 手绘风格流程图在线编辑：[excalidraw.com](https://excalidraw.com/)


### Intro

相比langgraph，设计了端点
圆括号，不需要手动写链式表达的换行


### usage

@workflow.chunk()
def add_one(inputs, storage):
	num = inputs["default"]
	num += 1
	return num

@workflow.chunk()
def echo(inputs, storage):
	return inputs["default"]

@workflow.chunk()
def print_inputs(inputs, storage):
	print(inputs)
	return

workflow.connect_to("add_one").connect_to("print_inputs.add_one_input")
workflow.connect_to("echo").connect_to("print_inputs.echo")
workflow.chunks["print_inputs"].connect_to("END")

workflow.start(1)
print(workflow.draw())



### baseline

from ENV import deep_seek_url, deep_seek_api_key, deep_seek_default_model
import Agently
agent = (
    Agently.create_agent()
        .set_settings("current_model", "OAIClient")
        .set_settings("model.OAIClient.url", deep_seek_url)
        .set_settings("model.OAIClient.auth", { "api_key": deep_seek_api_key })
        .set_settings("model.OAIClient.options", { "model": deep_seek_default_model })
)

result = agent.input(input("[请输入您的要求]: ")).start()
print("[回复]: ", result)



### workflow

workflow = Agently.Workflow()

@workflow.chunk()
def user_input(inputs, storage):
    storage.set("user_input", input("[请输入您的要求]: "))
    return

@workflow.chunk()
def judge_intent_and_quick_reply(inputs, storage):
    result = (
        agent
            .input(storage.get("user_input"))
            .output({
                "user_intent": ("闲聊 | 售后问题 | 其他", "判断用户提交的{input}内容属于给定选项中的哪一种"),
                "quick_reply": (
                    "str",
"""如果{user_intent}=='闲聊'，那么直接给出你的回应；
如果{user_intent}=='售后问题'，那么请用合适的方式告诉用户你已经明白用户的诉求，安抚客户情绪并请稍等你去看看应该如何处理；
如果{user_intent}=='其他'，此项输出null""")
            })
            .start()
    )
    storage.set("reply", result["quick_reply"])
    return result["user_intent"]

@workflow.chunk()
def generate_after_sales_reply(inputs, storage):
    storage.set("reply", (
        agent
            .input(storage.get("user_input"))
            .instruct(
"""请根据{input}的要求，以一个专业客户服务人员的角色给出回复，遵循如下模板进行回复：
亲爱的客户，感谢您的耐心等待。
我理解您希望{{复述客户的要求}}，是因为{{复述客户要求提出要求的理由}}，您的心情一定非常{{阐述你对客户心情/感受的理解}}。
{{给出对客户当前心情的抚慰性话语}}。
我们会尽快和相关人员沟通，并尽量进行满足。请留下您的联系方式以方便我们尽快处理后与您联系。
"""
)
            .start()
    ))
    return

@workflow.chunk()
def generate_other_topic_reply(inputs, storage):
    storage.set("reply", "我们好像不应该聊这个，还是回到您的问题或诉求上来吧。")
    return

@workflow.chunk_class()
def reply(inputs, storage):
    print("[回复]: ", storage.get("reply"))
    return

(
    workflow
        .connect_to("user_input")
        .connect_to("judge_intent_and_quick_reply")
        .if_condition(lambda return_value, storage: return_value=="闲聊")
            .connect_to("@reply")
            .connect_to("end")
        .elif_condition(lambda return_value, storage: return_value=="售后问题")
            .connect_to("@reply")
            .connect_to("generate_after_sales_reply")
            .connect_to("@reply")
            .connect_to("user_input")
        .else_condition()
            .connect_to("generate_other_topic_reply")
            .connect_to("@reply")
            .connect_to("END")
)

workflow.start()
pass




### translation agent

import json
from ENV import deep_seek_url, deep_seek_api_key, deep_seek_default_model
import Agently
import os 

# 将模型请求配置设置到agent工厂，后续工厂创建的agent对象都可以继承这个配置
agent_factory = (
    Agently.AgentFactory()
        .set_settings("current_model", "OAIClient")
        .set_settings("model.OAIClient.url", deep_seek_url)
        .set_settings("model.OAIClient.auth", { "api_key": deep_seek_api_key })
        .set_settings("model.OAIClient.options", { "model": deep_seek_default_model })
)

# 创建工作流
workflow = Agently.Workflow()

# 定义关键处理节点
## 首次翻译
# @workflow.chunks["initial_translation"]
# @workflow.chunk(id="init_translation")
@workflow.chunk()
def initial_translation(inputs, storage):
    source_lang = storage.get("source_lang")
    target_lang = storage.get("target_lang")
    source_text = storage.get("source_text")

    # 创建一个翻译agent来执行任务
    translate_agent = agent_factory.create_agent()
    
    # 给翻译agent设置system信息
    translate_agent.set_agent_prompt(
        "role",
        f"You are an expert linguist, specializing in translation from {source_lang} to {target_lang}."
    )

    # 向翻译agent发起翻译任务请求
    translation_1 = (
        translate_agent
        .input(
f"""This is an {source_lang} to {target_lang} translation, please provide the {target_lang} translation for this text. \
Do not provide any explanations or text apart from the translation.
{source_lang}: {source_text}

{target_lang}:"""
        )
        .start()
    )

    # 保存翻译结果
    storage.set("translation_1", translation_1)
    # 保存翻译agent备用
    storage.set("translate_agent", translate_agent)
    return {
        "stage": "initial translation",
        "result": translation_1
    }

## 反思优化
@workflow.chunk()
def reflect_on_translation(inputs, storage):
    source_lang = storage.get("source_lang")
    target_lang = storage.get("target_lang")
    source_text = storage.get("source_text")
    country = storage.get("country", "")
    translation_1 = storage.get("translation_1")

    # 创建一个反思agent来执行任务
    reflection_agent = agent_factory.create_agent()

    # 给反思agent设置system信息
    reflection_agent.set_agent_prompt(
        "role",
        f"You are an expert linguist specializing in translation from {source_lang} to {target_lang}. \
You will be provided with a source text and its translation and your goal is to improve the translation."
    )

    additional_rule = (
        "The final style and tone of the translation should match the style of {target_lang} colloquially spoken in {country}."
        if country != ""
        else ""
    )

    # 向反思agent发起反思任务
    reflection = (
        reflection_agent
            .input(
f"""Your task is to carefully read a source text and a translation from {source_lang} to {target_lang}, and then give constructive criticism and helpful suggestions to improve the translation. \
{additional_rule}

The source text and initial translation, delimited by XML tags <SOURCE_TEXT></SOURCE_TEXT> and <TRANSLATION></TRANSLATION>, are as follows:

<SOURCE_TEXT>
{source_text}
</SOURCE_TEXT>

<TRANSLATION>
{translation_1}
</TRANSLATION>

When writing suggestions, pay attention to whether there are ways to improve the translation's \n\
(i) accuracy (by correcting errors of addition, mistranslation, omission, or untranslated text),\n\
(ii) fluency (by applying {target_lang} grammar, spelling and punctuation rules, and ensuring there are no unnecessary repetitions),\n\
(iii) style (by ensuring the translations reflect the style of the source text and takes into account any cultural context),\n\
(iv) terminology (by ensuring terminology use is consistent and reflects the source text domain; and by only ensuring you use equivalent idioms {target_lang}).\n\

Write a list of specific, helpful and constructive suggestions for improving the translation.
Each suggestion should address one specific part of the translation.
Output only the suggestions and nothing else."""
            )
            .start()
    )

    # 保存反思结果
    storage.set("reflection", reflection)
    return {
        "stage": "reflection",
        "result": reflection
    }

## 二次翻译
@workflow.chunk()
def improve_translation(inputs, storage):
    source_lang = storage.get("source_lang")
    target_lang = storage.get("target_lang")
    source_text = storage.get("source_text")
    translation_1 = storage.get("translation_1")
    reflection = storage.get("reflection")

    # 使用保存下来的翻译agent
    translate_agent = storage.get("translate_agent")

    # 直接发起二次翻译任务
    translation_2 = (
        translate_agent
            .input(
f"""Your task is to carefully read, then edit, a translation from {source_lang} to {target_lang}, taking into
account a list of expert suggestions and constructive criticisms.

The source text, the initial translation, and the expert linguist suggestions are delimited by XML tags <SOURCE_TEXT></SOURCE_TEXT>, <TRANSLATION></TRANSLATION> and <EXPERT_SUGGESTIONS></EXPERT_SUGGESTIONS> \
as follows:

<SOURCE_TEXT>
{source_text}
</SOURCE_TEXT>

<TRANSLATION>
{translation_1}
</TRANSLATION>

<EXPERT_SUGGESTIONS>
{reflection}
</EXPERT_SUGGESTIONS>

Please take into account the expert suggestions when editing the translation. Edit the translation by ensuring:

(i) accuracy (by correcting errors of addition, mistranslation, omission, or untranslated text),
(ii) fluency (by applying {target_lang} grammar, spelling and punctuation rules and ensuring there are no unnecessary repetitions), \
(iii) style (by ensuring the translations reflect the style of the source text)
(iv) terminology (inappropriate for context, inconsistent use), or
(v) other errors.

Output only the new translation and nothing else."""
            )
            .start()
    )

    # 保存二次翻译结果
    storage.set("translation_2", translation_2)
    return {
        "stage": "improve translation",
        "result": translation_2
    }


# 连接工作块
# workflow == workflow.chunks["START"]
# workflow.chunks["initial_translation"].handle("output_handle").connect_to(...)
(
    workflow
        .connect_to("initial_translation")
        .connect_to("reflect_on_translation")
        .connect_to("improve_translation")
        .connect_to("end")
)

# 添加过程输出优化
# @表示是一个临时块    .connect_to("@output_stage_result") 相当于 .connect_to(output_stage_result)
@workflow.chunk_class()
def output_stage_result(inputs, storage):
    print(f"[{ inputs['default']['stage'] }]:\n", inputs["default"]["result"])
    return

(
    workflow.chunks["initial_translation"]
        .connect_to("@output_stage_result")
        .connect_to("reflect_on_translation.wait")
)
(
    workflow.chunks["reflect_on_translation"]
        .connect_to("@output_stage_result")
        .connect_to("improve_translation.wait")
)
(
    workflow.chunks["improve_translation"]
        .connect_to("@output_stage_result")
)

# 启动工作流
result = workflow.start(storage = {
    "source_lang": "English",
    "target_lang": "中文",
    "source_text": """Translation Agent: Agentic translation using reflection workflow
This is a Python demonstration of a reflection agentic workflow for machine translation. The main steps are:

Prompt an LLM to translate a text from source_language to target_language;
Have the LLM reflect on the translation to come up with constructive suggestions for improving it;
Use the suggestions to improve the translation.
Customizability
By using an LLM as the heart of the translation engine, this system is highly steerable. For example, by changing the prompts, it is easier using this workflow than a traditional machine translation (MT) system to:

Modify the output's style, such as formal/informal.
Specify how to handle idioms and special terms like names, technical terms, and acronyms. For example, including a glossary in the prompt lets you make sure particular terms (such as open source, H100 or GPU) are translated consistently.
Specify specific regional use of the language, or specific dialects, to serve a target audience. For example, Spanish spoken in Latin America is different from Spanish spoken in Spain; French spoken in Canada is different from how it is spoken in France.
This is not mature software, and is the result of Andrew playing around with translations on weekends the past few months, plus collaborators (Joaquin Dominguez, Nedelina Teneva, John Santerre) helping refactor the code.

According to our evaluations using BLEU score on traditional translation datasets, this workflow is sometimes competitive with, but also sometimes worse than, leading commercial offerings. However, we’ve also occasionally gotten fantastic results (superior to commercial offerings) with this approach. We think this is just a starting point for agentic translations, and that this is a promising direction for translation, with significant headroom for further improvement, which is why we’re releasing this demonstration to encourage more discussion, experimentation, research and open-source contributions.

If agentic translations can generate better results than traditional architectures (such as an end-to-end transformer that inputs a text and directly outputs a translation) -- which are often faster/cheaper to run than our approach here -- this also provides a mechanism to automatically generate training data (parallel text corpora) that can be used to further train and improve traditional algorithms. (See also this article in The Batch on using LLMs to generate training data.)

Comments and suggestions for how to improve this are very welcome!"""
})

print(workflow.draw())

# 打印执行结果
#print(workflow.storage.get("translation_1"))
#print(workflow.storage.get("reflection"))
#print(workflow.storage.get("translation_2"))
print(json.dumps(result, indent=4, ensure_ascii=False))
