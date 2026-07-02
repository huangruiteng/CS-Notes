from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
import random
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent
W, H = 1440, 2400
LEFT_RULE = 56
BOTTOM_RULE = H - 122
M = 80
CONTENT_W = W - 2 * M
BLUE = "#0068B7"
TEXT = "#383838"
MUTED = "#5F5F5F"
LINE_BLUE = "#B8D7E4"
BG = "#FCFCFB"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/System/Library/Fonts/STHeiti Medium.ttc",
]


def font_path() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    raise FileNotFoundError("No usable font found")


FONT_PATH = font_path()
FONT_INDEX = {
    "title": 6,  # Songti SC Regular; default index 0 is Songti SC Black and looks too heavy.
    "body": 6,
}
TOKEN_RE = re.compile(r"[A-Za-z0-9_./:+#-]+|[\u4e00-\u9fff]|[^\x00-\x7F]|\s+|.")


def font(size: int, style: str = "body") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX.get(style, FONT_INDEX["body"]))


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def split_oversized_token(draw: ImageDraw.ImageDraw, token: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for ch in token:
        candidate = current + ch
        if text_size(draw, candidate, fnt)[0] <= max_width:
            current = candidate
        else:
            if current:
                parts.append(current)
            current = ch
    if current:
        parts.append(current)
    return parts


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for raw in text.split("\n"):
        current = ""
        for token in TOKEN_RE.findall(raw):
            if not current and token.isspace():
                continue
            candidate = current + token
            if text_size(draw, candidate, fnt)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current.rstrip())
                    current = token.lstrip()
                if current and text_size(draw, current, fnt)[0] > max_width:
                    parts = split_oversized_token(draw, current, fnt, max_width)
                    lines.extend(parts[:-1])
                    current = parts[-1] if parts else ""
        if current:
            lines.append(current.rstrip())
        if raw == "":
            lines.append("")
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    fnt: ImageFont.FreeTypeFont,
    fill: str = TEXT,
    max_width: int = CONTENT_W,
    line_gap: int = 22,
) -> int:
    for line in wrap_text(draw, text, fnt, max_width):
        if not line:
            y += int(fnt.size * 0.85)
            continue
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y


def render_math(expr: str, size: int = 46, color: str = TEXT) -> Image.Image:
    fig = plt.figure(figsize=(8, 1.4), dpi=240)
    fig.patch.set_alpha(0)
    fig.text(0.02, 0.5, f"${expr}$", fontsize=size, color=color, va="center")
    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def draw_texture(img: Image.Image, seed: int) -> None:
    rng = random.Random(seed)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    clusters = [
        (120, 10, 560, 260),
        (720, 420, 540, 420),
        (80, 820, 480, 380),
        (650, 1220, 420, 420),
        (420, 1840, 420, 360),
    ]
    for cx, cy, cw, ch in clusters:
        for _ in range(18):
            x = cx + rng.randint(0, cw)
            y = cy + rng.randint(0, ch)
            points = []
            angle = rng.random() * math.tau
            steps = rng.randint(8, 18)
            for _ in range(steps):
                angle += rng.uniform(-0.9, 0.9)
                x += math.cos(angle) * rng.randint(8, 24)
                y += math.sin(angle) * rng.randint(8, 24)
                points.append((x, y))
            if len(points) > 1:
                draw.line(points, fill=(0, 104, 183, 50), width=2, joint="curve")
    img.alpha_composite(overlay)


