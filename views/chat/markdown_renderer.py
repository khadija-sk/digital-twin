import re


class MarkdownRenderer:
    @staticmethod
    def to_html(text):
        html = _escape_html(text)
        html = _render_code_blocks(html)
        html = _render_inline_code(html)
        html = _render_headers(html)
        html = _render_bold(html)
        html = _render_italic(html)
        html = _render_lists(html)
        html = _render_links(html)
        html = _render_paragraphs(html)
        return f"<div style='line-height: 1.6;'>{html}</div>"


def _escape_html(text):
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;"))


def _render_code_blocks(text):
    def replace_block(m):
        code = m.group(1)
        lang = m.group(2) or ""
        return (
            f"<pre style='background: #1B1613; color: #F7F3EF; "
            f"padding: 14px; border-radius: 10px; font-size: 12px; "
            f"overflow-x: auto; white-space: pre-wrap; "
            f"font-family: \"JetBrains Mono\", Consolas, monospace; "
            f"margin: 8px 0;'><code>{_escape_html(code)}</code></pre>"
        )
    return re.sub(
        r"```(\w*)\n(.*?)```",
        replace_block,
        text,
        flags=re.DOTALL
    )


def _render_inline_code(text):
    return re.sub(
        r"`([^`]+)`",
        r"<code style='background: rgba(47,39,35,0.8); color: #E8A5B5; "
        r"padding: 2px 6px; border-radius: 4px; font-size: 12px; "
        r"font-family: \"JetBrains Mono\", Consolas, monospace;'>\1</code>",
        text
    )


def _render_headers(text):
    text = re.sub(r"^### (.+)$", r"<h3 style='margin: 12px 0 6px 0; font-size: 15px;'>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r"<h2 style='margin: 14px 0 8px 0; font-size: 17px;'>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$", r"<h1 style='margin: 16px 0 10px 0; font-size: 20px;'>\1</h1>", text, flags=re.MULTILINE)
    return text


def _render_bold(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _render_italic(text):
    return re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)


def _render_lists(text):
    def replace_ul(m):
        items = re.findall(r"^- (.+)", m.group(0), re.MULTILINE)
        lis = "".join(f"<li style='margin: 2px 0;'>{i}</li>" for i in items)
        return f"<ul style='margin: 6px 0; padding-left: 20px;'>{lis}</ul>"
    text = re.sub(r"(?:^- .+(?:\n|$))+", replace_ul, text, flags=re.MULTILINE)

    def replace_ol(m):
        items = re.findall(r"^\d+\. (.+)", m.group(0), re.MULTILINE)
        lis = "".join(f"<li style='margin: 2px 0;'>{i}</li>" for i in items)
        return f"<ol style='margin: 6px 0; padding-left: 20px;'>{lis}</ol>"
    text = re.sub(r"(?:^\d+\. .+(?:\n|$))+", replace_ol, text, flags=re.MULTILINE)
    return text


def _render_links(text):
    return re.sub(r"\[(.+?)\]\((.+?)\)", r"<a href='\2' style='color: #E8A5B5;'>\1</a>", text)


def _render_paragraphs(text):
    blocks = re.split(r"\n\n+", text)
    out = []
    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith("<h") or stripped.startswith("<pre") or stripped.startswith("<ul") or stripped.startswith("<ol"):
            out.append(stripped)
        else:
            out.append(f"<p style='margin: 6px 0;'>{stripped}</p>")
    return "\n".join(out)
