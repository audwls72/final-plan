#!/usr/bin/env python3
"""MD 정리 노트 -> 정리 PDF (A4, 표지 + 자동 쪽번호 목차 + 본문).
usage: python3 mkpdf.py note.md out.pdf --subject 미적분학2 --code MAS102 --prof 이기선 --abbr 미2 \
         --color '#1e3a8a' --exam '기말 12/15(화) 19:00' --label 'Lecture 13'
"""
import argparse, html, os, re, subprocess, sys, tempfile

ap = argparse.ArgumentParser()
for a in ["md", "out"]: ap.add_argument(a)
for a in ["subject", "code", "prof", "abbr", "color", "exam", "label"]: ap.add_argument("--" + a, required=True)
A = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.dirname(HERE))
from mdfix import fix as mdfix
src = mdfix(open(A.md, encoding="utf-8").read())
title_line = re.search(r"^# (.+)$", src, re.M)
title = title_line.group(1) if title_line else os.path.basename(A.md)
src = src.replace(title_line.group(0), "", 1) if title_line else src
# strip "과목 L13 — " prefix for the big cover title
short = re.sub(r"^.*?—\s*", "", title)
short = re.sub(r"^\[[^\]]+\]\s*\d+\.?\s*", "", short)

def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"&lt;(/?)strong&gt;", r"<\1b>", t)
    return t

# display-formula lines: a paragraph made only of lines indented by exactly 2 spaces
out, lines = [], src.split("\n")
i = 0
while i < len(lines):
    ln = lines[i]
    prev_blank = (i == 0) or lines[i - 1].strip() == ""
    if prev_blank and re.match(r"^  \S", ln) and not re.match(r"^  (([-*+]|\d+\.)\s|\|)", ln):
        block = []
        while i < len(lines) and re.match(r"^  \S", lines[i]):
            block.append(lines[i].strip()); i += 1
        out.append('<div class="eq">' + "<br>".join(inline(b) for b in block) + "</div>")
        continue
    out.append(ln); i += 1
md = "\n".join(out)
# fenced div titles -> first paragraph span (so math/markdown in titles renders)
def divopen(m):
    cls, title = m.group(1), m.group(2).replace("\\\\", "\\")
    return f"::: {{.box .{cls}}}\n\n[{title}]{{.bt}}\n"
md = re.sub(r'^::: *\{\.(\w+) title="(.*)"\} *$', divopen, md, flags=re.M)

body = subprocess.run(["pandoc", "-f", "commonmark_x-fancy_lists", "-t", "html5", "--mathml", "--wrap=none"], input=md, capture_output=True, text=True, check=True).stdout

# figure placeholders
body = re.sub(r"<p>\[그림:\s*(.+?)\]</p>", r'<div class="fig"><span>🖼 그림</span>\1</div>', body, flags=re.S)
body = re.sub(r"\[그림:\s*(.+?)\]", r'<span class="figi">🖼 \1</span>', body)
# box types for blockquotes
def bq(m):
    inner = m.group(1); txt = re.sub("<[^>]+>", "", inner)
    if re.match(r"\s*(자료|출처|관련 복습)", txt): cls = "note"
    elif re.search(r"Theorem|정리 \d|Key point|KEY", txt): cls = "thm"
    elif re.search(r"Definition|정의", txt): cls = "def"
    elif "⚠️" in txt or "함정" in txt: cls = "warn"
    else: cls = "quote"
    return f'<div class="box {cls}"><p><span class="bt"></span></p>{inner}</div>'
body = re.sub(r"<blockquote>(.*?)</blockquote>", bq, body, flags=re.S)
# paragraphs / list items starting with ⚠️ -> trap highlight
body = re.sub(r"<p>⚠️", '<p class="warn">⚠️', body)
body = re.sub(r"<li>⚠️", '<li class="warn">⚠️', body)
# headings: ids + markers for page lookup
heads = []
def hd(m):
    lvl, inner = m.group(1), m.group(3)
    n = len(heads)
    toc = re.sub(r"<annotation.*?</annotation>", "", inner, flags=re.S)
    toc = re.sub(r"<(?!/?(math|mrow|mi|mo|mn|msub|msup|msubsup|mfrac|msqrt|mtext|mover|munder|semantics|mspace)\b)[^>]+>", "", toc)
    heads.append((lvl, toc))
    return f'<h{lvl} id="h{n}">{inner}<span class="mk">QQH{n}QQ</span></h{lvl}>'
body = re.sub(r"<h([23])(?: [^>]*)?()>(.*?)</h\1>", hd, body, flags=re.S)
# section bands for h2: checklist / glossary special classes
# math sub/superscripts in text nodes (not inside code/pre)
def mathfmt(seg):
    for _ in range(2):
        seg = re.sub(r"_\{([^{}<>]+)\}", r"<sub>\1</sub>", seg)
        seg = re.sub(r"\^\{([^{}<>]+)\}", r"<sup>\1</sup>", seg)
    seg = re.sub(r"(?<=[A-Za-zΔπσρθφ∫∬∭∮Σ\)\]])_([A-Za-z0-9αβγθφρ]{1,3})(?![A-Za-z0-9_])", r"<sub>\1</sub>", seg)
    seg = re.sub(r"(?<=[A-Za-z0-9\)\]|])\^([A-Za-z0-9αβγθφρ−\-]{1,3})(?![A-Za-z0-9])", r"<sup>\1</sup>", seg)
    return seg
parts = re.split(r"(<math.*?</math>|<pre.*?</pre>|<code.*?</code>|<[^>]+>)", body, flags=re.S)
body = "".join(x if (x.startswith("<")) else mathfmt(x) for x in parts)
body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
body = re.sub(r'<input type="checkbox" disabled="" />', '<span class="cb"></span>', body)

def build(pages):
    toc = "".join(
        f'<div class="t{l}"><a href="#h{k}">{t}</a><span class="dots"></span><span class="pg">{pages.get(k, "")}</span></div>'
        for k, (l, t) in enumerate(heads))
    return open(os.path.join(HERE, "template.html"), encoding="utf-8").read().format(
        color=A.color, subject=html.escape(A.subject), code=A.code, prof=html.escape(A.prof), abbr=html.escape(A.abbr),
        exam=html.escape(A.exam), label=html.escape(A.label), title=html.escape(short), fulltitle=html.escape(title),
        toc=toc, body=body)

def render(htm, pdf):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(htm); hp = f.name
    subprocess.run(["node", os.path.join(HERE, "print.mjs"), hp, pdf, A.abbr + " · " + A.label], check=True)
    os.unlink(hp)

tmp = A.out + ".pass1.pdf"
render(build({k: "00" for k in range(len(heads))}), tmp)
pages = {}
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", tmp], capture_output=True, text=True).stdout or "Pages: 0").group(1) or 0) if os.path.exists("/usr/bin/pdfinfo") else 0
txt = subprocess.run(["pdftotext", "-layout", tmp, "-"], capture_output=True, text=True).stdout.split("\f")
for p, t in enumerate(txt, 1):
    for m in re.finditer(r"QQH(\d+)QQ", t):
        pages.setdefault(int(m.group(1)), p)
render(build(pages), A.out)
os.unlink(tmp)
print(A.out, len(txt) - 1, "pages")
