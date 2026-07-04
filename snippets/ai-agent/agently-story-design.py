
# public_storage.进行workflow之间的通讯


import json
from ENV import deep_seek_url, deep_seek_api_key, deep_seek_default_model
import Agently
import os 

# 创建一个作家agent

writer = (
    Agently.create_agent()
        .set_settings("current_model", "OAIClient")
        .set_settings("model.OAIClient.url", os.environ["DEEPSEEK_BASE_URL"])
        .set_settings("model.OAIClient.auth", { "api_key": os.environ["DEEPSEEK_API_KEY"] })
        .set_settings("model.OAIClient.options", { "model": os.environ["DEEP_SEEK_DEFAULT_MODEL"] })
)

# 创建两个工作流：主工作流和分块创作工作流
main_workflow = Agently.Workflow()
block_workflow = Agently.Workflow()

# 定义主工作流的工作块
## 输入一句话描述
@main_workflow.chunk()
def input_story_idea(inputs, storage):
    storage.set("story_idea", input("[💡请输入您的故事灵感]: "))
    return

## 创建世界观背景故事
@main_workflow.chunk()
def generate_background(inputs, storage):
    story_idea = storage.get("story_idea")
    background = (
        writer
            .input({
                "故事灵感": story_idea
            })
            .instruct(
"""请根据{故事灵感}创作故事的世界信息和背景故事，其中：
世界信息需要包括世界的主要国家或地区分布，不同国家或地区的环境描写，科技水平，信仰情况等
世界背景故事需要以时间线的形式描述世界的主要历史沿革，国家或地区之间的重大事件及带来的影响变化等"""
            )
            .output({
                "世界名称": ("str", ),
                "主要国家或地区": [{
                    "名称": ("str", ),
                    "关键信息": ("str", ),
                }],
                "世界背景故事": [("str", )],
            })
            .start()
    )
    storage.set("background", background)
    return {
        "title": "世界观背景故事",
        "result": background,
    }

## 创建关键情节线
@main_workflow.chunk()
def generate_storyline(inputs, storage):
    story_idea = storage.get("story_idea")
    background = storage.get("background")
    storyline = (
        writer
            .input({
                "故事灵感": story_idea,
                "世界观背景故事": background,
            })
            .instruct(
"""请根据{世界观背景故事}，围绕{故事灵感}，创作故事的关键情节线安排"""
            )
            .output({
                "情节结构类型": ("str", "基于常见的故事、小说、剧作创作方法，输出你将要使用的剧情结构类型名称"),
                "情节结构特点": ("str", "阐述{剧情结构类型}的剧情结构手法、特点"),
                "故事线详细创作": [{
                    "本段故事作用": ("str", "描述本段故事在整体结构中发挥的作用"),
                    "关键情节": ([("str", )], "按时序描述本段故事中的关键情节，以及情节中的关键细节"),
                    "涉及关键人物": ([("str", )], "给出本段故事中涉及的关键人物名"),
                }],
            })
            .start()
    )
    storage.set("storyline", storyline)
    return {
        "title": "关键情节线",
        "result": storyline,
    }

## 分发故事段落设计
@main_workflow.chunk()
def send_story_block_list(inputs, storage):
    storyline = storage.get("storyline")
    storyline_details = storyline["故事线详细创作"]
    extra_instruction = input("[您是否还有其他创作指导说明？如创作风格、注意事项等]")
    story_block_list = []
    for item in storyline_details:
        item.update({ "补充创作指导": extra_instruction })
        story_block_list.append(item)
    return story_block_list

## 过程产出输出
@main_workflow.chunk_class()
def print_process_output(inputs, storage):
    print(f"[{ inputs['default']['title'] }]:")
    if isinstance(inputs["default"]["result"], dict):
        print(
            json.dumps(inputs["default"]["result"], indent=4, ensure_ascii=False)
        )
    else:
        print(inputs["default"]["result"])
    return

## 最终结果整理
@main_workflow.chunk()
def sort_out(inputs, storage):
    result = []
    for item in inputs["default"]:
        result.append(item["default"])
    return "\n\n".join(result)