class Page:
    def __init__(self, index: int) -> None:
        self.index = index
        self.img = Image.new("RGBA", (W, H), BG)
        draw_texture(self.img, index * 137)
        self.draw = ImageDraw.Draw(self.img)
        self.draw.line((LEFT_RULE, 0, LEFT_RULE, H), fill=LINE_BLUE, width=2)
        self.draw.line((0, BOTTOM_RULE, W, BOTTOM_RULE), fill=LINE_BLUE, width=2)
        self.y = 118

    def meta(self, text: str) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(40), TEXT, CONTENT_W, line_gap=18)
        self.y += 42
        self.draw.line((0, self.y, W, self.y), fill=LINE_BLUE, width=2)
        self.y += 38

    def title(self, text: str) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(148, "title"), BLUE, W - M - 40, line_gap=18)
        self.y += 56

    def heading(self, text: str) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(66, "title"), TEXT, CONTENT_W, line_gap=18)
        self.y += 58

    def paragraph(self, text: str, gap: int = 58, size: int = 58) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(size), TEXT, CONTENT_W, line_gap=34)
        self.y += gap

    def note(self, text: str, gap: int = 40) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(46), MUTED, CONTENT_W, line_gap=24)
        self.y += gap

    def bullets(self, items: list[str], gap: int = 30) -> None:
        for item in items:
            dot_y = self.y + 31
            self.draw.ellipse((M, dot_y, M + 44, dot_y + 44), fill=BLUE)
            self.y = draw_wrapped(self.draw, item, M + 170, self.y, font(58), TEXT, CONTENT_W - 170, line_gap=34)
            self.y += gap

    def formula(self, expr: str, size: int = 54, gap: int = 48) -> None:
        formula_img = render_math(expr, size=size)
        max_w = CONTENT_W - 40
        if formula_img.width > max_w:
            ratio = max_w / formula_img.width
            formula_img = formula_img.resize((int(formula_img.width * ratio), int(formula_img.height * ratio)), Image.Resampling.LANCZOS)
        x = M + (CONTENT_W - formula_img.width) // 2
        self.img.paste(formula_img, (x, self.y), formula_img)
        self.y += formula_img.height + gap

    def rule_line(self, text: str, size: int = 60, gap: int = 58) -> None:
        fnt = font(size)
        self.y = draw_wrapped(self.draw, text, M, self.y, fnt, TEXT, CONTENT_W, line_gap=22)
        self.y += gap

    def save(self, name: str) -> None:
        self.img.convert("RGB").save(OUT_DIR / name, quality=95)


