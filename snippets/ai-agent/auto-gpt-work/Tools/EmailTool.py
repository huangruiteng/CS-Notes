import webbrowser
import urllib.parse
import re


def _is_valid_email(email: str) -> bool:
    receivers = email.split(';')
    # 正则表达式匹配电子邮件
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    for receiver in receivers:
        if not bool(re.match(pattern, receiver.strip())):
            return False
    return True


def send_email(
        to: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
) -> str:
    """给指定的邮箱发送邮件"""

    if not _is_valid_email(to):
        return f"电子邮件地址 {to} 不合法"

    # 对邮件的主题和正文进行URL编码
    subject_code = urllib.parse.quote(subject)
    body_code = urllib.parse.quote(body)

    # 构造mailto链接
    mailto_url = f'mailto:{to}?subject={subject_code}&body={body_code}'
    if cc is not None:
        cc = urllib.parse.quote(cc)
        mailto_url += f'&cc={cc}'
    if bcc is not None:
        bcc = urllib.parse.quote(bcc)
        mailto_url += f'&bcc={bcc}'

    webbrowser.open(mailto_url)

    return f"状态: 成功\n备注: 已发送邮件给 {to}, 标题: {subject}"