# 定义分块创作工作流的工作块
## 获取初始数据
@block_workflow.chunk()
def init_data(inputs, storage):
    storage.set("story_block", inputs["default"])
    # 从公共存储中取出上一段创作结果
    storage.set("last_block_content", block_workflow.public_storage.get("last_block_content"))
    return

## 进行正文创作
@block_workflow.chunk()
def generate_block_content(inputs, storage):
    # 要考虑的条件较多，可以在请求外部构造input和instruct的prompt数据
    ## 围绕故事线详细创作信息的prompt
    ## {"本段故事作用": ,"关键情节": , "涉及关键人物": , "补充创作指导": }
    input_dict = storage.get("story_block")
    instruction_list = [
        "参考{本段故事作用}及{涉及关键人物}，将{关键情节}扩写为完整的故事",
        "每段故事需要尽量包括行动描写、心理活动描写和对白等细节",
        "每次创作只是完整文章结构中的一部分，承担{本段故事作用}说明的作用任务，只需要按要求完成{关键情节}的描述即可，不需要考虑本段故事自身结构的完整性",
    ]
    
    ## 如果有前一段内容，通过传入前一段内容末尾确保创作的连贯性
    last_block_content = storage.get("last_block_content", None)
    if last_block_content:
        ## 在这里取上一段落的最后50个字，可根据需要修改保留的长度
        keep_length = 50
        input_dict.update({ "上一段落的末尾": last_block_content[(-1 * keep_length):] })
        instruction_list.append("创作时需要承接{上一段落的末尾}，确保表达的连贯性")
    
    ## 如果有人类评判反馈的修改意见，添加prompt
    last_generation = storage.get("block_content", None)
    revision_suggestion = storage.get("revision_suggestion", None)
    if last_generation and revision_suggestion:
        input_dict.update({
            "已有创作结果": last_generation,
            "修改意见": revision_suggestion,
        })
        instruction_list.append("你之前已经创作了{已有创作结果}，但仍然需要修改，请参考{修改意见}进行修订")
    
    # 开始创作
    block_content = (
        writer
            .input(input_dict)
            .instruct(instruction_list)
            .start()
    )

    # 保存创作结果
    storage.set("block_content", block_content)
    return {
        "title": f"本轮创作目标：{ input_dict['本段故事作用'] }",
        "result": block_content,
    }

## 人类判断是否满意
@block_workflow.chunk()
def human_confirm(inputs, storage):
    confirm = ""
    while confirm.lower() not in ("y", "n"):
        confirm = input("[您是否满意本次创作结果？(y/n)]: ")
    return confirm.lower()

## 提交修改意见
@block_workflow.chunk()
def input_revision_suggestion(inputs, storage):
    storage.set("revision_suggestion", input("[请输入您的修改意见]: "))
    return

## 输出满意的创作成果
@block_workflow.chunk()
def return_block_content(inputs, storage):
    block_content = storage.get("block_content")
    # 记得在公共存储中更新本次创作结果
    block_workflow.public_storage.set("last_block_content", block_content)
    return block_content

## 过程产出输出
@block_workflow.chunk_class()
def print_process_output(inputs, storage):
    print(f"[{ inputs['default']['title'] }]:")
    if isinstance(inputs["default"]["result"], dict):
        print(
            json.dumps(inputs["default"]["result"], indent=4, ensure_ascii=False)
        )
    else:
        print(inputs["default"]["result"])
    return

# 定义分块创作工作流的工作流程
(
    block_workflow
        .connect_to("init_data")
        .connect_to("generate_block_content")
        .connect_to("@print_process_output")
        .connect_to("human_confirm")
        .if_condition(lambda return_value, storage: return_value == "y")
            .connect_to("return_block_content")
            .connect_to("end")
        .else_condition()
            .connect_to("input_revision_suggestion")
            .connect_to("generate_block_content")
)

(
    main_workflow
        .connect_to("input_story_idea")
        .connect_to("generate_background")
        .connect_to("@print_process_output")
        .connect_to("generate_storyline")
        .connect_to("@print_process_output")
        .connect_to("send_story_block_list")# -> list[item1, item2, item3, ...]
            .loop_with(block_workflow) # item1 -> block_workflow:inputs["default"]; item2 -> block_workflow: i
        #.connect_to("sort_out")
        .connect_to("end")
)

# 打印流程图，检查流程正确性
print(main_workflow.draw())