def build() -> None:
    p = Page(1)
    p.meta("全文约2200字 | 阅读需8分钟")
    p.title("Loop Engineering：\n长程任务状态定义\n= Handoff 不动点")
    p.paragraph("长程任务不是把上下文塞得更长，而是让一个 agent loop 在多轮执行、验证和 handoff 后，仍然保持同一个工作面。")
    p.paragraph("这就是 loop engineering 要解决的问题：每一轮可以推进业务，但目标、边界、证据和下一步不能被 session drift 偷走。")
    p.paragraph("GLM-5.2 把 1M context 放进 long-horizon Coding Agent 场景后，这个问题变得更明确：模型能力只是入口，外部状态才决定任务能不能长期跑。")
    p.paragraph("更硬的定义是：长程任务的状态，是 handoff 的不动点。")
    p.save("01-cover-and-intro.jpg")

    p = Page(2)
    p.heading("1. 从 1M context 开始")
    p.paragraph("GLM-5.2 的卖点当然是 1M context，但报告真正有意思的地方，是它把 1M 放进 long-horizon Coding Agent 场景里：大规模实现、自动化研究、性能优化、跨文件重构。")
    p.paragraph("官方文档提到，模型需要在长任务后段持续保留模块边界、架构约束、API contract、目录结构和历史决策。")
    p.paragraph("这句话非常关键。因为长上下文本身只解决“还能不能看见”。长程任务真正的问题是：")
    p.bullets([
        "前面的判断能不能继续约束后面的动作？",
        "中间产生的证据能不能被后续 agent 复核？",
        "一轮执行结束后，下一轮是否还能接住同一个目标？",
    ])
    p.paragraph("所以 context engineering 只覆盖了一半。另一半是 harness engineering：把目标、边界、证据和下一步写成外部状态。")
    p.save("02-context-to-harness.jpg")

    p = Page(3)
    p.heading("2. 为什么 single-commit benchmark 不够")
    p.paragraph("GLM-5 技术报告里的 long-horizon evaluation 很有启发。它不是只看一次修改有没有通过测试，而是把评估拆成两类：Large Repo Exploration 和 Multi-step Chained Tasks。")
    p.bullets([
        "前者看 agent 能不能在一个陌生大仓库里，从业务语义一路定位到真正相关的文件。",
        "后者从真实 PR 里拆出连续任务链，让代码库状态随着每一步提交持续变化。",
    ])
    p.paragraph("这比传统 SWE-bench 更接近真实工程：每一步动作都会改写下一步的上下文。")
    p.paragraph("如果第一个任务里做了一个次优修改，它可能不会立刻爆炸，但会在后面的任务链里变成累积错误。")
    p.paragraph("这就是长程任务和短程任务最大的不同：长程任务不是一次性解题，而是状态递归。")
    p.save("03-benchmark-state-recursion.jpg")

    p = Page(4)
    p.heading("3. Agent loop 其实是在改写状态")
    p.paragraph("把这个问题抽象一下。长程任务在某一阶段有一个持久状态 X。一次 agent loop 不是只生成回答，而是在改写 X。")
    p.rule_line("X′ = X + ΔP + ΔS", size=64)
    p.paragraph("这里可以拆成两部分：")
    p.bullets([
        "进度增量 ΔP：任务确实往前移动，比如完成代码、验证、PR、文档或一次安全的 cleanup。",
        "结构漂移 ΔS：状态表示本身发生偏移，比如目标被改写、约束被漏掉、证据链断开、下一步动作变得不稳定。",
    ])
    p.paragraph("长程任务当然允许 ΔP 增长，但要让 ΔS 收敛。也就是：进度可以继续变，结构不能持续漂。")
    p.rule_line("结构收敛：Structure(after) ≈ Structure(before)", size=50)
    p.save("04-agent-loop-state.jpg")

    p = Page(5)
    p.heading("4. Handoff 是一次无进展 loop")
    p.paragraph("handoff 本身不应该完成新的业务工作。它只做三件事：停止当前 worker，加载持久状态，恢复同一个工作面。")
    p.rule_line("Handoff：ΔP ≈ 0，ΔH ≈ ΔS", size=58)
    p.paragraph("因此 handoff 检验的不是模型这轮会不会写代码，而是新 agent 是否仍然能读出同一组东西：")
    p.bullets([
        "objective",
        "authority sources",
        "validation surfaces",
        "claim boundary",
        "next action",
    ], gap=24)
    p.paragraph("如果这些东西在 handoff 后变了，说明任务看似继续了，状态其实已经漂了。")
    p.rule_line("稳定性：N(after handoff) ≈ N(before)", size=52)
    p.save("05-handoff-loop.jpg")

    p = Page(6)
    p.heading("5. LoopX 的位置")
    p.paragraph("LoopX 的定位因此很清楚：它不是新的 agent executor。Codex、Claude Code、Cursor 这类 runtime 负责执行 bounded loop；LoopX 负责维护 loop 之外的状态。")
    p.paragraph("这个状态至少要包括：")
    p.bullets([
        "目标和当前 active state",
        "todo / gate / claim",
        "证据、验证结果和 run history",
        "handoff packet，以及下一轮恢复条件",
    ])
    p.paragraph("换句话说，runtime 解决“这一轮怎么做”，LoopX 解决“下一轮还怎么接着同一个任务做”。")
    p.paragraph("GitHub 搜：huangruiteng/loopx")
    p.save("06-loopx-control-plane.jpg")

    p = Page(7)
    p.heading("6. 怎么验证状态定义是否 work")
    p.paragraph("状态定义必须经得起 handoff 压测。")
    p.paragraph("一种最小评估方式是：让新 agent 只读取状态，然后输出 normalized state，不允许推进业务。")
    p.paragraph("它至少要复述出：目标、约束、证据缺口、下一步、验证面、claim 边界、当前 gate。")
    p.paragraph("然后比较 handoff 前后的状态投影：")
    p.rule_line("连续 handoff：N(after) ≈ N(before)", size=52)
    p.paragraph("如果连续 N 次 handoff 后仍然不漂，状态才算从 session memory 变成 project memory。")
    p.save("07-validate-state.jpg")

    p = Page(8)
    p.heading("7. 总结")
    p.paragraph("GLM-5.2 的价值，不只是又把 context window 拉长了。更重要的是，它把 long-horizon agent 重新推到模型训练和评测的中心。")
    p.paragraph("但对真实工程系统来说，模型只是一半。另一半是 agent 运行时外面的状态控制面。")
    p.paragraph("结论是：")
    p.bullets([
        "长程任务的状态是 handoff 的不动点。",
        "业务可以继续推进，状态结构需要收敛。",
        "真正的 long-horizon agent，需要同时解决模型能力、context 组织和 harness 状态协议。",
    ])
    p.paragraph("LoopX 要解决的正是这个问题：让 agent 不只会干活，还能被管理、复盘、接手。")
    p.save("08-summary.jpg")


if __name__ == "__main__":
    build()
