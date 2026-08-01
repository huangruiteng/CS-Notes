from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).parent
ROOT = OUT.parents[1]


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for path in candidates:
        try:
            if path.endswith("Songti.ttc"):
                return ImageFont.truetype(path, size=size, index=6 if bold else 3)
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


BLUE = "#0071B8"
TEXT = "#2D3035"
MUTED = "#68707A"
LINE = "#B9D6E6"
BG = "#FBFAF7"


def rounded_rect(draw: ImageDraw.ImageDraw, box, *, fill, outline=LINE, width=3, radius=20):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw: ImageDraw.ImageDraw, box, text: str, *, fill=TEXT, size=34, bold=False, line_gap=8):
    x1, y1, x2, y2 = box
    lines = text.split("\n")
    f = font(size, bold=bold)
    heights = []
    widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    total_h = sum(heights) + line_gap * (len(lines) - 1)
    y = y1 + (y2 - y1 - total_h) / 2
    for line, w, h in zip(lines, widths, heights):
        draw.text((x1 + (x2 - x1 - w) / 2, y), line, fill=fill, font=f)
        y += h + line_gap


def arrow(draw: ImageDraw.ImageDraw, start, end, *, fill=BLUE, width=4):
    draw.line((start, end), fill=fill, width=width)
    x1, y1 = start
    x2, y2 = end
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 >= x1 else -1
        pts = [(x2, y2), (x2 - 16 * direction, y2 - 10), (x2 - 16 * direction, y2 + 10)]
    else:
        direction = 1 if y2 >= y1 else -1
        pts = [(x2, y2), (x2 - 10, y2 - 16 * direction), (x2 + 10, y2 - 16 * direction)]
    draw.polygon(pts, fill=fill)


