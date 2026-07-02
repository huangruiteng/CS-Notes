from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent
W, H = 1242, 1656
M = 72
CONTENT_W = W - 2 * M

FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def font_path() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return path
    raise FileNotFoundError("No Chinese font found")


FONT_PATH = font_path()


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


TOKEN_RE = re.compile(r"[A-Za-z0-9_./:+#-]+|[\u4e00-\u9fff]|[^\x00-\x7F]|\s+|.")


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
    fill: str,
    max_width: int,
    line_gap: int = 12,
) -> int:
    for line in wrap_text(draw, text, fnt, max_width):
        if not line:
            y += int(fnt.size * 0.75)
            continue
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(draw, line, fnt)[1] + line_gap
    return y


def paste_logo(img: Image.Image, max_size: int = 168, x=None, y: int = 58) -> None:
    logo_path = OUT_DIR / "loopx-logo.png"
    if not logo_path.exists():
        return
    logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    lx = x if x is not None else W - M - logo.width
    img.paste(logo, (lx, y), logo)


def render_math(expr: str, size: int = 34, color: str = "#1C1F26") -> Image.Image:
    fig = plt.figure(figsize=(8, 1.5), dpi=240)
    fig.patch.set_alpha(0)
    fig.text(0.02, 0.5, f"${expr}$", fontsize=size, color=color, va="center")
    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


class Page:
    def __init__(self, index: int, total: int, kicker: str, title: str, bg: str = "#FBFAF6", title_size: int = 62) -> None:
        self.index = index
        self.total = total
        self.img = Image.new("RGB", (W, H), bg)
        self.draw = ImageDraw.Draw(self.img)
        self.y = 58
        self.kicker(kicker)
        self.y += 54
        self.title(title, title_size)

    def kicker(self, text: str) -> None:
        fnt = font(31)
        tw, th = text_size(self.draw, text, fnt)
        self.draw.rounded_rectangle((M, self.y, M + tw + 46, self.y + th + 26), radius=8, fill="#E94F37")
        self.draw.text((M + 23, self.y + 11), text, font=fnt, fill="#FFFFFF")
        self.y += th + 26

    def title(self, text: str, size: int) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(size), "#1C1F26", CONTENT_W, line_gap=14)
        self.draw.rectangle((M, self.y + 16, M + 300, self.y + 28), fill="#1677FF")
        self.y += 76

    def paragraph(self, text: str, size: int = 38, color: str = "#3B404A", gap: int = 22) -> None:
        self.y = draw_wrapped(self.draw, text, M, self.y, font(size), color, CONTENT_W, line_gap=14)
        self.y += gap

    def bullet(self, text: str, size: int = 36, gap: int = 18) -> None:
        bullet_y = self.y + 16
        self.draw.ellipse((M + 4, bullet_y, M + 18, bullet_y + 14), fill="#1677FF")
        self.y = draw_wrapped(self.draw, text, M + 38, self.y, font(size), "#3B404A", CONTENT_W - 38, line_gap=12)
        self.y += gap

    def subbullet(self, text: str, size: int = 34, gap: int = 14) -> None:
        bullet_y = self.y + 16
        self.draw.ellipse((M + 44, bullet_y, M + 56, bullet_y + 12), fill="#8ABEFF")
        self.y = draw_wrapped(self.draw, text, M + 76, self.y, font(size), "#4F5663", CONTENT_W - 76, line_gap=10)
        self.y += gap

    def formula(self, expr: str, size: int = 34, gap: int = 24) -> None:
        formula_img = render_math(expr, size=size)
        max_w = CONTENT_W - 56
        if formula_img.width > max_w:
            ratio = max_w / formula_img.width
            formula_img = formula_img.resize((int(formula_img.width * ratio), int(formula_img.height * ratio)), Image.Resampling.LANCZOS)
        box_h = formula_img.height + 42
        self.draw.rounded_rectangle((M, self.y, W - M, self.y + box_h), radius=8, fill="#EEF6FF", outline="#A8CCFF", width=2)
        self.draw.rectangle((M, self.y, M + 10, self.y + box_h), fill="#1677FF")
        fx = M + (CONTENT_W - formula_img.width) // 2
        self.img.paste(formula_img, (fx, self.y + 20), formula_img)
        self.y += box_h + gap

    def formula_group(self, exprs: list[str], size: int = 31, gap: int = 24) -> None:
        rendered = [render_math(expr, size=size) for expr in exprs]
        max_w = CONTENT_W - 56
        resized = []
        for img in rendered:
            if img.width > max_w:
                ratio = max_w / img.width
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)
            resized.append(img)
        box_h = sum(img.height for img in resized) + 34 * len(resized) + 24
        self.draw.rounded_rectangle((M, self.y, W - M, self.y + box_h), radius=8, fill="#EEF6FF", outline="#A8CCFF", width=2)
        self.draw.rectangle((M, self.y, M + 10, self.y + box_h), fill="#1677FF")
        yy = self.y + 20
        for img in resized:
            fx = M + (CONTENT_W - img.width) // 2
            self.img.paste(img, (fx, yy), img)
            yy += img.height + 34
        self.y += box_h + gap

    def callout(self, text: str) -> None:
        y0 = self.y
        tmp_y = draw_wrapped(self.draw, text, M + 34, self.y + 28, font(33), "#1E2B3A", CONTENT_W - 68, line_gap=12)
        h = max(96, tmp_y - y0 + 20)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle((M, y0, W - M, y0 + h), radius=8, fill="#EAF3FF", outline="#9CC6FF", width=3)
        od.rectangle((M, y0, M + 12, y0 + h), fill="#1677FF")
        self.img = Image.alpha_composite(self.img.convert("RGBA"), overlay).convert("RGB")
        self.draw = ImageDraw.Draw(self.img)
        draw_wrapped(self.draw, text, M + 34, y0 + 28, font(33), "#1E2B3A", CONTENT_W - 68, line_gap=12)
        self.y = y0 + h + 28

    def logo_strip(self) -> None:
        logo_path = OUT_DIR / "loopx-logo.png"
        if not logo_path.exists():
            return
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((154, 154), Image.Resampling.LANCZOS)
        x = W - M - logo.width
        y = 56
        self.img.paste(logo, (x, y), logo)

    def footer(self) -> None:
        self.draw.text((M, H - 62), "github.com/huangruiteng/loopx", font=font(28), fill="#6A717D")
        self.draw.text((W - 144, H - 64), f"{self.index}/{self.total}", font=font(30), fill="#262A31")

    def save(self, name: str) -> None:
        self.footer()
        self.img.save(OUT_DIR / name, quality=95)