def draw_goal_vs_loopx() -> None:
    img = Image.new("RGB", (1280, 760), BG)
    d = ImageDraw.Draw(img)
    d.line((640, 76, 640, 650), fill=LINE, width=3)
    d.text((70, 38), "Codex /goal", fill=BLUE, font=font(46, bold=True))
    d.text((708, 38), "LoopX control plane", fill=BLUE, font=font(46, bold=True))

    left = [
        ((92, 132, 548, 210), "静态 objective"),
        ((92, 260, 548, 338), "bounded run"),
        ((92, 388, 548, 466), "completion audit"),
        ((92, 516, 548, 594), "continue / complete / blocked"),
    ]
    right = [
        ((732, 116, 1188, 184), "goal"),
        ((732, 216, 1188, 284), "vision / acceptance"),
        ((732, 316, 1188, 384), "todo / handoff"),
        ((732, 416, 1188, 484), "run evidence"),
        ((732, 516, 1188, 584), "quota / replan"),
    ]
    for box, text in left:
        rounded_rect(d, box, fill="#FFFFFF")
        center_text(d, box, text, size=34, bold=("objective" in text or "audit" in text))
    for a, b in zip(left, left[1:]):
        arrow(d, ((a[0][0] + a[0][2]) // 2, a[0][3]), ((b[0][0] + b[0][2]) // 2, b[0][1]))

    for box, text in right:
        rounded_rect(d, box, fill="#FFFFFF")
        center_text(d, box, text, size=32, bold=("vision" in text or "replan" in text))
    for a, b in zip(right, right[1:]):
        arrow(d, ((a[0][0] + a[0][2]) // 2, a[0][3]), ((b[0][0] + b[0][2]) // 2, b[0][1]))
    arrow(d, (1188, 550), (1218, 550))
    d.arc((720, 176, 1236, 608), start=-74, end=76, fill=BLUE, width=4)
    arrow(d, (995, 188), (995, 216))

    d.text((118, 652), "结果引导：每轮主要问“能否结束”", fill=MUTED, font=font(34))
    d.text((754, 652), "过程引导：每轮必须写回状态 delta", fill=MUTED, font=font(34))
    img.save(OUT / "goal-vs-loopx-loop.png", quality=95)


def draw_replan_state() -> None:
    img = Image.new("RGB", (1280, 760), BG)
    d = ImageDraw.Draw(img)
    d.text((62, 42), "LoopX 的 goal / vision / replan", fill=BLUE, font=font(44, bold=True))
    boxes = [
        ((80, 150, 330, 230), "Goal\n长期方向"),
        ((410, 150, 660, 230), "Active Vision\n当前边界"),
        ((740, 150, 990, 230), "Run\n执行一段"),
        ((410, 330, 660, 410), "Evidence\n证据写回"),
        ((740, 330, 990, 410), "Frontier\n剩余边界"),
        ((410, 510, 660, 590), "Replan\n重规划"),
        ((80, 510, 330, 590), "Vision Patch\nbounded delta"),
    ]
    for box, text in boxes:
        rounded_rect(d, box, fill="#FFFFFF")
        center_text(d, box, text, size=30, bold=True)
    arrow(d, (330, 190), (410, 190))
    arrow(d, (660, 190), (740, 190))
    arrow(d, (865, 230), (865, 330))
    arrow(d, (740, 370), (660, 370))
    arrow(d, (660, 370), (740, 370))
    arrow(d, (865, 410), (660, 550))
    arrow(d, (410, 550), (330, 550))
    arrow(d, (205, 510), (505, 230))
    d.text((76, 662), "有效 replan 必须写回 vision / todo / acceptance / no-follow-up。", fill=TEXT, font=font(36))
    d.text((76, 710), "只有 ACK、没有 delta，在 LoopX 里就是 replan_noop。", fill=MUTED, font=font(32))
    img.save(OUT / "goal-vision-replan-state.png", quality=95)


PAGES = [
    {
        "filename": "01-cover.jpg",
        "meta": "Codex /goal 模式分析 | 阅读需9分钟",
        "title": "Codex /goal 的\n核心问题",
        "blocks": [
            {
                "type": "paragraph",
                "text": "Codex /goal 的核心问题很明确：它是一个优秀的目标审计层，但不是完整的长程任务控制面。",
            },
            {
                "type": "paragraph",
                "text": "问题一：只适合静态目标，无法维护长程动态复杂目标。objective 可以跨 turn 持久，但执行时长通常仍在 24 小时以内；目标一旦跨天、跨反馈、跨 handoff，人就要手动维护、改写和解释目标。",
            },
            {
                "type": "paragraph",
                "text": "问题二：由结果引导 loop，而非过程引导 loop。continuation.md 的核心是每轮检查“是否完成 / 是否真的 blocked”，而不是要求 agent 写回 evidence、acceptance、successor、quota、replan 等过程状态。",
            },
            {
                "type": "paragraph",
                "text": "所以它能防止 agent 过早停下，却难以把 agent 的行为模式塑造成更适合长程任务的 loop。后面先拆 Codex /goal 的实现，再说为什么需要过程控制面。",
            },
        ],
    },
    {
        "filename": "02-goal-did-right.jpg",
        "meta": "Codex /goal 实现解析",
        "heading": "1. /goal 是目标审计，不是普通继续按钮",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "Codex 的 goal 工具很克制：create_goal 创建 objective，可选 token_budget；get_goal 读当前目标、预算和用量；update_goal 只能把目标标成 complete 或 blocked。",
            },
            {
                "type": "paragraph",
                "text": "protocol 里的状态更完整：Active、Paused、Blocked、UsageLimited、BudgetLimited、Complete。模型自己能调用的终态口径却很窄：完成或严格 blocked。",
            },
            {
                "type": "paragraph",
                "text": "continuation prompt 的核心是完成审计：不能缩水目标，不能用弱证据宣布完成，不能因为预算快没了就收尾。",
            },
            {
                "type": "note",
                "text": "源码：github.com/openai/codex @ 9d87b771\ncodex-rs/ext/goal/templates/goals/continuation.md",
                "gap": 34,
            },
            {
                "type": "rule",
                "text": "它解决的是：agent 什么时候不该停。",
                "size": 58,
                "gap": 48,
            },
            {
                "type": "heading",
                "text": "2. Hermes：把 done 判断交给 grader",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "paragraph",
                "text": "Hermes 代表另一种解法：不让执行 agent 自己宣布 done，而是引入独立 grader / judge。",
            },
        ],
    },
    {
        "filename": "03-hermes-judge.jpg",
        "meta": "另一条路线：独立 judge",
        "heading": "Hermes 的 ROI 权衡",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "执行一轮后，judge 读取 goal 和响应，输出类似 done / reason 的结构化判断。",
            },
            {
                "type": "paragraph",
                "text": "这比 self-audit 更干净。终态判断从执行模型身上拆出来，能降低“我已经做完了”的自评偏差，也更容易把 completion 变成可观测信号。",
            },
            {
                "type": "paragraph",
                "text": "但关键权衡在 ROI。judge 如果只看最终回复或最近 response，成本低，却容易评判叙事完成，而不是证据完成。",
            },
            {
                "type": "paragraph",
                "text": "judge 如果 review 全部 trajectory、工具调用、文件 diff、测试结果和外部状态，判断会更可靠，但每轮都这么做，token、延迟和实现复杂度都会抬高。",
            },
            {
                "type": "rule",
                "text": "分层 judge：客观证据先过，疑难切片再交给强 judge。",
                "size": 58,
                "gap": 48,
            },
            {
                "type": "heading",
                "text": "3. 静态 objective 扛不住动态复杂目标",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "paragraph",
                "text": "Codex /goal 的目标核心是一个 objective。它可以跨 turn 持久，也可以带 token budget，但它不是一个项目状态机。",
            },
        ],
    },
    {
        "filename": "04-static-objective.jpg",
        "meta": "问题一：静态目标",
        "heading": "静态目标的状态缺口",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "长程任务跑到跨小时、跨天、跨多轮反馈时，变化对象不只是一句目标文本，还包括很多中间事实：哪些 evidence 已经成立，哪些 scope 变了，哪个 handoff 已经清空，哪个 successor 还没生成。",
            },
            {
                "type": "paragraph",
                "text": "这时如果只维护静态 goal，人就会重新变成调度器：手动改目标、补上下文、解释新边界、提醒 agent 上一轮证据在哪里。",
            },
            {
                "type": "paragraph",
                "text": "所以 /goal 更适合小时级、一天内、验收边界相对稳定的目标。更长的动态任务，不能只靠一个 objective 保持形状。",
            },
            {
                "type": "heading",
                "text": "4. 用户反馈不是聊天消息，是控制面信号",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "paragraph",
                "text": "人在长程任务里经常会改方向：这个先别做、那个可以旁路推进、这一项需要等我判断、这条证据不够、这个 PR 不要合。",
            },
            {
                "type": "rule",
                "text": "静态 goal 保存目标文本，控制面保存目标变化的证据。",
                "size": 56,
            },
        ],
    },
    {
        "filename": "05-human-collab.jpg",
        "meta": "人机协作问题",
        "heading": "用户反馈要写成状态",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "这些反馈如果只留在聊天里，当轮 agent 能理解，下一轮 agent 未必能继承；压缩、resume、换 agent 后，又会回到自然语言猜测。",
            },
            {
                "type": "paragraph",
                "text": "更稳的做法是把反馈写成状态：gate 的 scope 是什么，阻塞的是哪个 action，是否允许 safe fallback，证据引用在哪里，下一轮谁可以继续。",
            },
            {
                "type": "rule",
                "text": "长程协作的关键：让用户判断能被继承。",
                "size": 58,
                "gap": 48,
            },
            {
                "type": "heading",
                "text": "5. /goal 更像结果审计，不塑造过程",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "paragraph",
                "text": "Codex continuation 的强约束几乎都围绕终点：目标不能缩水，当前状态是权威，完成需要逐项证据，blocked 需要连续三轮同一阻塞。",
            },
            {
                "type": "paragraph",
                "text": "这些规则能防止 agent 过早停下，却不直接规定过程状态怎么写回：本轮产生了什么 evidence，是否改变 acceptance，是否需要 successor，quota 下一轮是否该继续花。",
            },
        ],
    },
    {
        "filename": "06-result-led-loop.jpg",
        "meta": "问题二：结果引导 loop",
        "heading": "结果审计无法塑造过程",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "结果引导 loop 的形状是：跑一轮，然后问“完成了吗”。如果没完成，就让 agent 继续在原来的上下文里找路。",
            },
            {
                "type": "paragraph",
                "text": "长程任务需要另一种形状：每一轮都要产生可继承的过程 delta，让下一轮沿着状态机继续，减少对聊天记忆的依赖。",
            },
            {
                "type": "rule",
                "text": "结果引导问终点，过程引导写状态。",
                "size": 58,
            },
            {
                "type": "heading",
                "text": "6. 区别不在是否自动继续，而在写回什么",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "paragraph",
                "text": "这里的分界可以直接看写回对象：",
            },
            {
                "type": "bullets",
                "items": [
                    "/goal 写回 complete / blocked",
                    "judge 写回 done / reason",
                    "control plane 写回 evidence / frontier / replan",
                ],
            },
        ],
    },
    {
        "filename": "07-two-loops.jpg",
        "meta": "两种 loop",
        "heading": "两种 loop 的状态差异",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {"type": "image", "path": "创作/Codex-goal模式问题-小逸排版/goal-vs-loopx-loop.png", "gap": 52},
            {
                "type": "paragraph",
                "text": "左边的 loop 适合防止 premature stop。右边的 loop 才能承接 state drift：目标推进一次，状态就写回一次；证据耗尽，replan 就成为下一步工作本身。",
            },
            {
                "type": "paragraph",
                "text": "核心是把下一轮需要知道的事实从 transcript 外部化，而不只是在 prompt 里追加说明。",
            },
            {
                "type": "heading",
                "text": "7. 把 goal 拆成 vision、evidence 和 replan",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "paragraph",
                "text": "LoopX 不替代 Codex。Codex 仍然负责 bounded agent loop；LoopX 负责保存这些 loop 能继续工作的动态状态。",
            },
        ],
    },
    {
        "filename": "08-loopx-replan.jpg",
        "meta": "LoopX 的解法",
        "heading": "LoopX 的 replan 合同",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "在 goal_vision_replan_contract_v0 里，每个 agent 只有一份小的 vision packet：vision_summary、role_scope、acceptance_summary、replan_trigger_summary 等字段都有硬预算。",
            },
            {"type": "image", "path": "创作/Codex-goal模式问题-小逸排版/goal-vision-replan-state.png", "gap": 48},
            {
                "type": "paragraph",
                "text": "关键点是：replan 不能只 ACK。有效 replan 必须写回 bounded delta：新的 vision、todo、acceptance，或者明确 no-follow-up。",
            },
            {
                "type": "paragraph",
                "text": "这里的差别很小但很硬：replan 不是一句“我会调整计划”，而是下一轮 agent 能直接继承、也能被系统检查的状态 artifact。",
            },
        ],
    },
    {
        "filename": "09-closing.jpg",
        "meta": "结尾",
        "heading": "8. /goal 是第一层，control plane 是下一层",
        "heading_color": "blue",
        "heading_size": 70,
        "blocks": [
            {
                "type": "paragraph",
                "text": "Codex /goal 的价值是把“能否结束”做成 runtime 审计。它让 agent 不轻易缩水目标、不用弱证据完成、不把困难误报成 blocked。",
            },
            {
                "type": "paragraph",
                "text": "但长程任务还需要第二层：让过程本身可继承。goal 定方向，vision 定当前边界，todo/handoff 定谁继续，evidence 定什么为真，quota 定是否值得继续花，replan 定下一轮怎么变。",
            },
            {
                "type": "paragraph",
                "text": "LoopX 的位置：把静态 goal 变成动态、人类在环、可持续接力的 agent loop 状态。",
            },
            {
                "type": "rule",
                "text": "/goal 管终点，judge 管判定，LoopX 管可继承状态。",
                "size": 64,
            },
            {
                "type": "heading",
                "text": "源码入口",
                "color": "blue",
                "size": 70,
            },
            {
                "type": "note",
                "text": "Codex continuation prompt：github.com/openai/codex @ 9d87b771\ncodex-rs/ext/goal/templates/goals/continuation.md",
                "gap": 26,
            },
            {
                "type": "note",
                "text": "LoopX：github.com/huangruiteng/loopx",
                "gap": 26,
            },
        ],
    },
]