def build_pages() -> None:
    total = 8

    cover = Image.new("RGB", (W, H), "#FBFAF6")
    cd = ImageDraw.Draw(cover)
    y = 72
    kf = font(31)
    kt = "Long-horizon Agent"
    kw, kh = text_size(cd, kt, kf)
    cd.rounded_rectangle((M, y, M + kw + 46, y + kh + 26), radius=8, fill="#E94F37")
    cd.text((M + 23, y + 11), kt, font=kf, fill="#FFFFFF")
    paste_logo(cover, max_size=164, y=58)
    y += 136
    y = draw_wrapped(cd, "长程任务状态定义：Handoff 的不动点", M, y, font(72), "#1C1F26", CONTENT_W, line_gap=16)
    cd.rectangle((M, y + 20, M + 330, y + 34), fill="#1677FF")
    y += 104
    y = draw_wrapped(
        cd,
        "不是把 context window 拉长，而是让状态跨 loop、跨 handoff 后语义不漂。",
        M,
        y,
        font(42),
        "#3B404A",
        CONTENT_W,
        line_gap=16,
    )
    y += 58
    formula_img = render_math(r"d(N(H^k(X)), N(X)) < \epsilon", size=42)
    max_w = CONTENT_W - 70
    if formula_img.width > max_w:
        ratio = max_w / formula_img.width
        formula_img = formula_img.resize((int(formula_img.width * ratio), int(formula_img.height * ratio)), Image.Resampling.LANCZOS)
    box_h = formula_img.height + 72
    cd.rounded_rectangle((M, y, W - M, y + box_h), radius=8, fill="#EEF6FF", outline="#A8CCFF", width=2)
    cd.rectangle((M, y, M + 12, y + box_h), fill="#1677FF")
    cover.paste(formula_img, (M + (CONTENT_W - formula_img.width) // 2, y + 34), formula_img)
    y += box_h + 62
    y = draw_wrapped(
        cd,
        "runtime 执行 loop；LoopX 维护目标、边界、证据、下一步和 handoff 合约。",
        M,
        y,
        font(38),
        "#3B404A",
        CONTENT_W,
        line_gap=16,
    )
    cd.text((M, H - 80), "github.com/huangruiteng/loopx", font=font(30), fill="#6A717D")
    cover.save(OUT_DIR / "00-cover.png", quality=95)

    p = Page(1, total, "状态定义", "长程任务需要外部状态")
    p.bullet("我们假设模型的上下文能力是有限的，而长程任务的上下文是不断膨胀的。我们假设未来 Agent 成为数字员工，当用户给他定下了赚 100 万元的目标，在达成目标前，它将日夜不息地积攒海量上下文。")
    p.bullet("因此长程任务需要外部状态，克服模型有限的上下文。")
    p.callout("这篇的主线：长程任务不是把 context window 拉长，而是把可恢复、可交接、可验证的状态外置。")
    p.save("01-long-task-external-state.png")

    p = Page(2, total, "Agent Loop", "Agent loop 中的状态转化")
    p.bullet("设长程任务在某一阶段的持久状态为 X。一次 agent loop 对状态的转化为 F，可以写成：")
    p.formula(r"F(X)=X+\Delta X", size=36)
    p.bullet("ΔX 可以拆成两个部分：")
    p.subbullet("进度增量 ΔP：任务确实往前移动，例如完成代码、验证、PR、文档或一次安全的 cleanup。")
    p.subbullet("结构漂移 ΔS：状态表示本身发生偏移，例如目标被改写、约束被漏掉、证据链断开、下一步动作变得不稳定。")
    p.save("02-agent-loop-state-transform.png")

    p = Page(3, total, "收敛条件", "长程任务允许进度增长，但要求结构漂移收敛")
    p.bullet("长程任务允许进度继续增长，同时要求结构漂移收敛：")
    p.formula_group([
        r"\Delta S \to 0",
        r"\operatorname{Structure}(F(X)) \approx \operatorname{Structure}(X)",
    ], size=32)
    p.bullet("工程化的检验口径是：")
    p.formula(r"d(N(F(X)), N(X)) < \epsilon", size=36)
    p.subbullet("其中 N 是状态归一化或投影函数，d 是衡量语义漂移的评估器；投影口径对应目标是否一致、约束是否保留、证据是否可复核、下一步是否稳定。")
    p.save("03-drift-convergence.png")

    p = Page(4, total, "Handoff", "Handoff 可以建模成一次无进展 loop")
    p.bullet("一次 handoff 不应该完成新的业务工作，它只做三件事：停止当前 worker，加载持久状态，恢复同一个工作面。")
    p.subbullet("形式上，handoff 可以写成：")
    p.formula_group([
        r"H(X)=X+\Delta H",
        r"\Delta P_H \approx 0",
        r"\Delta H \approx \Delta S_H",
    ], size=32)
    p.bullet("因此，handoff 把检验对象从业务能力切到状态稳定性：新 agent 是否仍能读出同一组 objective、authority sources、validation surfaces、claim boundary 和 next action。")
    p.subbullet("稳定性要求是：")
    p.formula_group([
        r"\operatorname{Structure}(H(X)) \approx \operatorname{Structure}(X)",
        r"d(N(H(X)), N(X)) < \epsilon",
    ], size=29)
    p.save("04-handoff-no-progress-loop.png")

    p = Page(5, total, "不动点", "长程任务状态是 Agent Handoff 的不动点")
    p.bullet("如果连续 N 次 handoff 后，仍然满足：")
    p.formula(r"d(N(H^k(X)), N(X)) < \epsilon,\quad k=1,\dots,N", size=32)
    p.bullet("说明状态已经从 session memory 变成 project memory。")
    p.subbullet("它不依赖某个 worker 的临时上下文，而是可以被不同 agent 恢复、继承和复核。")
    p.callout("判断一个状态定义是否成立，不看它写得多完整，而看它能否在连续 handoff 后保持同一组目标、边界、证据和 next action。")
    p.save("05-handoff-fixed-point.png")

    p = Page(6, total, "LoopX", "LoopX：长程任务的状态控制面")
    p.logo_strip()
    p.bullet("LoopX 不是新的 agent executor。Codex、Claude Code、Cursor 等 runtime 负责执行一次 bounded loop；LoopX 负责让这个 loop 跨小时、跨天、跨 handoff 后仍然保持同一组目标、边界、证据和下一步。")
    p.bullet("对用户，LoopX 把底层状态压成五个问题：目标是什么、下一步谁做、哪里需要人判断、证据改变了什么、下一轮能否安全交接。")
    p.bullet("对开发者，LoopX 提供本地控制面：.loopx registry、active state、todo / gate / claim、run history、quota、public/private boundary。")
    p.callout("一句话：runtime 执行 loop，LoopX 维护状态不漂和 handoff 合约。GitHub 搜 huangruiteng/loopx。")
    p.save("06-loopx-control-plane.png")

    p = Page(7, total, "验证", "如何验证长程任务的状态定义是否 work", title_size=56)
    p.bullet("评估单次 handoff 的状态漂移：让新 agent 只读取状态并输出 objective、约束、证据缺口和 next action，不允许推进业务，比较 N(H(X)) 和 N(X)。")
    p.subbullet("N 是评估器。")
    p.bullet("通过连续 N 次 handoff 来验证：")
    p.subbullet("handoff 前生成 canonical state packet；")
    p.subbullet("新 agent 只读状态，禁止业务推进；")
    p.subbullet("输出 normalized state；")
    p.subbullet("LLM 评估，对比 7 个字段，记录 drift score；")
    p.paragraph("连续 N 次后看收敛情况。", size=36)
    p.save("07-validate-handoff-drift.png")

    p = Page(8, total, "验证与总结", "通过拉长任务时间来验证")
    p.bullet("允许 agent 完成一个小的可验证动作，检查 ΔP 是否进入状态，ΔS 是否保持在阈值内。")
    p.subbullet("能 work 的状态定义，有助于长程任务的 loop 拉的更长。")
    p.callout("总结：长程任务的状态是 Handoff 的不动点，应在多轮 loop 和 handoff 后语义不漂。")
    p.bullet("业务可以继续推进，状态结构需要收敛。")
    p.save("08-validation-summary.png")


if __name__ == "__main__":
    build_pages()