def write_spec() -> None:
    spec = {
        "style": {
            "width": 1440,
            "height": 2400,
            "margin": 80,
            "left_rule": 56,
            "bottom_rule_offset": 122,
            "title_size": 148,
            "heading_size": 66,
            "body_size": 58,
            "meta_size": 40,
            "title_font_index": 6,
            "body_font_index": 6,
            "body_line_gap": 26,
            "paragraph_gap": 34,
        },
        "pages": PAGES,
    }
    (OUT / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_publish_md() -> None:
    body = """# Codex /goal 模式问题小红书素材 - 小逸排版版

## 图片上传顺序

1. ![](./Codex-goal模式问题-小逸排版/01-cover.jpg)
2. ![](./Codex-goal模式问题-小逸排版/02-goal-did-right.jpg)
3. ![](./Codex-goal模式问题-小逸排版/03-hermes-judge.jpg)
4. ![](./Codex-goal模式问题-小逸排版/04-static-objective.jpg)
5. ![](./Codex-goal模式问题-小逸排版/05-human-collab.jpg)
6. ![](./Codex-goal模式问题-小逸排版/06-result-led-loop.jpg)
7. ![](./Codex-goal模式问题-小逸排版/07-two-loops.jpg)
8. ![](./Codex-goal模式问题-小逸排版/08-loopx-replan.jpg)
9. ![](./Codex-goal模式问题-小逸排版/09-closing.jpg)

## 标题

推荐：

Codex /goal 的核心问题

备选：

- Codex /goal 核心问题：目标不会演化
- Codex /goal：管终点，难管目标演化
- Codex /goal 的短板：目标不会自己演化
- Codex /goal 很强，但它不是长程控制面
- 为什么 Codex /goal 更像结果审计
- 长程 Agent 不能只有一个静态 Goal

## 正文

Codex /goal 的核心问题很明确：

它是一个优秀的目标审计层，但不是完整的长程任务控制面。

问题一：只适合静态目标，无法维护长程动态复杂目标。

objective 可以跨 turn 持久，也可以带 token budget。但它仍然更适合小时级、一天内、验收边界相对稳定的任务。执行时长一旦拉到跨天、跨多轮反馈、跨 handoff，人就要手动维护目标、改写目标、解释新边界。

这也是人机协作体验差的地方：

目标看似持久，真实目标状态却仍然散在聊天、文件、证据、用户反馈和 agent 自己的记忆里。

问题二：由结果引导 loop，而非过程引导 loop。

Codex continuation.md 的核心问题是：

这轮之后，目标完成了吗？

证据够不够？

是不是真的 blocked？

如果没有完成，就继续。

这套设计能防止 agent 过早停下，但很难主动塑造 agent 的过程行为。长程任务还需要每一轮都写回过程状态：

- 本轮产生了什么 evidence；
- acceptance 是否变化；
- 是否需要 successor；
- handoff 是否清空；
- 是否应该 replan；
- quota 下一轮是否值得继续花。

所以 /goal 的问题落在 loop 的驱动力上。

结果引导 loop 会不断问“完成了吗”。

过程引导 loop 要求每一轮都写回状态 delta。

先看 Codex /goal 的实现。

Codex 的 create_goal / get_goal / update_goal 把 objective、status、token budget、usage accounting 做成 thread-level state；update_goal 只允许模型把目标标成 complete 或 blocked。

protocol 里的状态更完整：Active、Paused、Blocked、UsageLimited、BudgetLimited、Complete。但模型自己能写入的终态口径很窄。

continuation prompt 的核心是完成审计：不能缩水目标，不能用弱证据宣布完成，不能因为预算快没了就收尾，blocked 需要连续多轮同一阻塞。

这层能力很有价值。它解决的是：agent 什么时候不该停。

Hermes 代表另一种补法：把 done 判断交给独立 grader / judge。

执行 agent 跑完一轮后，不由它自己宣布完成，而是让 judge 读取 goal 和响应，输出类似 done / reason 的结构化判断。

这能降低 self-audit 偏差，也能把 completion 变成更独立的信号。

但它的权衡在 ROI。

如果 judge 只看最终回复或最近 response，成本低，却容易评判叙事完成，而不是证据完成。

如果 judge review 全部 trajectory、工具调用、文件 diff、测试结果和外部状态，判断会更可靠，但每轮都这么做，token、延迟和实现复杂度都会很高。

分层 judge 更适合这类任务：默认不全量 review traj；客观证据先过，疑难切片、高风险 gate、无法被 deterministic check 覆盖的部分，再交给强 judge。

但无论是 /goal 的终点审计，还是 Hermes 的独立 judge，长程任务还需要另一层：agent 每一轮应该如何留下可继承的过程状态。

LoopX 想补的就是这一层。

它不替代 Codex。Codex 仍然负责 bounded agent loop：读文件、改代码、跑命令、回复用户。

LoopX 负责保存这些 loop 能继续工作的动态状态：goal、vision、todo、handoff、run history、evidence、quota 和 replan。

更具体一点，在 goal_vision_replan_contract_v0 里，每个 agent 有一份小的 vision packet：当前方向、role scope、acceptance、replan trigger 都有硬预算。

当 advancement frontier 耗尽、monitor-only lane 无法推进、handoff 清空但没有 successor、用户目标或 acceptance 变化时，系统进入 replan。

有效 replan 不能只是 ACK。

它必须写回 bounded delta：新的 vision、todo、acceptance，或者明确 no-follow-up。

/goal 的位置可以压成一句：

它是长程 agent 的第一层能力，负责终点审计。

下一层能力，是过程控制面。

goal 定方向，vision 定当前边界，todo/handoff 定谁继续，evidence 定什么为真，quota 定是否继续花，replan 定下一轮怎么变。

LoopX 的位置：把静态 goal 变成动态、人类在环、可持续接力的 agent loop 状态。

GitHub 搜：huangruiteng/loopx

#Codex #OpenAI #AIAgent #AI编程 #LoopX #LoopEngineering #ClaudeCode #Cursor #AgentInfra #开发者工具

## 技术来源

- Codex continuation prompt：<https://raw.githubusercontent.com/openai/codex/9d87b771cebd0f80e4637e80c93b0d66b10d86c0/codex-rs/ext/goal/templates/goals/continuation.md>
- Codex goal tools：<https://raw.githubusercontent.com/openai/codex/9d87b771cebd0f80e4637e80c93b0d66b10d86c0/codex-rs/ext/goal/src/spec.rs>
- Codex ThreadGoalStatus：<https://github.com/openai/codex/blob/9d87b771cebd0f80e4637e80c93b0d66b10d86c0/codex-rs/protocol/src/protocol.rs#L3661-L3701>
- Hermes Persistent Goals：<https://hermes-agent.nousresearch.com/docs/user-guide/features/goals>
- Hermes slash commands reference：<https://hermes-agent.nousresearch.com/docs/reference/slash-commands>
- LoopX repo：<https://github.com/huangruiteng/loopx>
- LoopX goal / vision / replan contract：<https://github.com/huangruiteng/loopx/blob/main/docs/reference/protocols/goal-vision-replan-contract-v0.md>

## 发布备注

- 标题要保留 Codex /goal，保证第一眼知道在蹭什么话题。
- 正文不要写成“Codex 不行”。主线是：/goal 做对了终点审计，但长程任务还需要过程控制面。
- 小红书正文里写“GitHub 搜：huangruiteng/loopx”，评论区可放完整链接。
"""
    (OUT.parent / "Codex-goal模式问题-小逸排版发布稿.md").write_text(body, encoding="utf-8")


def main() -> None:
    draw_goal_vs_loopx()
    draw_replan_state()
    write_spec()
    write_publish_md()


if __name__ == "__main__":
    main()
